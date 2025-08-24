-- Add status column and enum to documents table
-- Date: 2025-08-24

-- Step 1: Create document_status_enum
DO $$ BEGIN
    CREATE TYPE document_status_enum AS ENUM (
        'processing',        -- Document is being processed
        'review_pending',    -- Ready for human review
        'active',           -- Approved and in library
        'deleted',          -- Soft deleted
        'archived'          -- Archived for long-term storage
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Step 2: Add status column to documents table
ALTER TABLE documents
ADD COLUMN IF NOT EXISTS status document_status_enum DEFAULT 'processing';

-- Step 3: Update existing documents to have proper status
UPDATE documents
SET status = CASE
    WHEN is_deleted = true THEN 'deleted'::document_status_enum
    WHEN is_archived = true THEN 'archived'::document_status_enum
    WHEN is_reviewed = true THEN 'active'::document_status_enum
    ELSE 'processing'::document_status_enum
END;

-- Step 4: Add constraint to ensure status is not null
ALTER TABLE documents
ALTER COLUMN status SET NOT NULL;

-- Step 5: Add check constraint for valid statuses
ALTER TABLE documents
ADD CONSTRAINT chk_documents_status
CHECK (status IN ('processing', 'review_pending', 'active', 'deleted', 'archived'));

-- Step 6: Create index for status filtering
CREATE INDEX IF NOT EXISTS idx_documents_status
ON documents(status);

-- Comments for documentation
COMMENT ON TYPE document_status_enum IS 'Document status for processing pipeline and library management';
COMMENT ON COLUMN documents.status IS 'Current status of document in processing pipeline (constrained by enum)';
