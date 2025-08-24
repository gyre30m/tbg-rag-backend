"""
Embedding service for generating vector embeddings from document text.
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import numpy as np
import openai

from app.core.config import settings
from app.core.database import db
from app.core.logging_utils import processing_logger
from app.models.enums import FileStatus

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Handles vector embedding generation for document text."""

    def __init__(self):
        self.openai_client = None
        self.embedding_model = settings.embedding_model
        self.chunk_size = settings.chunk_size  # Use config value
        self.chunk_overlap = min(
            settings.chunk_overlap, settings.chunk_size // 4
        )  # Ensure overlap is max 25% of chunk size
        self.max_chunks_per_document = 500  # Reasonable limit
        logger.info(
            f"Embedding service initialized with chunk_size={self.chunk_size}, chunk_overlap={self.chunk_overlap}"
        )

        # Initialize OpenAI client if API key is available
        if settings.openai_api_key and settings.openai_api_key.strip():
            try:
                self.openai_client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
                logger.info("OpenAI embedding service initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")
                self.openai_client = None
        else:
            logger.warning("OpenAI API key not configured - embedding generation disabled")

    async def generate_embeddings(self, file_id: str) -> Dict[str, Any]:
        """
        Generate vector embeddings for a processing file.

        Args:
            file_id: Processing file ID

        Returns:
            Dict with generation results
        """
        start_time = time.time()
        processing_logger.log_step("embedding_service_start", file_id=file_id)

        if not self.openai_client:
            logger.warning(
                f"Skipping embeddings for file {file_id} - OpenAI API key not configured"
            )
            # Update file status to move forward in pipeline without embeddings
            await self._update_file_status(file_id, FileStatus.REVIEW_PENDING)
            return {
                "success": True,
                "file_id": file_id,
                "chunk_count": 0,
                "embedding_dimension": 0,
                "message": "Embeddings skipped - no OpenAI API key",
            }

        try:
            # Get file record with extracted text
            client = await db.get_supabase_client()
            file_result = await (
                client.table("processing_files").select("*").eq("id", file_id).execute()
            )
            if not file_result.data:
                raise ValueError(f"File {file_id} not found")

            file_record = file_result.data[0]

            if not file_record.get("extracted_text"):
                raise ValueError(f"No extracted text found for file {file_id}")

            # Update status to generating embeddings
            await self._update_file_status(file_id, FileStatus.GENERATING_EMBEDDINGS)

            # Split text into chunks
            text_length = len(file_record["extracted_text"])
            processing_logger.log_step(
                "text_chunking_start", file_id=file_id, text_length=text_length
            )
            chunks = self._split_text_into_chunks(file_record["extracted_text"])
            processing_logger.log_step(
                "text_chunking_complete",
                file_id=file_id,
                chunk_count=len(chunks),
                text_length=text_length,
            )
            processing_logger.log_memory_warning(
                "post_chunking", threshold_mb=200, file_id=file_id, chunk_count=len(chunks)
            )

            if len(chunks) > self.max_chunks_per_document:
                processing_logger.log_step(
                    "chunk_truncation",
                    file_id=file_id,
                    original_chunks=len(chunks),
                    truncated_to=self.max_chunks_per_document,
                )
                chunks = chunks[: self.max_chunks_per_document]

            # Generate and save embeddings in streaming fashion to avoid memory buildup
            embed_start = time.time()
            processing_logger.log_step(
                "embedding_generation_batch_start",
                file_id=file_id,
                total_chunks=len(chunks),
                max_chunks_per_doc=self.max_chunks_per_document,
            )
            processing_logger.log_memory_warning(
                "pre_embedding_batches", threshold_mb=200, file_id=file_id
            )

            # Process embeddings in smaller batches and save immediately
            embeddings_result = await self._generate_and_save_embeddings_streaming(file_id, chunks)
            embed_duration = time.time() - embed_start

            if embeddings_result["success"]:
                logger.info(f"✅ STREAMING: Processed file {file_id} in {embed_duration:.2f}s")

                await self._update_file_status(file_id, FileStatus.REVIEW_PENDING)

                total_duration = time.time() - start_time
                logger.info(
                    f"🎯 EMBEDDING COMPLETE: File {file_id} ({len(chunks)} chunks) in {total_duration:.2f}s"
                )
                return {
                    "success": True,
                    "file_id": file_id,
                    "chunk_count": embeddings_result.get("chunk_count", 0),
                    "embedding_dimension": embeddings_result.get("embedding_dimension", 0),
                }
            else:
                await self._update_file_status(
                    file_id, FileStatus.EMBEDDING_FAILED, error_message=embeddings_result["error"]
                )
                return {"success": False, "file_id": file_id, "error": embeddings_result["error"]}

        except Exception as e:
            logger.error(f"Embedding generation failed for file {file_id}: {e}")
            await self._update_file_status(
                file_id, FileStatus.EMBEDDING_FAILED, error_message=str(e)
            )
            return {"success": False, "file_id": file_id, "error": str(e)}

    def _split_text_into_chunks(self, text: str) -> List[str]:
        """Split text into overlapping chunks for embedding."""
        processing_logger.log_step(
            "chunk_splitting_start",
            text_length=len(text),
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
        )

        if len(text) <= self.chunk_size:
            processing_logger.log_step(
                "chunk_splitting_single_chunk", text_length=len(text), chunk_size=self.chunk_size
            )
            return [text]

        chunks: List[str] = []
        start = 0
        iteration_count = 0  # Safety counter to detect infinite loops

        while start < len(text):
            iteration_count += 1

            # Safety check to prevent infinite loops
            if iteration_count > 10000:  # Reasonable maximum for any document
                processing_logger.log_error(
                    "chunk_splitting_infinite_loop_detected",
                    Exception("Chunking exceeded 10,000 iterations - possible infinite loop"),
                    text_length=len(text),
                    chunk_size=self.chunk_size,
                    chunk_overlap=self.chunk_overlap,
                    current_start=start,
                    chunks_created=len(chunks),
                )
                break

            end = start + self.chunk_size

            # If this isn't the last chunk, try to break at a sentence or paragraph
            # But ensure we don't make chunks too small (min 50% of chunk_size)
            min_chunk_end = start + (self.chunk_size // 2)

            if end < len(text) and end > min_chunk_end:
                # Look for paragraph break first (only in second half of chunk)
                paragraph_break = text.rfind("\n\n", min_chunk_end, end)
                if paragraph_break > start:
                    end = paragraph_break
                else:
                    # Look for sentence break (only in second half of chunk)
                    sentence_break = text.rfind(". ", min_chunk_end, end)
                    if sentence_break > start:
                        end = sentence_break + 1

            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

                # Log progress every 1000 chunks to detect runaway chunking
                if len(chunks) % 1000 == 0:
                    processing_logger.log_step(
                        "chunk_splitting_progress",
                        chunks_created=len(chunks),
                        iteration_count=iteration_count,
                        current_position=start,
                        text_length=len(text),
                        progress_percent=round((start / len(text)) * 100, 2),
                    )
                    processing_logger.log_memory_warning(
                        "chunking_memory_check", threshold_mb=1000, chunks_in_memory=len(chunks)
                    )

            # Move start position with overlap
            if end >= len(text):
                break

            # Calculate next start position, ensuring forward progress
            # The next chunk should start at (end - overlap), but never go backwards
            next_start = end - self.chunk_overlap

            # Critical fix: Ensure we always move forward by at least 50 characters
            # This prevents infinite loops when sentence breaks create small chunks
            min_forward_progress = max(
                50, self.chunk_size // 20
            )  # At least 5% of chunk size or 50 chars
            if next_start <= start:
                next_start = start + min_forward_progress

            start = next_start

        processing_logger.log_step(
            "chunk_splitting_complete",
            total_chunks=len(chunks),
            iteration_count=iteration_count,
            text_length=len(text),
        )

        return chunks

    async def _generate_chunk_embeddings(self, chunks: List[str]) -> Dict[str, Any]:
        """Generate embeddings for text chunks using OpenAI API."""
        try:
            # Process chunks in batches to avoid rate limits
            batch_size = 100  # OpenAI allows up to 2048 inputs per request
            all_embeddings = []

            for i in range(0, len(chunks), batch_size):
                batch_chunks = chunks[i : i + batch_size]

                try:
                    # Add timeout to prevent hanging
                    response = await asyncio.wait_for(
                        self.openai_client.embeddings.create(
                            model=self.embedding_model, input=batch_chunks, encoding_format="float"
                        ),
                        timeout=60.0,  # 60 second timeout per batch
                    )

                    batch_embeddings = [data.embedding for data in response.data]
                    all_embeddings.extend(batch_embeddings)

                    # Rate limiting - be gentle with API
                    if i + batch_size < len(chunks):
                        await asyncio.sleep(0.1)

                except asyncio.TimeoutError:
                    logger.error(
                        f"Embedding batch {i // batch_size + 1} timed out after 60 seconds"
                    )
                    return {"success": False, "error": "OpenAI embedding API timed out"}
                except Exception as e:
                    logger.error(f"Embedding batch {i // batch_size + 1} failed: {e}")
                    return {"success": False, "error": f"OpenAI embedding API failed: {str(e)}"}

            if len(all_embeddings) != len(chunks):
                raise ValueError(
                    f"Embedding count mismatch: {len(all_embeddings)} != {len(chunks)}"
                )

            return {"success": True, "embeddings": all_embeddings}

        except Exception as e:
            logger.error(f"Embedding generation error: {e}")
            return {"success": False, "error": f"Embedding generation failed: {str(e)}"}

    async def _save_embeddings(
        self, file_id: str, chunks: List[str], embeddings: List[List[float]]
    ):
        """Save text chunks and their embeddings to the database."""
        try:
            client = await db.get_supabase_client()

            # Process and save chunks in smaller batches to avoid memory buildup
            batch_size = 50  # Smaller batches to reduce memory usage
            total_chunks = len(chunks)

            for batch_start in range(0, total_chunks, batch_size):
                batch_end = min(batch_start + batch_size, total_chunks)

                # Create batch data on-demand (not all at once)
                chunk_batch = []
                for i in range(batch_start, batch_end):
                    chunk_batch.append(
                        {
                            "processing_file_id": file_id,
                            "chunk_index": i,
                            "content": chunks[i],
                            "embedding": embeddings[i],
                            "token_count": len(chunks[i].split()),
                            "created_at": datetime.utcnow().isoformat(),
                        }
                    )

                # Insert this batch
                await client.table("document_chunks").insert(chunk_batch).execute()

                # Clear batch from memory immediately
                del chunk_batch

                logger.debug(f"Saved chunk batch {batch_start + 1}-{batch_end} of {total_chunks}")

            # Update processing file with chunk count
            await client.table("processing_files").update({"chunk_count": len(chunks)}).eq(
                "id", file_id
            ).execute()

            logger.info(
                f"Saved {len(chunks)} chunks for file {file_id} in memory-efficient batches"
            )

        except Exception as e:
            logger.error(f"Failed to save embeddings for file {file_id}: {e}")
            raise

    async def _generate_and_save_embeddings_streaming(
        self, file_id: str, chunks: List[str]
    ) -> Dict[str, Any]:
        """Generate embeddings and save in streaming fashion to avoid memory buildup."""
        try:
            client = await db.get_supabase_client()
            total_chunks = len(chunks)
            stream_batch_size = 50  # Process this many chunks at a time
            openai_batch_size = 20  # OpenAI API batch size (smaller to reduce memory)
            total_saved = 0

            processing_logger.log_step(
                "streaming_embeddings_start",
                file_id=file_id,
                total_chunks=total_chunks,
                stream_batch_size=stream_batch_size,
                openai_batch_size=openai_batch_size,
            )

            for stream_start in range(0, total_chunks, stream_batch_size):
                stream_end = min(stream_start + stream_batch_size, total_chunks)
                stream_chunks = chunks[stream_start:stream_end]

                processing_logger.log_step(
                    "stream_batch_start",
                    file_id=file_id,
                    batch_start=stream_start + 1,
                    batch_end=stream_end,
                    batch_size=len(stream_chunks),
                    total_chunks=total_chunks,
                )
                processing_logger.log_memory_warning(
                    "stream_batch_memory_check",
                    threshold_mb=500,
                    file_id=file_id,
                    batch_number=stream_start // stream_batch_size + 1,
                )

                # Generate embeddings for this stream batch
                stream_embeddings = []
                processing_logger.log_step(
                    "openai_embedding_batches_start",
                    file_id=file_id,
                    stream_chunks_count=len(stream_chunks),
                )
                for i in range(0, len(stream_chunks), openai_batch_size):
                    openai_batch = stream_chunks[i : i + openai_batch_size]

                    try:
                        response = await asyncio.wait_for(
                            self.openai_client.embeddings.create(
                                model=self.embedding_model,
                                input=openai_batch,
                                encoding_format="float",
                            ),
                            timeout=60.0,
                        )

                        batch_embeddings = [data.embedding for data in response.data]
                        stream_embeddings.extend(batch_embeddings)

                        processing_logger.log_step(
                            "openai_batch_complete",
                            file_id=file_id,
                            batch_size=len(openai_batch),
                            embeddings_received=len(batch_embeddings),
                            total_embeddings_so_far=len(stream_embeddings),
                        )
                        processing_logger.log_memory_warning(
                            "post_openai_batch", threshold_mb=300, file_id=file_id
                        )

                        # Rate limiting
                        await asyncio.sleep(0.1)

                    except asyncio.TimeoutError:
                        logger.error("Embedding batch timed out")
                        return {"success": False, "error": "OpenAI embedding API timed out"}
                    except Exception as e:
                        logger.error(f"Embedding batch failed: {e}")
                        return {"success": False, "error": f"OpenAI embedding API failed: {str(e)}"}

                # Save this stream batch immediately
                processing_logger.log_step(
                    "database_save_start",
                    file_id=file_id,
                    chunks_to_save=len(stream_chunks),
                    embeddings_to_save=len(stream_embeddings),
                )
                processing_logger.log_memory_warning(
                    "pre_database_save", threshold_mb=500, file_id=file_id
                )

                chunk_batch = []
                for i, (chunk_text, embedding) in enumerate(zip(stream_chunks, stream_embeddings)):
                    chunk_batch.append(
                        {
                            "processing_file_id": file_id,
                            "chunk_index": stream_start + i,
                            "content": chunk_text,
                            "embedding": embedding,
                            "token_count": len(chunk_text.split()),
                            "created_at": datetime.utcnow().isoformat(),
                        }
                    )

                # Insert to database
                processing_logger.log_step(
                    "database_insert_start", file_id=file_id, chunk_batch_size=len(chunk_batch)
                )
                await client.table("document_chunks").insert(chunk_batch).execute()
                total_saved += len(chunk_batch)

                processing_logger.log_step(
                    "database_insert_complete",
                    file_id=file_id,
                    chunks_saved=len(chunk_batch),
                    total_saved=total_saved,
                )

                # Clear memory immediately
                processing_logger.log_step(
                    "memory_cleanup_start",
                    file_id=file_id,
                    objects_to_delete=["stream_embeddings", "chunk_batch"],
                )
                del stream_embeddings
                del chunk_batch

                processing_logger.log_step(
                    "stream_batch_complete",
                    file_id=file_id,
                    chunks_processed=len(stream_chunks),
                    total_saved=total_saved,
                )
                processing_logger.log_memory_warning(
                    "post_cleanup", threshold_mb=200, file_id=file_id
                )

            # Update processing file with final chunk count
            processing_logger.log_step(
                "update_final_chunk_count", file_id=file_id, total_chunks_saved=total_saved
            )
            await client.table("processing_files").update({"chunk_count": total_saved}).eq(
                "id", file_id
            ).execute()

            processing_logger.log_step(
                "streaming_embeddings_complete",
                file_id=file_id,
                total_chunks_saved=total_saved,
                embedding_dimension=1536,
            )
            return {"success": True, "chunk_count": total_saved, "embedding_dimension": 1536}

        except Exception as e:
            processing_logger.log_error(
                "streaming_embeddings_failed",
                e,
                file_id=file_id,
                total_chunks=total_chunks if "total_chunks" in locals() else "unknown",
            )
            return {"success": False, "error": f"Streaming embedding generation failed: {str(e)}"}

    async def search_similar_chunks(
        self,
        query_text: str,
        limit: int = 10,
        similarity_threshold: float = 0.7,
        doc_categories: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for similar document chunks using vector similarity.

        Args:
            query_text: Text to search for
            limit: Maximum number of results
            similarity_threshold: Minimum similarity score (0-1)
            doc_categories: Optional list of document categories to filter by

        Returns:
            List of similar chunks with metadata
        """
        if not self.openai_client:
            logger.warning("Cannot perform similarity search - OpenAI API key not configured")
            return []

        try:
            # Generate embedding for query
            response = await self.openai_client.embeddings.create(
                model=self.embedding_model, input=[query_text], encoding_format="float"
            )

            query_embedding = response.data[0].embedding

            # Build the SQL query for similarity search
            # Note: This uses pgvector's cosine similarity operator (<->)
            sql_query = f"""
            SELECT
                dc.content,
                dc.chunk_index,
                pf.original_filename,
                pf.ai_title,
                pf.ai_doc_type,
                pf.ai_doc_category,
                (1 - (dc.embedding <-> '[{','.join(map(str, query_embedding))}]'::vector)) as similarity_score
            FROM document_chunks dc
            JOIN processing_files pf ON dc.processing_file_id = pf.id
            WHERE pf.status = 'processing_complete'
            """

            # Add category filter if specified
            if doc_categories:
                category_list = "', '".join(doc_categories)
                sql_query += f" AND pf.ai_doc_category IN ('{category_list}')"

            sql_query += f"""
            ORDER BY dc.embedding <-> '[{','.join(map(str, query_embedding))}]'::vector
            LIMIT {limit}
            """

            # Execute similarity search
            client = await db.get_supabase_client()
            result = await client.rpc("sql_query", {"query": sql_query}).execute()

            # Filter by similarity threshold
            similar_chunks = []
            for row in result.data:
                if row.get("similarity_score", 0) >= similarity_threshold:
                    similar_chunks.append(
                        {
                            "content": row["content"],
                            "chunk_index": row["chunk_index"],
                            "filename": row["original_filename"],
                            "title": row["ai_title"],
                            "doc_type": row["ai_doc_type"],
                            "doc_category": row["ai_doc_category"],
                            "similarity_score": row["similarity_score"],
                        }
                    )

            return similar_chunks

        except Exception as e:
            logger.error(f"Similarity search failed: {e}")
            return []

    async def _update_file_status(self, file_id: str, status: FileStatus, **kwargs):
        """Update file processing status."""
        try:
            update_data = {
                "status": status.value,
                "updated_at": datetime.utcnow().isoformat(),
                **kwargs,
            }

            client = await db.get_supabase_client()
            await client.table("processing_files").update(update_data).eq("id", file_id).execute()

        except Exception as e:
            logger.error(f"Failed to update file {file_id} status: {e}")
            raise
