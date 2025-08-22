# Simple Migration - Run Each Step Separately

Run these one at a time in the SQL Editor. If any step gives an error, just skip it and move to the next one.

## Step 1: Create Enums (run this first)
```sql
DO $$ BEGIN
    CREATE TYPE doc_type_enum AS ENUM (
        'book', 'article', 'statute', 'case_law', 'expert_report', 'other'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE doc_category_enum AS ENUM (
        'PI', 'WD', 'EM', 'BV', 'Other'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;
```

## Step 2: Add Citation Column
```sql
ALTER TABLE documents ADD COLUMN IF NOT EXISTS citation text;
```

## Step 3: Drop firm_id Column
```sql
ALTER TABLE documents DROP COLUMN IF EXISTS firm_id;
```

## Step 4: Enable RLS on document_access
```sql
ALTER TABLE document_access ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view access they granted or received"
ON document_access FOR ALL
USING (granted_by = auth.uid() OR user_id = auth.uid());
```

## Step 5: Add Indexes
```sql
CREATE INDEX IF NOT EXISTS idx_documents_citation ON documents(citation) WHERE citation IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_documents_doc_type ON documents(doc_type);
CREATE INDEX IF NOT EXISTS idx_documents_doc_category ON documents(doc_category);
```

## Step 6: Add Comments
```sql
COMMENT ON TYPE doc_type_enum IS 'Document format/source types for RAG system';
COMMENT ON TYPE doc_category_enum IS 'Document domain/practice area categories';
COMMENT ON COLUMN documents.citation IS 'Bluebook citation for legal documents';
```

**Skip the enum conversion for now** - we can handle that later if needed. This gets us 90% of what we want without the headache!
