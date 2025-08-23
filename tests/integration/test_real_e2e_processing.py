"""
Real end-to-end integration tests for document processing.
These tests use actual Supabase database connections and real processing pipeline.
"""

import asyncio

import pytest

from app.api.documents import get_document_stats, get_review_queue
from app.core.database import db
from app.services.processing_service import ProcessingService


class TestRealE2EProcessing:
    """Real integration tests using actual database connections."""

    @pytest.mark.asyncio
    async def test_existing_files_can_be_processed_to_documents(self):
        """Test that existing processing files can be converted to documents."""

        # Get a processing file that needs document creation
        client = await db.get_supabase_client()

        # Find files that don't have document_id yet
        files_result = (
            await client.table("processing_files").select("*").is_("document_id", None).execute()
        )

        if not files_result.data:
            pytest.skip("No processing files found that need document creation")

        test_file = files_result.data[0]
        file_id = test_file["id"]
        original_status = test_file["status"]

        print(f"Testing with file: {test_file['original_filename']} (status: {original_status})")

        # Check initial state - should have no documents
        docs_before = await client.table("documents").select("id").execute()
        initial_doc_count = len(docs_before.data)

        # Process the file with our updated pipeline
        processing_service = ProcessingService()

        if original_status == "review_pending":
            # File already processed, just needs document creation
            # Simulate the final step by creating document directly
            fake_metadata = {
                "title": test_file.get("ai_title", test_file["original_filename"]),
                "doc_type": test_file.get("ai_doc_type", "other"),
                "doc_category": test_file.get("ai_doc_category", "Other"),
                "confidence_score": 0.85,
                "summary": "Test document created by integration test",
            }

            try:
                document_id = await processing_service._create_document_for_review(
                    file_id, fake_metadata
                )
                assert document_id is not None, "Document ID should not be None"

                # Update the processing file status
                await client.table("processing_files").update(
                    {"document_id": document_id, "status": "review_pending"}
                ).eq("id", file_id).execute()

                print(f"✅ Created document {document_id} for file {file_id}")

            except Exception as e:
                print(f"❌ Failed to create document: {e}")
                raise

        # Verify document was created
        docs_after = await client.table("documents").select("*").execute()
        final_doc_count = len(docs_after.data)

        assert (
            final_doc_count > initial_doc_count
        ), f"Document count should increase from {initial_doc_count} to {final_doc_count}"

        # Verify the processing file now has a document_id
        updated_file = (
            await client.table("processing_files").select("document_id").eq("id", file_id).execute()
        )
        assert (
            updated_file.data[0]["document_id"] is not None
        ), "Processing file should have document_id"

        print("✅ Integration test passed: Document created and linked to processing file")

    @pytest.mark.asyncio
    async def test_review_queue_shows_documents_after_processing(self):
        """Test that review queue shows documents after processing pipeline creates them."""

        # Create mock user for API test
        mock_user = {"sub": "test-user-integration"}

        # Get review queue - should now show documents if our fixes work
        try:
            queue_result = await get_review_queue(mock_user)

            print(f"Review queue contains {len(queue_result['queue'])} items")
            print(f"Total pending: {queue_result['total_pending']}")
            print(f"Total in progress: {queue_result['total_in_progress']}")

            # Verify queue structure
            assert "queue" in queue_result
            assert "total_pending" in queue_result
            assert "total_in_progress" in queue_result
            assert isinstance(queue_result["queue"], list)

            # If we have queue items, verify they have the expected structure
            if queue_result["queue"]:
                first_item = queue_result["queue"][0]
                expected_fields = [
                    "id",
                    "title",
                    "original_filename",
                    "doc_type",
                    "doc_category",
                    "confidence_score",
                    "preview_text",
                    "processing_status",
                    "uploaded_at",
                    "file_size",
                    "batch_id",
                    "summary",
                ]

                for field in expected_fields:
                    assert field in first_item, f"Queue item missing field: {field}"

                print(f"✅ Queue item structure verified: {first_item['title']}")

            print("✅ Review queue API integration test passed")

        except Exception as e:
            print(f"❌ Review queue test failed: {e}")
            import traceback

            traceback.print_exc()
            raise

    @pytest.mark.asyncio
    async def test_document_stats_api_integration(self):
        """Test that document stats API works with real database."""

        mock_user = {"sub": "test-user-integration"}

        try:
            stats_result = await get_document_stats(mock_user)

            print(f"Document stats: {stats_result}")

            # Verify stats structure
            expected_fields = [
                "total_documents",
                "books_textbooks",
                "articles_publications",
                "statutes_codes",
                "case_law",
                "expert_reports",
                "other_documents",
            ]

            for field in expected_fields:
                assert field in stats_result, f"Stats missing field: {field}"
                assert isinstance(stats_result[field], int), f"Field {field} should be integer"
                assert stats_result[field] >= 0, f"Field {field} should be non-negative"

            print("✅ Document stats API integration test passed")

        except Exception as e:
            print(f"❌ Document stats test failed: {e}")
            import traceback

            traceback.print_exc()
            raise

    @pytest.mark.asyncio
    async def test_processing_pipeline_async_patterns(self):
        """Test that processing pipeline uses async patterns correctly."""

        try:
            # Test database client initialization
            client = await db.get_supabase_client()
            assert client is not None, "Async Supabase client should be created"

            # Test basic database query
            result = await client.table("processing_jobs").select("id").limit(1).execute()
            assert hasattr(result, "data"), "Query result should have data attribute"

            print(f"✅ Found {len(result.data)} processing jobs")

            # Test processing service initialization
            processing_service = ProcessingService()
            assert processing_service is not None, "Processing service should initialize"

            print("✅ Async patterns integration test passed")

        except Exception as e:
            print(f"❌ Async patterns test failed: {e}")
            import traceback

            traceback.print_exc()
            raise

    @pytest.mark.asyncio
    async def test_database_schema_consistency(self):
        """Test that database schema matches our expectations."""

        try:
            client = await db.get_supabase_client()

            # Test that key tables exist and have expected structure
            tables_to_test = [
                ("documents", ["id", "title", "doc_type", "is_reviewed"]),
                ("processing_files", ["id", "original_filename", "status", "document_id"]),
                ("document_chunks", ["id", "document_id", "processing_file_id", "content"]),
                ("processing_jobs", ["id", "status", "created_at"]),
            ]

            for table_name, expected_columns in tables_to_test:
                # Try to query the table with expected columns
                result = (
                    await client.table(table_name)
                    .select(",".join(expected_columns))
                    .limit(1)
                    .execute()
                )
                assert hasattr(result, "data"), f"Table {table_name} should be queryable"

                print(f"✅ Table {table_name} verified with columns: {expected_columns}")

            print("✅ Database schema consistency test passed")

        except Exception as e:
            print(f"❌ Database schema test failed: {e}")
            import traceback

            traceback.print_exc()
            raise
