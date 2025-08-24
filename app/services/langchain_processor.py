"""
LangChain-based document processing service.
Replaces the complex custom chunking and embedding logic with battle-tested LangChain components.
"""

import logging
from typing import Any, Dict, List, Optional

from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
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
            # Step 1: Get file content from Supabase storage (in-memory processing)
            import io

            import pdfplumber

            from app.core.database import db

            processing_logger.log_step(
                "loading_file_content", file_id=file_id, storage_path=file_path
            )

            # Get file content from Supabase storage
            client = await db.get_supabase_client()

            try:
                # Supabase storage download returns bytes directly
                file_content = client.storage.from_("documents").download(file_path)

                if not file_content:
                    raise ValueError(
                        f"Failed to download file from storage: {file_path} - No content received"
                    )

                # Ensure we have bytes
                if not isinstance(file_content, bytes):
                    raise ValueError(f"Downloaded content is not bytes: {type(file_content)}")

            except Exception as e:
                raise ValueError(f"Error downloading file from storage: {file_path} - {str(e)}")

            processing_logger.log_step(
                "file_content_loaded", file_id=file_id, size=len(file_content)
            )

            # Step 2: Process PDF directly from memory using pdfplumber
            processing_logger.log_step("pdf_memory_processing_start", file_id=file_id)

            documents = []
            with io.BytesIO(file_content) as pdf_buffer:
                with pdfplumber.open(pdf_buffer) as pdf:
                    full_text_parts = []
                    for page_num, page in enumerate(pdf.pages):
                        page_text = page.extract_text()
                        if page_text:
                            full_text_parts.append(page_text)
                            # Create LangChain-compatible document for each page
                            doc = Document(
                                page_content=page_text,
                                metadata={"page": page_num + 1, "source": file_path},
                            )
                            documents.append(doc)

                    processing_logger.log_step(
                        "pdf_memory_processing_complete",
                        file_id=file_id,
                        pages_processed=len(pdf.pages),
                        documents_created=len(documents),
                    )

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
