"""
Database connection and Supabase client configuration.
Handles both direct Supabase operations and raw SQL when needed.
"""

import logging
from typing import Optional

import supabase
from app.core.config import settings

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages database connections and operations."""

    def __init__(self):
        self._supabase_client: Optional[supabase.Client] = None

    @property  
    def supabase(self) -> supabase.Client:
        """Get or create Supabase client."""
        if self._supabase_client is None:
            self._supabase_client = supabase.create_client(
                settings.supabase_url,
                settings.supabase_secret_key,  # Using secret key for backend operations
            )
            logger.info("Supabase client initialized")
        return self._supabase_client

    async def execute_sql(self, query: str, params: dict = None) -> dict:
        """Execute raw SQL query via Supabase RPC."""
        try:
            # Use Supabase RPC for complex queries
            result = self.supabase.rpc("execute_sql", {"query": query}).execute()
            return {"success": True, "data": result.data}
        except Exception as e:
            logger.error(f"SQL execution failed: {e}")
            return {"success": False, "error": str(e)}

    async def health_check(self) -> bool:
        """Check database connectivity."""
        try:
            # Simple query to test connection
            result = self.supabase.table("processing_jobs").select("count").limit(1).execute()
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False


# Global database manager instance
db = DatabaseManager()
