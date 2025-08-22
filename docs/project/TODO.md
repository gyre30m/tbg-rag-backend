# TBG RAG Backend - TODO List

## 🔧 Deployment Warnings to Fix
- [ ] **Install python-magic properly** - Currently using file extension fallback
  - Warning: `WARNING:root:python-magic not available, using extension-based file type detection`
  - Solution: Need to install libmagic system library for Railway deployment

- [ ] **Install PyMuPDF for PDF processing** - Currently PDF extraction is disabled
  - Warning: `WARNING:root:PyMuPDF not available, PDF extraction disabled`
  - Solution: Use the PyMuPDF installation notes provided earlier for proper setup

## 📊 Database Migrations ✅ COMPLETED

### Migration 1: Remove firm_id from documents table ✅
- [x] Removed `firm_id` column from `documents` table
- Reason: RAG documents don't have firm ownership (only forms do)
- Completed: 2025-01-21

### Migration 2: Add Bluebook citation field ✅
- [x] Added `bluebook_citation` field to `documents` table
- [x] Added `ai_bluebook_citation` to `processing_files` table
- Type: TEXT, nullable
- Purpose: Store proper legal citations for case law and statutes
- Completed: 2025-01-21

### Migration 3: Doc_category already correct ✅
- [x] Column already named `doc_category` (no rename needed)
- Verified: 2025-01-21

### Additional Migrations Completed ✅
- [x] Added missing fields to `documents` table:
  - status, char_count, chunk_count
  - reviewed_by, reviewed_at, review_notes
  - keywords, description
- [x] Added AI extraction fields to `processing_files` table:
  - ai_title, ai_authors, ai_publication_date
  - ai_doc_type, ai_doc_category, ai_description
  - ai_keywords, ai_confidence_scores
- [x] Added processing_file_id to `document_chunks` table
- [x] Created necessary indexes for performance
- Completed: 2025-01-21

## 🚀 Feature Enhancements
- [ ] Add proper PDF text extraction support
- [ ] Add DOCX text extraction support
- [ ] Implement Bluebook citation extraction for legal documents
- [ ] Add support for batch file uploads via UI
- [ ] Implement document versioning system

## 🐛 Known Issues
- [ ] FastAPI deprecation warnings for `@app.on_event` (should use lifespan context manager)
- [ ] No retry mechanism for failed AI extraction
- [ ] Missing rate limiting on API endpoints
- [ ] No caching layer for expensive operations

## 📝 Documentation
- [ ] Add API documentation with example requests
- [ ] Create deployment guide for other platforms
- [ ] Document the human review workflow
- [ ] Add troubleshooting guide for common issues

## 🔒 Security
- [ ] Add rate limiting to prevent abuse
- [ ] Implement API key authentication as alternative to JWT
- [ ] Add file virus scanning before processing
- [ ] Implement data retention policies

---
*Last Updated: 2025-01-21*
