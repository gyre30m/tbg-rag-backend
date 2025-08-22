# Clean Up Citation Columns

## Step 1: Drop the verbose bluebook_citation column
```sql
ALTER TABLE documents DROP COLUMN IF EXISTS bluebook_citation;
```

## Step 2: Add comment to the citation column
```sql
COMMENT ON COLUMN documents.citation IS 'Citation for legal documents (Bluebook format for legal docs)';
```

Run these in the SQL Editor to clean up the duplicate citation columns.
