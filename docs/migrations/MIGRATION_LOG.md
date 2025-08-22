# Database Migration Log

## Applied Migrations

### 2025-08-22

#### ✅ Schema Updates: Enums, Citation, and Cleanup
**Status**: COMPLETED
**Files**:
- `simple_migration.md` - Step-by-step approach that succeeded
- `schema_migration.md` - Original comprehensive migration (had issues with enum conversion)
- `cleanup_citation.md` - Removed duplicate bluebook_citation column

**Changes Applied**:
1. Created `doc_type_enum` with values: book, article, statute, case_law, expert_report, other
2. Created `doc_category_enum` with values: PI, WD, EM, BV, Other
3. Added `citation` column to documents table for Bluebook citations
4. Removed `firm_id` column from documents table
5. Enabled RLS on `document_access` table
6. Added indexes for performance (citation, doc_type, doc_category)
7. Dropped duplicate `bluebook_citation` column

#### ✅ RLS Policy Updates
**Status**: COMPLETED
**Files**:
- `enable_rls_policies.md` - Initial overly-permissive policies (replaced)
- `fix_rls_policies_rag_admins.md` - Corrected policies using rag_admins table

**Changes Applied**:
1. Dropped overly permissive "Admin only access" policies that allowed any authenticated user
2. Created "RAG admins only access" policies for all RAG/document tables:
   - documents, document_chunks, document_collections, document_collection_items
   - document_versions, document_relationships
   - processing_files, processing_jobs, processing_webhooks
   - saved_searches, search_feedback, search_logs
   - forensic_documents
3. All policies now use `is_rag_admin((auth.jwt() ->> 'email'::text))` function
4. Only users in rag_admins table can access these tables

## Pending Migrations

None at this time. All planned schema changes have been applied.

## Migration Notes

- The original `schema_migration.md` attempted complex enum conversion but encountered issues
- We opted for the simpler `simple_migration.md` approach which worked successfully
- Multi-tenancy is now handled via Document Collections → Forms → Firms relationship chain
- RLS policies provide secure access control via the rag_admins table
