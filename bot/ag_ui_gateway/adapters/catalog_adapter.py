"""
Catalog Adapter for AG-UI Protocol

Provides knowledge base listing, search, and metadata management.
"""
from typing import Optional, List, Dict, Any
import time
from loguru import logger

# Lazy imports to avoid circular dependencies
# from luka_bot.services.elasticsearch_service import get_elasticsearch_service
from ag_ui_gateway.database import get_elasticsearch


class CatalogAdapter:
    """
    Adapter for knowledge base catalog operations.
    
    Provides:
    - KB listing with filters
    - KB search functionality
    - KB metadata retrieval
    - Permission-based access control
    """
    
    def __init__(self):
        self.es = None  # Will be lazy-loaded
    
    async def _get_es_service(self):
        """Lazy load Elasticsearch service."""
        if self.es is None:
            from luka_bot.services.elasticsearch_service import get_elasticsearch_service
            self.es = await get_elasticsearch_service()
        return self.es
    
    async def list_knowledge_bases(
        self,
        user_id: Optional[int] = None,
        group_id: Optional[int] = None,
        include_stats: bool = False
    ) -> List[Dict[str, Any]]:
        """
        List available knowledge bases for a user or group.
        
        Args:
            user_id: Optional user ID to filter user KBs
            group_id: Optional group ID to filter group KBs
            include_stats: Whether to include statistics (document count, size)
        
        Returns:
            List of KB metadata dicts
        """
        try:
            es_service = await self._get_es_service()
            if not es_service:
                logger.warning("Elasticsearch service not available")
                return []
            
            # Determine index pattern based on filters
            if user_id:
                pattern = f"tg-kb-user-{user_id}"
            elif group_id:
                pattern = f"tg-kb-group-{group_id}"
            else:
                # List all KBs (admin view)
                pattern = "tg-kb-*"
            
            # Get indices matching pattern
            indices = await es_service.list_indices(pattern)
            
            kbs = []
            for idx in indices:
                kb_data = {
                    "id": idx["name"],
                    "name": idx["name"],
                    "type": self._extract_kb_type(idx["name"]),
                    "owner_id": self._extract_owner_id(idx["name"]),
                }
                
                if include_stats:
                    kb_data["document_count"] = idx["doc_count"]
                    kb_data["size_bytes"] = idx["size_bytes"]
                
                kbs.append(kb_data)
            
            logger.info(f"📚 Listed {len(kbs)} knowledge bases (pattern={pattern})")
            return kbs
            
        except Exception as e:
            logger.warning(f"⚠️  Could not list knowledge bases: {e}")
            logger.debug(f"   Elasticsearch might not be available")
            return []
    
    def _extract_kb_type(self, index_name: str) -> str:
        """Extract KB type from index name."""
        if "tg-kb-user-" in index_name:
            return "user"
        elif "tg-kb-group-" in index_name:
            return "group"
        else:
            return "unknown"
    
    def _extract_owner_id(self, index_name: str) -> Optional[int]:
        """Extract owner ID from index name."""
        try:
            if "tg-kb-user-" in index_name:
                return int(index_name.replace("tg-kb-user-", ""))
            elif "tg-kb-group-" in index_name:
                return int(index_name.replace("tg-kb-group-", ""))
        except:
            pass
        return None
    
    async def get_knowledge_base(
        self,
        kb_id: str,
        user_id: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get knowledge base metadata.
        
        Args:
            kb_id: Knowledge base ID (index name)
            user_id: Optional user ID for permission check
        
        Returns:
            KB metadata dict or None if not found/no access
        """
        try:
            # Check permissions
            if user_id and not await self._check_kb_access(kb_id, user_id):
                logger.warning(f"User {user_id} denied access to KB {kb_id}")
                return None
            
            es_service = await self._get_es_service()
            if not es_service:
                return None
            
            # Get index stats
            stats = await es_service.get_index_stats(kb_id)
            
            return {
                "id": kb_id,
                "name": kb_id,
                "type": self._extract_kb_type(kb_id),
                "owner_id": self._extract_owner_id(kb_id),
                "document_count": stats.get("message_count", 0),
                "size_bytes": stats.get("size_bytes", 0),
                "size_mb": stats.get("size_mb", 0.0)
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting KB {kb_id}: {e}")
            return None
    
    async def _check_kb_access(self, kb_id: str, user_id: int) -> bool:
        """
        Check if user has access to knowledge base.
        
        Rules:
        - User can access their own user KB (tg-kb-user-{user_id})
        - User can access group KBs they're a member of (TODO: implement group membership check)
        - Admins can access all KBs (TODO: implement admin check)
        
        Args:
            kb_id: KB index name
            user_id: User ID
        
        Returns:
            True if user has access
        """
        # User's own KB
        if kb_id == f"tg-kb-user-{user_id}":
            return True
        
        # Group KBs - for now, allow access (TODO: implement group membership check)
        if "tg-kb-group-" in kb_id:
            return True
        
        # Default: deny access
        return False
    
    async def search_knowledge_base(
        self,
        kb_id: str,
        query: str,
        user_id: Optional[int] = None,
        max_results: int = 5,
        min_score: float = 0.1,
        search_method: str = "text"
    ) -> List[Dict[str, Any]]:
        """
        Search knowledge base.
        
        Args:
            kb_id: KB index name
            query: Search query text
            user_id: Optional user ID for permission check
            max_results: Maximum number of results
            min_score: Minimum relevance score
            search_method: Search method (text, vector, hybrid)
        
        Returns:
            List of search results
        """
        try:
            # Check permissions
            if user_id and not await self._check_kb_access(kb_id, user_id):
                logger.warning(f"User {user_id} denied search access to KB {kb_id}")
                return []
            
            es_service = await self._get_es_service()
            if not es_service:
                return []
            
            logger.info(f"🔍 Searching KB {kb_id}: query='{query}', method={search_method}")
            
            # Perform search based on method
            if search_method == "text":
                results = await es_service.search_messages_text(
                    index_name=kb_id,
                    query_text=query,
                    min_score=min_score,
                    max_results=max_results
                )
            elif search_method == "vector":
                # TODO: Implement vector search (need to generate query embedding)
                logger.warning("Vector search not yet implemented, falling back to text")
                results = await es_service.search_messages_text(
                    index_name=kb_id,
                    query_text=query,
                    min_score=min_score,
                    max_results=max_results
                )
            elif search_method == "hybrid":
                # TODO: Implement hybrid search (need to generate query embedding)
                logger.warning("Hybrid search not yet implemented, falling back to text")
                results = await es_service.search_messages_text(
                    index_name=kb_id,
                    query_text=query,
                    min_score=min_score,
                    max_results=max_results
                )
            else:
                logger.error(f"Unknown search method: {search_method}")
                return []
            
            # Format results for AG-UI
            formatted_results = []
            for result in results:
                doc = result.get("doc", {})
                formatted_results.append({
                    "id": doc.get("message_id"),
                    "score": result.get("score", 0.0),
                    "text": doc.get("message_text", ""),
                    "date": doc.get("message_date"),
                    "sender": doc.get("sender_name"),
                    "metadata": {
                        "user_id": doc.get("user_id"),
                        "thread_id": doc.get("thread_id"),
                        "role": doc.get("role")
                    }
                })
            
            logger.info(f"✅ Found {len(formatted_results)} results in KB {kb_id}")
            return formatted_results
            
        except Exception as e:
            logger.warning(f"⚠️  Could not search KB {kb_id}: {e}")
            logger.debug(f"   Elasticsearch might not be available or index doesn't exist")
            return []
    
    async def delete_knowledge_base(
        self,
        kb_id: str,
        user_id: int
    ) -> bool:
        """
        Delete knowledge base.
        
        Args:
            kb_id: KB index name
            user_id: User ID (for permission check)
        
        Returns:
            True if deleted successfully
        """
        try:
            # Check if user owns this KB
            if kb_id != f"tg-kb-user-{user_id}":
                logger.warning(f"User {user_id} attempted to delete KB they don't own: {kb_id}")
                return False
            
            es_service = await self._get_es_service()
            if not es_service:
                return False
            
            success = await es_service.delete_index(kb_id)
            
            if success:
                logger.info(f"🗑️  Deleted KB {kb_id} for user {user_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Error deleting KB {kb_id}: {e}")
            return False


# Singleton instance
_catalog_adapter: Optional[CatalogAdapter] = None


def get_catalog_adapter() -> CatalogAdapter:
    """Get or create CatalogAdapter singleton."""
    global _catalog_adapter
    if _catalog_adapter is None:
        _catalog_adapter = CatalogAdapter()
        logger.info("✅ CatalogAdapter singleton created")
    return _catalog_adapter

