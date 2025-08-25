-- Clear all data from database tables EXCEPT users table
-- This will remove all documents, processing files, chunks, etc.
-- WARNING: This action is irreversible!

-- Disable foreign key checks temporarily to avoid constraint issues
SET session_replication_role = replica;

-- Clear document-related tables (in order to respect foreign keys)
TRUNCATE TABLE document_chunks RESTART IDENTITY CASCADE;
TRUNCATE TABLE document_collection_items RESTART IDENTITY CASCADE;
TRUNCATE TABLE document_access RESTART IDENTITY CASCADE;
TRUNCATE TABLE document_relationships RESTART IDENTITY CASCADE;
TRUNCATE TABLE document_versions RESTART IDENTITY CASCADE;
TRUNCATE TABLE documents RESTART IDENTITY CASCADE;

-- Clear processing-related tables
TRUNCATE TABLE processing_files RESTART IDENTITY CASCADE;
TRUNCATE TABLE processing_jobs RESTART IDENTITY CASCADE;
TRUNCATE TABLE processing_webhooks RESTART IDENTITY CASCADE;

-- Clear search and analytics tables
TRUNCATE TABLE search_logs RESTART IDENTITY CASCADE;
TRUNCATE TABLE search_feedback RESTART IDENTITY CASCADE;
TRUNCATE TABLE saved_searches RESTART IDENTITY CASCADE;

-- Clear form-related tables
TRUNCATE TABLE form_audit_trail RESTART IDENTITY CASCADE;
TRUNCATE TABLE personal_injury_forms RESTART IDENTITY CASCADE;
TRUNCATE TABLE personal_injury_drafts RESTART IDENTITY CASCADE;
TRUNCATE TABLE wrongful_death_forms RESTART IDENTITY CASCADE;
TRUNCATE TABLE wrongful_death_drafts RESTART IDENTITY CASCADE;
TRUNCATE TABLE wrongful_termination_forms RESTART IDENTITY CASCADE;
TRUNCATE TABLE wrongful_termination_drafts RESTART IDENTITY CASCADE;

-- Clear organization-related tables (but keep user profiles)
TRUNCATE TABLE user_invitations RESTART IDENTITY CASCADE;
TRUNCATE TABLE document_collections RESTART IDENTITY CASCADE;
TRUNCATE TABLE firms RESTART IDENTITY CASCADE;

-- Clear admin and utility tables
TRUNCATE TABLE rag_admins RESTART IDENTITY CASCADE;
TRUNCATE TABLE forensic_documents RESTART IDENTITY CASCADE;

-- Re-enable foreign key checks
SET session_replication_role = DEFAULT;

-- Verify that users table is preserved
SELECT 'Users preserved:' as status, count(*) as user_count FROM auth.users;
SELECT 'User profiles preserved:' as status, count(*) as profile_count FROM user_profiles;

-- Show what's been cleared
SELECT 'Documents cleared:' as status, count(*) as count FROM documents;
SELECT 'Processing files cleared:' as status, count(*) as count FROM processing_files;
SELECT 'Document chunks cleared:' as status, count(*) as count FROM document_chunks;
