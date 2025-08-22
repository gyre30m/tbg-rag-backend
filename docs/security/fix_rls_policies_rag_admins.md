# Fix RLS Policies - Use rag_admins Table

Run these SQL commands to drop the overly permissive policies and replace them with rag_admins-based policies.

## Drop Existing "Admin only access" Policies

```sql
-- Drop the overly permissive policies
DROP POLICY IF EXISTS "Admin only access" ON documents;
DROP POLICY IF EXISTS "Admin only access" ON document_chunks;
DROP POLICY IF EXISTS "Admin only access" ON document_collections;
DROP POLICY IF EXISTS "Admin only access" ON document_collection_items;
DROP POLICY IF EXISTS "Admin only access" ON document_versions;
DROP POLICY IF EXISTS "Admin only access" ON document_relationships;
DROP POLICY IF EXISTS "Admin only access" ON processing_files;
DROP POLICY IF EXISTS "Admin only access" ON processing_jobs;
DROP POLICY IF EXISTS "Admin only access" ON processing_webhooks;
DROP POLICY IF EXISTS "Admin only access" ON saved_searches;
DROP POLICY IF EXISTS "Admin only access" ON search_feedback;
DROP POLICY IF EXISTS "Admin only access" ON search_logs;
DROP POLICY IF EXISTS "Admin only access" ON forensic_documents;
```

## Create RAG Admin Policies

```sql
-- Document Tables - Only RAG admins
CREATE POLICY "RAG admins only access" ON documents
FOR ALL USING (is_rag_admin((auth.jwt() ->> 'email'::text)));

CREATE POLICY "RAG admins only access" ON document_chunks
FOR ALL USING (is_rag_admin((auth.jwt() ->> 'email'::text)));

CREATE POLICY "RAG admins only access" ON document_collections
FOR ALL USING (is_rag_admin((auth.jwt() ->> 'email'::text)));

CREATE POLICY "RAG admins only access" ON document_collection_items
FOR ALL USING (is_rag_admin((auth.jwt() ->> 'email'::text)));

CREATE POLICY "RAG admins only access" ON document_versions
FOR ALL USING (is_rag_admin((auth.jwt() ->> 'email'::text)));

CREATE POLICY "RAG admins only access" ON document_relationships
FOR ALL USING (is_rag_admin((auth.jwt() ->> 'email'::text)));

-- Processing Tables - Only RAG admins
CREATE POLICY "RAG admins only access" ON processing_files
FOR ALL USING (is_rag_admin((auth.jwt() ->> 'email'::text)));

CREATE POLICY "RAG admins only access" ON processing_jobs
FOR ALL USING (is_rag_admin((auth.jwt() ->> 'email'::text)));

CREATE POLICY "RAG admins only access" ON processing_webhooks
FOR ALL USING (is_rag_admin((auth.jwt() ->> 'email'::text)));

-- Search Tables - Only RAG admins
CREATE POLICY "RAG admins only access" ON saved_searches
FOR ALL USING (is_rag_admin((auth.jwt() ->> 'email'::text)));

CREATE POLICY "RAG admins only access" ON search_feedback
FOR ALL USING (is_rag_admin((auth.jwt() ->> 'email'::text)));

CREATE POLICY "RAG admins only access" ON search_logs
FOR ALL USING (is_rag_admin((auth.jwt() ->> 'email'::text)));

-- Other Tables - Only RAG admins
CREATE POLICY "RAG admins only access" ON forensic_documents
FOR ALL USING (is_rag_admin((auth.jwt() ->> 'email'::text)));
```

## What this does:
- **Drops** all the overly permissive policies that allowed any authenticated user
- **Creates new policies** that only allow users listed in the `rag_admins` table to access these RAG/document tables
- **Uses the existing `is_rag_admin()` function** which checks if the user's email exists in the `rag_admins` table
- **Provides flexibility** - you can add more RAG admins in the future by simply adding their emails to the `rag_admins` table
- **Maintains consistency** with your existing `rag_admins` table policies

After running this, only users in the `rag_admins` table will be able to CRUD the RAG system tables, while the forms and firms tables maintain their existing multi-user policies.
