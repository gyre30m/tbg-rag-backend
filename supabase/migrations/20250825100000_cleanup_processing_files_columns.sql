-- Clean up processing_files table by removing redundant ai_* metadata columns
-- These columns are now stored directly in the documents table

-- Drop AI metadata columns that are redundant with documents table
ALTER TABLE processing_files
DROP COLUMN IF EXISTS ai_title,
DROP COLUMN IF EXISTS ai_authors,
DROP COLUMN IF EXISTS ai_publication_date,
DROP COLUMN IF EXISTS ai_doc_type,
DROP COLUMN IF EXISTS ai_doc_category,
DROP COLUMN IF EXISTS ai_description,
DROP COLUMN IF EXISTS ai_keywords,
DROP COLUMN IF EXISTS ai_bluebook_citation,
DROP COLUMN IF EXISTS ai_confidence_scores,
DROP COLUMN IF EXISTS ai_court,
DROP COLUMN IF EXISTS ai_identified_amounts,
DROP COLUMN IF EXISTS ai_identified_rates,
DROP COLUMN IF EXISTS ai_case_name,
DROP COLUMN IF EXISTS ai_case_number,
DROP COLUMN IF EXISTS ai_jurisdiction,
DROP COLUMN IF EXISTS ai_practice_area;

-- Add comment explaining the simplified architecture
COMMENT ON TABLE processing_files IS 'Tracks file processing pipeline and batch information. After successful processing, large fields like extracted_text are cleared to save storage. Metadata is stored directly in documents table.';

-- Update comments on remaining columns
COMMENT ON COLUMN processing_files.extracted_text IS 'Full extracted text - cleared after successful processing to save storage';
COMMENT ON COLUMN processing_files.preview_text IS 'Text preview - cleared after successful processing (stored in documents)';
COMMENT ON COLUMN processing_files.page_count IS 'Page count - cleared after successful processing (stored in documents)';
COMMENT ON COLUMN processing_files.word_count IS 'Word count - cleared after successful processing (stored in documents)';
COMMENT ON COLUMN processing_files.char_count IS 'Character count - cleared after successful processing (stored in documents)';
COMMENT ON COLUMN processing_files.chunk_count IS 'Chunk count - cleared after successful processing (stored in documents)';
