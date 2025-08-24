"""
LangChain-based document processing service.
Replaces the complex custom chunking and embedding logic with battle-tested LangChain components.
"""

import logging
from typing import Any, Dict, List, Optional

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PDFPlumberLoader
from langchain_community.vectorstores import SupabaseVectorStore
from langchain_openai import OpenAIEmbeddings

from app.core.config import settings
from app.core.database import db
from app.core.logging_utils import processing_logger
from app.models.enums import FileStatus

logger = logging.getLogger(__name__)


class LangChainDocumentProcessor:
    """Simplified document processor using LangChain components."""

    def __init__(self):
        self.embeddings = None
        try:
            if settings.openai_api_key and settings.openai_api_key.strip():
                try:
                    self.embeddings = OpenAIEmbeddings(
                        openai_api_key=settings.openai_api_key, model=settings.embedding_model
                    )
                    logger.info("LangChain OpenAI embeddings initialized successfully")
                except Exception as e:
                    logger.error(f"Failed to initialize OpenAI embeddings: {e}")
                    self.embeddings = None
            else:
                logger.warning("OpenAI API key not configured - embedding generation disabled")
        except Exception as e:
            logger.error(f"Critical error initializing LangChain processor: {e}")
            self.embeddings = None

        # Initialize text splitter with safe, proven settings
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""],  # Standard separators
        )

        logger.info(
            f"LangChain processor initialized with chunk_size={settings.chunk_size}, chunk_overlap={settings.chunk_overlap}"
        )

    async def process_pdf_file(self, file_id: str, file_path: str) -> Dict[str, Any]:
        """
        Process a PDF file using LangChain components.

        Args:
            file_id: Processing file ID
            file_path: Path to the uploaded PDF file

        Returns:
            Dict with processing results
        """
        processing_logger.log_step(
            "langchain_processing_start", file_id=file_id, file_path=file_path
        )

        try:
            # Step 1: Download file from Supabase storage if needed
            import os
            import tempfile

            from app.core.database import db

            local_file_path = file_path
            temp_file = None

            # If file_path looks like a Supabase storage path, download it locally
            if file_path.startswith("uploads/") and not os.path.exists(file_path):
                processing_logger.log_step(
                    "downloading_from_storage", file_id=file_id, storage_path=file_path
                )

                try:
                    # Get file content from Supabase storage
                    client = await db.get_supabase_client()
                    response = client.storage.from_("documents").download(file_path)

                    # Handle the response based on its type
                    file_content = None
                    if hasattr(response, "data") and response.data:
                        file_content = response.data
                    elif isinstance(response, bytes):
                        file_content = response
                    else:
                        # Try to get content as bytes
                        file_content = bytes(response)

                    if file_content:
                        # Create temporary file
                        temp_file = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
                        temp_file.write(file_content)
                        temp_file.close()
                        local_file_path = temp_file.name
                        processing_logger.log_step(
                            "file_downloaded",
                            file_id=file_id,
                            temp_path=local_file_path,
                            size=len(file_content),
                        )
                    else:
                        raise ValueError(
                            f"Failed to download file from storage: {file_path} - No content received"
                        )

                except Exception as e:
                    processing_logger.log_error("storage_download_failed", e, file_id=file_id)
                    raise ValueError(f"Could not access file {file_path}: {str(e)}")

            # Step 2: Load PDF using LangChain's PDFPlumberLoader
            processing_logger.log_step("pdf_loading_start", file_id=file_id)
            loader = PDFPlumberLoader(local_file_path)
            documents = loader.load()

            # Clean up temporary file if created
            if temp_file and os.path.exists(local_file_path) and local_file_path != file_path:
                try:
                    os.unlink(local_file_path)
                    processing_logger.log_step("temp_file_cleanup", file_id=file_id)
                except Exception:
                    pass  # Don't fail processing if cleanup fails

            # Extract text from all pages
            full_text = "\n".join([doc.page_content for doc in documents])
            text_length = len(full_text)

            processing_logger.log_step(
                "pdf_loading_complete",
                file_id=file_id,
                pages_loaded=len(documents),
                text_length=text_length,
            )

            # Step 2: Update processing file with extracted text
            await self._update_file_status(
                file_id, FileStatus.ANALYZING_METADATA, extracted_text=full_text
            )

            # Step 3: Split documents using RecursiveCharacterTextSplitter
            processing_logger.log_step("text_splitting_start", file_id=file_id)
            chunks = self.text_splitter.split_documents(documents)

            processing_logger.log_step(
                "text_splitting_complete",
                file_id=file_id,
                total_chunks=len(chunks),
                avg_chunk_size=sum(len(chunk.page_content) for chunk in chunks) / len(chunks)
                if chunks
                else 0,
            )

            # Step 4: Generate and store embeddings if OpenAI is available
            if self.embeddings and chunks:
                processing_logger.log_step(
                    "embedding_generation_start", file_id=file_id, chunk_count=len(chunks)
                )
                await self._update_file_status(file_id, FileStatus.GENERATING_EMBEDDINGS)

                # Create Supabase vector store and add documents
                client = await db.get_supabase_client()
                vector_store = SupabaseVectorStore.from_documents(
                    chunks,
                    self.embeddings,
                    client=client,
                    table_name="document_chunks",
                    query_name="match_documents",
                )

                # Update chunk count in processing file
                await client.table("processing_files").update({"chunk_count": len(chunks)}).eq(
                    "id", file_id
                ).execute()

                processing_logger.log_step(
                    "embedding_generation_complete",
                    file_id=file_id,
                    chunks_embedded=len(chunks),
                    embedding_dimension=1536,  # OpenAI default
                )
            else:
                processing_logger.log_step(
                    "embedding_generation_skipped",
                    file_id=file_id,
                    reason="No OpenAI API key" if not self.embeddings else "No chunks",
                )

            # Step 5: Mark as ready for review
            await self._update_file_status(file_id, FileStatus.REVIEW_PENDING)

            processing_logger.log_step(
                "langchain_processing_complete",
                file_id=file_id,
                text_length=text_length,
                chunk_count=len(chunks),
                success=True,
            )

            return {
                "success": True,
                "file_id": file_id,
                "text_length": text_length,
                "chunk_count": len(chunks),
                "embedding_dimension": 1536 if self.embeddings else 0,
            }

        except Exception as e:
            processing_logger.log_error("langchain_processing_failed", e, file_id=file_id)
            await self._update_file_status(file_id, FileStatus.EXTRACTION_FAILED, error=str(e))
            return {"success": False, "file_id": file_id, "error": str(e)}

    async def _update_file_status(
        self,
        file_id: str,
        status: FileStatus,
        extracted_text: Optional[str] = None,
        error: Optional[str] = None,
    ):
        """Update processing file status and optional fields."""
        client = await db.get_supabase_client()

        update_data = {"status": status.value}
        if extracted_text:
            update_data["extracted_text"] = extracted_text
        if error:
            update_data["error_message"] = error

        await client.table("processing_files").update(update_data).eq("id", file_id).execute()


# Global processor instance
langchain_processor = LangChainDocumentProcessor()
