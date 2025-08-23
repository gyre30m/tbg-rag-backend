"""
Database connection and Supabase client configuration.
Handles both direct Supabase operations and raw SQL when needed.
"""

import logging
from typing import Optional

from supabase import AsyncClient, acreate_client

from app.core.config import settings

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages database connections and operations."""

    def __init__(self):
        self._supabase_client: Optional[AsyncClient] = None

    async def get_supabase_client(self) -> AsyncClient:
        """Get or create async Supabase client."""
        if self._supabase_client is None:
            self._supabase_client = await acreate_client(
                settings.supabase_url,
                settings.supabase_secret_key,  # Using secret key for backend operations
            )
            logger.info("Async Supabase client initialized")
        return self._supabase_client

    @property
    async def supabase(self) -> AsyncClient:
        """Property to get async Supabase client."""
        return await self.get_supabase_client()

    async def execute_sql(self, query: str, params: dict = None) -> dict:
        """Execute raw SQL query via Supabase RPC."""
        try:
            # Use Supabase RPC for complex queries
            client = await self.get_supabase_client()
            result = await client.rpc("execute_sql", {"query": query}).execute()
            return {"success": True, "data": result.data}
        except Exception as e:
            logger.error(f"SQL execution failed: {e}")
            return {"success": False, "error": str(e)}

    async def health_check(self) -> bool:
        """Check database connectivity."""
        try:
            # Simple query to test connection
            client = await self.get_supabase_client()
            result = await client.table("processing_jobs").select("count").limit(1).execute()
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False


# Global database manager instance
db = DatabaseManager()
