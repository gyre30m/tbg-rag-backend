-- Clean up unused columns and add keywords column to documents table
-- Also ensure metadata fields are properly set up

-- Remove unused columns from legacy system
ALTER TABLE documents
DROP COLUMN IF EXISTS discount_rates,
DROP COLUMN IF EXISTS damage_amounts,
DROP COLUMN IF EXISTS methodologies,
DROP COLUMN IF EXISTS subject_ages,
DROP COLUMN IF EXISTS education_levels;

-- Add keywords column if it doesn't exist
ALTER TABLE documents
ADD COLUMN IF NOT EXISTS keywords text[] DEFAULT '{}';

-- Add summary column if it doesn't exist (for full document summary)
ALTER TABLE documents
ADD COLUMN IF NOT EXISTS summary text;

-- Add preview_text column for document preview
ALTER TABLE documents
ADD COLUMN IF NOT EXISTS preview_text text;

-- Ensure metadata columns exist
ALTER TABLE documents
ADD COLUMN IF NOT EXISTS page_count integer,
ADD COLUMN IF NOT EXISTS word_count integer,
ADD COLUMN IF NOT EXISTS char_count integer,
ADD COLUMN IF NOT EXISTS chunk_count integer;

-- Add tags column for user-defined tags (separate from AI keywords)
ALTER TABLE documents
ADD COLUMN IF NOT EXISTS tags text[] DEFAULT '{}';

-- Add indexes for better search performance
CREATE INDEX IF NOT EXISTS idx_documents_keywords ON documents USING gin(keywords);
CREATE INDEX IF NOT EXISTS idx_documents_tags ON documents USING gin(tags);

-- Add comment to clarify the difference between keywords and tags
COMMENT ON COLUMN documents.keywords IS 'AI-extracted keywords from document content';
COMMENT ON COLUMN documents.tags IS 'User-defined tags for organization';
COMMENT ON COLUMN documents.summary IS 'AI-generated summary of document content';
COMMENT ON COLUMN documents.preview_text IS 'First portion of document text for preview';
