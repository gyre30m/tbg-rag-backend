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
from app.models.enums import FileStatus

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Handles vector embedding generation for document text."""

    def __init__(self):
        self.openai_client = None
        self.embedding_model = "text-embedding-3-small"  # OpenAI's latest embedding model
        self.chunk_size = 1000  # Characters per chunk
        self.chunk_overlap = 200  # Overlap between chunks
        self.max_chunks_per_document = 500  # Reasonable limit

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
        logger.info(f"🔗 EMBEDDING START: File {file_id}")

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
            logger.info(f"📄 CHUNKING: File {file_id} has {text_length} characters")
            chunks = self._split_text_into_chunks(file_record["extracted_text"])
            logger.info(f"✂️ CHUNKS: File {file_id} split into {len(chunks)} chunks")

            if len(chunks) > self.max_chunks_per_document:
                logger.warning(
                    f"⚠️ TRUNCATING: File {file_id} has {len(chunks)} chunks, truncating to {self.max_chunks_per_document}"
                )
                chunks = chunks[: self.max_chunks_per_document]

            # Generate and save embeddings in streaming fashion to avoid memory buildup
            embed_start = time.time()
            logger.info(
                f"🧠 OPENAI: Processing {len(chunks)} chunks from file {file_id} in memory-efficient batches"
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
        if len(text) <= self.chunk_size:
            return [text]

        chunks = []
        start = 0

        while start < len(text):
            end = start + self.chunk_size

            # If this isn't the last chunk, try to break at a sentence or paragraph
            if end < len(text):
                # Look for paragraph break first
                paragraph_break = text.rfind("\n\n", start, end)
                if paragraph_break > start:
                    end = paragraph_break
                else:
                    # Look for sentence break
                    sentence_break = text.rfind(". ", start, end)
                    if sentence_break > start:
                        end = sentence_break + 1

            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            # Move start position with overlap
            if end >= len(text):
                break
            start = end - self.chunk_overlap

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
                            "text_content": chunks[i],
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

            for stream_start in range(0, total_chunks, stream_batch_size):
                stream_end = min(stream_start + stream_batch_size, total_chunks)
                stream_chunks = chunks[stream_start:stream_end]

                logger.debug(
                    f"Processing chunk batch {stream_start + 1}-{stream_end} of {total_chunks}"
                )

                # Generate embeddings for this stream batch
                stream_embeddings = []
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

                        # Rate limiting
                        await asyncio.sleep(0.1)

                    except asyncio.TimeoutError:
                        logger.error("Embedding batch timed out")
                        return {"success": False, "error": "OpenAI embedding API timed out"}
                    except Exception as e:
                        logger.error(f"Embedding batch failed: {e}")
                        return {"success": False, "error": f"OpenAI embedding API failed: {str(e)}"}

                # Save this stream batch immediately
                chunk_batch = []
                for i, (chunk_text, embedding) in enumerate(zip(stream_chunks, stream_embeddings)):
                    chunk_batch.append(
                        {
                            "processing_file_id": file_id,
                            "chunk_index": stream_start + i,
                            "text_content": chunk_text,
                            "embedding": embedding,
                            "token_count": len(chunk_text.split()),
                            "created_at": datetime.utcnow().isoformat(),
                        }
                    )

                # Insert to database
                await client.table("document_chunks").insert(chunk_batch).execute()
                total_saved += len(chunk_batch)

                # Clear memory immediately
                del stream_embeddings
                del chunk_batch

                logger.debug(f"Saved {len(stream_chunks)} chunks to database")

            # Update processing file with final chunk count
            await client.table("processing_files").update({"chunk_count": total_saved}).eq(
                "id", file_id
            ).execute()

            logger.info(f"Streamed and saved {total_saved} chunks for file {file_id}")
            return {"success": True, "chunk_count": total_saved, "embedding_dimension": 1536}

        except Exception as e:
            logger.error(f"Streaming embedding generation error: {e}")
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
                dc.text_content,
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
                            "text_content": row["text_content"],
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
