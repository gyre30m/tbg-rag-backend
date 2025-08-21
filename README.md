# TBG RAG Document Ingestion Backend

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/7uJqm-)

A FastAPI-based backend service for the TBG Agentic RAG System's document ingestion pipeline. This service handles document upload, processing, AI metadata extraction, and vector embedding generation for the forensic economics document library.

## 🚀 Live Deployment

This backend is automatically deployed to Railway on every push to the main branch.

## 🏗️ Architecture

### Core Components

- **FastAPI Application**: Modern async web framework with automatic API documentation
- **Supabase Integration**: Database, authentication, and file storage
- **Document Processing Pipeline**: Text extraction → AI metadata → Vector embeddings
- **Authentication**: RS256 JWT token verification with Supabase
- **File Management**: Upload validation, storage, and retrieval

### Processing Pipeline

1. **Upload** → File validation and storage in Supabase
2. **Text Extraction** → PDF/DOCX/TXT content extraction
3. **AI Metadata** → Claude/OpenAI metadata extraction (title, authors, type, etc.)
4. **Vector Embeddings** → OpenAI text-embedding-3-small chunk embeddings
5. **Human Review** → Approval workflow for library inclusion

## 📁 Project Structure

```
webapp-backend/
├── app/
│   ├── main.py                 # FastAPI application entry point
│   ├── core/
│   │   ├── config.py          # Pydantic settings configuration
│   │   ├── database.py        # Supabase client and connection
│   │   └── security.py        # JWT authentication logic
│   ├── models/
│   │   ├── enums.py          # Status enums and constants
│   │   ├── documents.py      # Document Pydantic models
│   │   └── processing.py     # Processing job models
│   ├── services/
│   │   ├── file_service.py           # File upload and validation
│   │   ├── extraction_service.py     # Text extraction (PDF/DOCX)
│   │   ├── ai_service.py             # AI metadata extraction
│   │   ├── embedding_service.py      # Vector embedding generation
│   │   └── processing_service.py     # Pipeline orchestration
│   ├── api/
│   │   ├── documents.py       # Document upload and library endpoints
│   │   ├── processing.py      # Processing status and management
│   │   └── webhooks.py        # Processing notifications
│   └── utils/
│       └── file_utils.py      # File validation utilities
├── requirements.txt           # Python dependencies
├── .env.example              # Environment variables template
├── test_structure.py         # Structure validation script
└── README.md                 # This file
```

## 🚀 Getting Started

### Prerequisites

- Python 3.9+
- Supabase project with pgvector extension
- OpenAI API key (for embeddings and optional metadata extraction)
- Anthropic API key (optional, for metadata extraction)

### Installation

1. **Clone and navigate to backend directory**
   ```bash
   cd /path/to/tbg/webapp-backend
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your actual credentials
   ```

4. **Configure environment variables**
   ```env
   # Supabase Configuration
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_PUBLISHABLE_KEY=eyJ...
   SUPABASE_SECRET_KEY=eyJ...
   
   # AI API Keys
   OPENAI_API_KEY=sk-...
   ANTHROPIC_API_KEY=sk-ant-...
   
   # Application Settings
   DEBUG=true
   LOG_LEVEL=info
   MAX_FILE_SIZE=52428800  # 50MB
   SUPPORTED_MIME_TYPES=application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,text/plain,text/markdown
   MAX_FILES_PER_BATCH=10
   
   # Security
   JWT_SECRET_KEY=your-jwt-secret
   WEBHOOK_SECRET=your-webhook-secret
   ```

5. **Run the application**
   ```bash
   python -m app.main
   ```

The API will be available at `http://localhost:8000` with interactive documentation at `http://localhost:8000/docs`.

## 📚 API Endpoints

### Documents API (`/api/documents/`)

- `POST /upload` - Upload multiple documents for processing
- `GET /processing-status/{batch_id}` - Get processing status for a batch
- `POST /approve/{file_id}` - Approve processed file for library
- `POST /reject/{file_id}` - Reject processed file
- `POST /search` - Vector similarity search
- `GET /library` - List library documents
- `GET /library/{document_id}` - Get document details
- `DELETE /library/{document_id}` - Delete document (soft delete)

