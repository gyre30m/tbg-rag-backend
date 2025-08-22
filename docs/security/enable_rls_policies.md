# Enable RLS and Create Admin-Only Policies

Run these SQL commands to enable RLS and create policies that only allow authenticated users (you) to access the tables.

## Document-related Tables

```sql
-- Enable RLS on documents table
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Admin only access" ON documents FOR ALL USING (auth.uid() IS NOT NULL);

-- Enable RLS on document_chunks table
ALTER TABLE document_chunks ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Admin only access" ON document_chunks FOR ALL USING (auth.uid() IS NOT NULL);

-- Enable RLS on document_collections table
ALTER TABLE document_collections ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Admin only access" ON document_collections FOR ALL USING (auth.uid() IS NOT NULL);

-- Enable RLS on document_collection_items table
ALTER TABLE document_collection_items ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Admin only access" ON document_collection_items FOR ALL USING (auth.uid() IS NOT NULL);

-- Enable RLS on document_versions table
ALTER TABLE document_versions ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Admin only access" ON document_versions FOR ALL USING (auth.uid() IS NOT NULL);

-- Enable RLS on document_relationships table
ALTER TABLE document_relationships ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Admin only access" ON document_relationships FOR ALL USING (auth.uid() IS NOT NULL);
```

## Search and Processing Tables

```sql
-- Enable RLS on saved_searches table
ALTER TABLE saved_searches ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Admin only access" ON saved_searches FOR ALL USING (auth.uid() IS NOT NULL);

-- Enable RLS on search_feedback table
ALTER TABLE search_feedback ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Admin only access" ON search_feedback FOR ALL USING (auth.uid() IS NOT NULL);

-- Enable RLS on search_logs table
ALTER TABLE search_logs ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Admin only access" ON search_logs FOR ALL USING (auth.uid() IS NOT NULL);

-- Enable RLS on processing_files table
ALTER TABLE processing_files ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Admin only access" ON processing_files FOR ALL USING (auth.uid() IS NOT NULL);

-- Enable RLS on processing_jobs table
ALTER TABLE processing_jobs ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Admin only access" ON processing_jobs FOR ALL USING (auth.uid() IS NOT NULL);

-- Enable RLS on processing_webhooks table
ALTER TABLE processing_webhooks ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Admin only access" ON processing_webhooks FOR ALL USING (auth.uid() IS NOT NULL);

-- Enable RLS on forensic_documents table
ALTER TABLE forensic_documents ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Admin only access" ON forensic_documents FOR ALL USING (auth.uid() IS NOT NULL);
```

## What this does:
- **Enables RLS** on all the missing tables
- **Creates "Admin only" policies** that only allow access when `auth.uid() IS NOT NULL` (i.e., user is authenticated)
- **Applies to all operations** (SELECT, INSERT, UPDATE, DELETE)

This ensures only authenticated users (you) can access these tables, providing complete security for your RAG system data.
