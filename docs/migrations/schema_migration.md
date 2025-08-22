# Schema Migration: Enums, Citation, RLS

Copy and paste this SQL into the Supabase SQL Editor:

```sql
-- Schema Updates: Remove firm_id, Add citation, Create enums, Enable RLS
-- Date: 2025-08-22

-- Step 1: Create enums for doc_type and doc_category
DO $$ BEGIN
    CREATE TYPE doc_type_enum AS ENUM (
        'book',
        'article',
        'statute',
        'case_law',
        'expert_report',
        'other'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE doc_category_enum AS ENUM (
        'PI',   -- Personal Injury
        'WD',   -- Wrongful Death
        'EM',   -- Employment
        'BV',   -- Business Valuation
        'Other' -- General/uncategorized
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Step 2: Add citation column to documents table
ALTER TABLE documents
ADD COLUMN IF NOT EXISTS citation text;

-- Step 3: Drop firm_id column from documents table
-- (Multi-tenancy handled via Document Collections -> Forms -> Firms relationship)
ALTER TABLE documents
DROP COLUMN IF EXISTS firm_id;

-- Step 4: Update doc_type column to use enum (handle existing enum or text)
DO $$
BEGIN
    -- Check if column is already enum type
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'documents'
        AND column_name = 'doc_type'
        AND udt_name = 'doc_type_enum'
    ) THEN
        -- Already enum, just update values if needed
        UPDATE documents
        SET doc_type = 'other'::doc_type_enum
        WHERE doc_type IS NULL;
    ELSE
        -- Still text, convert to enum
        UPDATE documents
        SET doc_type = 'other'
        WHERE doc_type IS NULL OR doc_type NOT IN ('book', 'article', 'statute', 'case_law', 'expert_report', 'other');

        ALTER TABLE documents ALTER COLUMN doc_type DROP DEFAULT;
        ALTER TABLE documents
        ALTER COLUMN doc_type TYPE doc_type_enum
        USING doc_type::doc_type_enum;
    END IF;
END $$;

-- Step 5: Update doc_category column to use enum (handle existing enum or text)
DO $$
BEGIN
    -- Check if column is already enum type
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'documents'
        AND column_name = 'doc_category'
        AND udt_name = 'doc_category_enum'
    ) THEN
        -- Already enum, just update values if needed
        UPDATE documents
        SET doc_category = 'Other'::doc_category_enum
        WHERE doc_category IS NULL;
    ELSE
        -- Still text, convert to enum
        UPDATE documents
        SET doc_category = 'Other'
        WHERE doc_category IS NULL OR doc_category NOT IN ('PI', 'WD', 'EM', 'BV', 'Other');

        ALTER TABLE documents ALTER COLUMN doc_category DROP DEFAULT;
        ALTER TABLE documents
        ALTER COLUMN doc_category TYPE doc_category_enum
        USING doc_category::doc_category_enum;
    END IF;
END $$;

-- Step 6: Enable RLS on document_access table
ALTER TABLE document_access ENABLE ROW LEVEL SECURITY;

-- Add basic RLS policy - users can only see access records they granted or were granted to them
CREATE POLICY "Users can view access they granted or received"
ON document_access
FOR ALL
USING (
  granted_by = auth.uid() OR
  user_id = auth.uid()
);

-- Step 7: Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_documents_citation
ON documents(citation)
WHERE citation IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_documents_doc_type
ON documents(doc_type);

CREATE INDEX IF NOT EXISTS idx_documents_doc_category
ON documents(doc_category);

-- Step 8: Add constraints
ALTER TABLE documents
ALTER COLUMN doc_type SET NOT NULL;

ALTER TABLE documents
ALTER COLUMN doc_category SET NOT NULL;

-- Comments for documentation
COMMENT ON TYPE doc_type_enum IS 'Document format/source types for RAG system';
COMMENT ON TYPE doc_category_enum IS 'Document domain/practice area categories';
COMMENT ON COLUMN documents.citation IS 'Bluebook citation for legal documents';
COMMENT ON COLUMN documents.doc_type IS 'Document format/source type (constrained by enum)';
COMMENT ON COLUMN documents.doc_category IS 'Document practice area category (constrained by enum)';
```

## What this migration does:

1. ✅ **Creates enums** for `doc_type` and `doc_category` with proper values
2. ✅ **Adds citation column** for Bluebook citations
3. ✅ **Removes firm_id column** (clean architecture via document collections)
4. ✅ **Converts existing columns** to use the new enums
5. ✅ **Enables RLS** on `document_access` table with proper policy
6. ✅ **Adds performance indexes** for the new columns
7. ✅ **Adds constraints** to ensure data integrity
8. ✅ **Documents everything** with comments

Copy the SQL block above and paste it into the Supabase SQL Editor, then click **Run**.