### Processing API (`/api/processing/`)

- `POST /batch/{batch_id}/process` - Manually trigger batch processing
- `GET /batches` - List processing batches
- `GET /files/pending-review` - List files ready for review
- `GET /files/{file_id}` - Get processing file details
- `GET /files/{file_id}/text` - Get extracted text
- `GET /files/{file_id}/chunks` - Get text chunks
- `POST /files/{file_id}/retry` - Retry failed processing
- `GET /stats` - Get processing statistics

### Webhooks API (`/api/webhooks/`)

- `POST /processing/status` - Processing status notifications
- `POST /test` - Test webhook endpoint
- `GET /health` - Webhook health check

## 🔧 Configuration

### File Processing Limits

- **Max file size**: 50MB (configurable)
- **Supported formats**: PDF, DOCX, TXT, MD
- **Max files per batch**: 10 (configurable)
- **Max text length**: 10MB (for processing)

### AI Services

- **Anthropic Claude**: Primary metadata extraction (Haiku model)
- **OpenAI GPT-4**: Fallback metadata extraction (GPT-4o-mini)
- **OpenAI Embeddings**: Vector embeddings (text-embedding-3-small)

### Document Types and Categories

**Document Types:**
- `book` - Books, textbooks, reference materials
- `article` - Academic papers, journal articles
- `statute` - Laws, regulations, statutes
- `case_law` - Court cases, legal precedents
- `expert_report` - Expert witness reports
- `other` - Other document types

**Document Categories:**
- `PI` - Personal Injury
- `WD` - Wrongful Death
- `EM` - Employment
- `BV` - Business Valuation
- `Other` - Other practice areas

## 🔐 Authentication

The API uses Supabase JWT tokens for authentication:

1. Users authenticate through the frontend application
2. Frontend receives JWT token from Supabase Auth
3. API endpoints verify JWT signature using RS256 with Supabase public key
4. User information is extracted from token claims

## 🔄 Processing Workflow

### File Status Flow
```
uploaded → queued_for_extraction → extracting_text → text_extracted 
→ extracting_metadata → metadata_extracted → generating_embeddings 
→ embeddings_generated → ready_for_review → approved_for_library
```

### Error States
```
extraction_failed → [retry] → uploaded
ai_failed → [retry] → text_extracted  
embedding_failed → [retry] → metadata_extracted
processing_failed → [retry] → uploaded
rejected → [manual intervention]
```

### Batch Status Flow
```
created → uploaded → processing → completed/partially_failed/failed
```

## 🧪 Testing

Run structure validation:
```bash
python test_structure.py
```

## 📊 Monitoring

The application provides several monitoring endpoints:

- `/health` - Application health check
- `/api/processing/stats` - Processing statistics
- `/api/webhooks/health` - Webhook service health

## 🔧 Development

### Code Organization

- **Services**: Business logic and external API integration
- **Models**: Pydantic schemas for request/response validation
- **API**: FastAPI route handlers
- **Core**: Configuration, database, and security utilities
- **Utils**: Shared utility functions

### Key Design Decisions

1. **File-level processing**: Each file processed independently with its own status
2. **Async/await**: Full async support for high concurrency
3. **Pydantic validation**: Strong typing and validation throughout
4. **Modern Supabase**: Uses latest authentication and client libraries
5. **AI flexibility**: Support for multiple AI providers with fallbacks

## 📈 Performance

- **Concurrent processing**: Configurable concurrent file processing
- **Chunked embeddings**: Text split into optimized chunks for vector search
- **Batch operations**: Efficient database operations
- **Rate limiting**: Built-in API rate limiting respect

## 🛡️ Security

- **File validation**: MIME type and content validation
- **JWT verification**: Secure token verification with RS256
- **Input sanitization**: All inputs validated through Pydantic
- **Webhook signatures**: Optional webhook signature verification
- **Path traversal protection**: Safe filename generation

---

## 📝 Code Statistics

- **Total files**: 24 Python files
- **Lines of code**: 3,447 lines
- **Test coverage**: Structure validation included

This backend provides a robust, scalable foundation for the TBG RAG document ingestion system with comprehensive error handling, monitoring, and security features.