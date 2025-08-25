-- Add processing_status column to documents table for detailed pipeline tracking
-- This replaces the complex processing_files status tracking with a simpler documents-only approach

-- Add processing_status column to track detailed pipeline stages
ALTER TABLE documents
ADD COLUMN IF NOT EXISTS processing_status text DEFAULT 'uploaded';

-- Add index for efficient filtering by processing status
CREATE INDEX IF NOT EXISTS idx_documents_processing_status
ON documents(processing_status);

-- Add comments for documentation
COMMENT ON COLUMN documents.processing_status IS 'Detailed processing pipeline status (uploaded, extracting_text, analyzing_metadata, generating_embeddings, processing_complete, processing_failed, ready_for_review)';

-- Update existing documents to have proper processing_status based on current status
UPDATE documents
SET processing_status = CASE
    WHEN status = 'processing' THEN 'processing_complete'
    WHEN status = 'review_pending' THEN 'ready_for_review'
    WHEN status = 'active' THEN 'processing_complete'
    ELSE 'uploaded'
END
WHERE processing_status = 'uploaded';  -- Only update documents that still have default status
