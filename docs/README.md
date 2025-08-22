# TBG RAG Backend Documentation

This directory contains all documentation for the TBG RAG Backend system, organized by category.

## 📁 Directory Structure

### `/migrations/`
Database migration scripts and schema changes:
- `schema_migration.md` - Full schema migration with enums, citation, and RLS
- `simple_migration.md` - Simplified step-by-step migration approach
- `cleanup_citation.md` - Script to clean up duplicate citation columns

### `/security/`
Security and access control documentation:
- `enable_rls_policies.md` - Initial RLS policy setup for all tables
- `fix_rls_policies_rag_admins.md` - Corrected RLS policies using rag_admins table

### `/project/`
Project management and planning:
- `TODO.md` - Project todo list and completed tasks

## 🔗 Quick Links

- [Main README](../README.md) - Project overview and setup instructions
- [Frontend Docs](../../webapp/docs/) - Frontend-specific documentation
- [API Documentation](../app/api/) - API endpoint implementations

## 📝 Recent Changes

**2025-08-22**:
- Organized documentation into structured directories
- Applied schema migrations (removed firm_id, added citation, created enums)
- Fixed RLS policies to use rag_admins table
- Set up TypeScript type generation workflow

## 🚀 Getting Started

1. Review the [Main README](../README.md) for setup instructions
2. Check [TODO.md](project/TODO.md) for current project status
3. See migration files for database schema details
4. Review security docs for access control configuration
