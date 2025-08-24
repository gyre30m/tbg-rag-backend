-- Rename text_content column to content in document_chunks table
-- This standardizes on 'content' and removes the confusing text_content/content duality

ALTER TABLE document_chunks
RENAME COLUMN text_content TO content;

-- Update the NOT NULL constraint if it exists
-- The column should remain nullable for now since document_id is set later
ALTER TABLE document_chunks
ALTER COLUMN content DROP NOT NULL;
