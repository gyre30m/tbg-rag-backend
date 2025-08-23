"""
Embedding service for generating vector embeddings from document text.
"""

import asyncio
import logging
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
        self.openai_client = (
            openai.AsyncOpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None
        )
        self.embedding_model = "text-embedding-3-small"  # OpenAI's latest embedding model
        self.chunk_size = 1000  # Characters per chunk
        self.chunk_overlap = 200  # Overlap between chunks
        self.max_chunks_per_document = 500  # Reasonable limit

        if not self.openai_client:
            logger.warning("OpenAI API key not configured - embedding generation disabled")

    async def generate_embeddings(self, file_id: str) -> Dict[str, Any]:
        """
        Generate vector embeddings for a processing file.

        Args:
            file_id: Processing file ID

        Returns:
            Dict with generation results
        """
        logger.info(f"Starting embedding generation for file {file_id}")

        if not self.openai_client:
            return {"success": False, "file_id": file_id, "error": "OpenAI API key not configured"}

        try:
            # Get file record with extracted text
            file_result = (
                db.supabase.table("processing_files").select("*").eq("id", file_id).execute()
            )
            if not file_result.data:
                raise ValueError(f"File {file_id} not found")

            file_record = file_result.data[0]

            if not file_record.get("extracted_text"):
                raise ValueError(f"No extracted text found for file {file_id}")

            # Update status to generating embeddings
            self._update_file_status(file_id, FileStatus.GENERATING_EMBEDDINGS)

            # Split text into chunks
            chunks = self._split_text_into_chunks(file_record["extracted_text"])

            if len(chunks) > self.max_chunks_per_document:
                logger.warning(
                    f"File {file_id} has {len(chunks)} chunks, truncating to {self.max_chunks_per_document}"
                )
                chunks = chunks[: self.max_chunks_per_document]

            # Generate embeddings for chunks
            embeddings_result = await self._generate_chunk_embeddings(chunks)

            if embeddings_result["success"]:
                # Save embeddings to database
                await self._save_embeddings(file_id, chunks, embeddings_result["embeddings"])
                self._update_file_status(file_id, FileStatus.PROCESSING_COMPLETE)

                logger.info(
                    f"Successfully generated embeddings for file {file_id} ({len(chunks)} chunks)"
                )
                return {
                    "success": True,
                    "file_id": file_id,
                    "chunk_count": len(chunks),
                    "embedding_dimension": (
                        len(embeddings_result["embeddings"][0])
                        if embeddings_result["embeddings"]
                        else 0
                    ),
                }
            else:
                self._update_file_status(
                    file_id, FileStatus.EMBEDDING_FAILED, error_message=embeddings_result["error"]
                )
                return {"success": False, "file_id": file_id, "error": embeddings_result["error"]}

        except Exception as e:
            logger.error(f"Embedding generation failed for file {file_id}: {e}")
            self._update_file_status(file_id, FileStatus.EMBEDDING_FAILED, error_message=str(e))
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
                    response = await self.openai_client.embeddings.create(
                        model=self.embedding_model, input=batch_chunks, encoding_format="float"
                    )

                    batch_embeddings = [data.embedding for data in response.data]
                    all_embeddings.extend(batch_embeddings)

                    # Rate limiting - be gentle with API
                    if i + batch_size < len(chunks):
                        await asyncio.sleep(0.1)

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
            # Prepare chunk data for batch insert
            chunk_data = []
            for i, (chunk_text, embedding) in enumerate(zip(chunks, embeddings)):
                chunk_data.append(
                    {
                        "processing_file_id": file_id,
                        "chunk_index": i,
                        "text_content": chunk_text,
                        "embedding": embedding,
                        "token_count": len(chunk_text.split()),  # Rough token estimate
                        "created_at": datetime.utcnow().isoformat(),
                    }
                )

            # Insert chunks in batches
            batch_size = 100
            for i in range(0, len(chunk_data), batch_size):
                batch = chunk_data[i : i + batch_size]
                db.supabase.table("document_chunks").insert(batch).execute()

            # Update processing file with chunk count
            db.supabase.table("processing_files").update({"chunk_count": len(chunks)}).eq(
                "id", file_id
            ).execute()

            logger.info(f"Saved {len(chunks)} chunks for file {file_id}")

        except Exception as e:
            logger.error(f"Failed to save embeddings for file {file_id}: {e}")
            raise

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
            result = db.supabase.rpc("sql_query", {"query": sql_query}).execute()

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

    def _update_file_status(self, file_id: str, status: FileStatus, **kwargs):
        """Update file processing status."""
        try:
            update_data = {
                "status": status.value,
                "updated_at": datetime.utcnow().isoformat(),
                **kwargs,
            }

            db.supabase.table("processing_files").update(update_data).eq("id", file_id).execute()

        except Exception as e:
            logger.error(f"Failed to update file {file_id} status: {e}")
            raise
