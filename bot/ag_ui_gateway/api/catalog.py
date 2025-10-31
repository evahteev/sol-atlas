"""
Catalog API Endpoints

Handles knowledge base catalog listing, details, and management.
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Optional, List
from loguru import logger

from ag_ui_gateway.auth.permissions import get_current_user
from ag_ui_gateway.adapters.catalog_adapter import get_catalog_adapter

router = APIRouter()


@router.get("/catalog")
async def list_catalog(
    visibility: Optional[str] = Query("all", description="Filter by visibility (user, group, all)"),
    include_stats: bool = Query(False, description="Include document counts and sizes"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user_data: Optional[dict] = Depends(get_current_user)
):
    """
    List knowledge bases in catalog with filters.
    
    Args:
        visibility: Filter by KB type (user, group, all)
        include_stats: Whether to include document counts and sizes
        limit: Maximum results per page
        offset: Pagination offset
        user_data: Optional authenticated user data
    
    Returns:
        Paginated list of knowledge bases
    """
    try:
        user_id = user_data.get("user_id") if user_data else None
        
        logger.info(f"📚 Catalog request: visibility={visibility}, user={user_id}")
        
        catalog_adapter = get_catalog_adapter()
        
        # List KBs based on visibility filter
        if visibility == "user" and user_id:
            kbs = await catalog_adapter.list_knowledge_bases(
                user_id=user_id,
                include_stats=include_stats
            )
        elif visibility == "group":
            # List all group KBs (for now - TODO: filter by user's groups)
            kbs = await catalog_adapter.list_knowledge_bases(
                include_stats=include_stats
            )
            kbs = [kb for kb in kbs if kb.get("type") == "group"]
        else:
            # List all accessible KBs
            if user_id:
                kbs = await catalog_adapter.list_knowledge_bases(
                    user_id=user_id,
                    include_stats=include_stats
                )
            else:
                # Guest users - only public group KBs
                kbs = await catalog_adapter.list_knowledge_bases(
                    include_stats=include_stats
                )
                kbs = [kb for kb in kbs if kb.get("type") == "group"]
        
        # Apply pagination
        total = len(kbs)
        paginated = kbs[offset:offset + limit]
        
        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "results": paginated
        }
        
    except Exception as e:
        logger.error(f"❌ Error listing catalog: {e}")
        raise HTTPException(status_code=500, detail="Failed to list catalog")


@router.get("/kb/{kb_id}")
async def get_kb_details(
    kb_id: str,
    user_data: Optional[dict] = Depends(get_current_user)
):
    """
    Get knowledge base details.
    
    Args:
        kb_id: Knowledge base ID (index name)
        user_data: Optional authenticated user data
    
    Returns:
        KB metadata including stats
    """
    try:
        user_id = user_data.get("user_id") if user_data else None
        
        logger.info(f"📖 KB details request: {kb_id}, user={user_id}")
        
        catalog_adapter = get_catalog_adapter()
        kb = await catalog_adapter.get_knowledge_base(kb_id, user_id)
        
        if not kb:
            raise HTTPException(status_code=404, detail="Knowledge base not found or access denied")
        
        return kb
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting KB details: {e}")
        raise HTTPException(status_code=500, detail="Failed to get knowledge base details")


@router.delete("/kb/{kb_id}")
async def delete_kb(
    kb_id: str,
    user_data: dict = Depends(get_current_user)
):
    """
    Delete knowledge base (owner only).
    
    Args:
        kb_id: Knowledge base ID (index name)
        user_data: Authenticated user data
    
    Returns:
        Success message
    """
    try:
        user_id = user_data.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Authentication required")
        
        logger.info(f"🗑️  KB delete request: {kb_id}, user={user_id}")
        
        catalog_adapter = get_catalog_adapter()
        success = await catalog_adapter.delete_knowledge_base(kb_id, user_id)
        
        if not success:
            raise HTTPException(status_code=403, detail="Not authorized to delete this knowledge base")
        
        return {
            "message": "Knowledge base deleted successfully",
            "kb_id": kb_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error deleting KB: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete knowledge base")


@router.get("/kb/{kb_id}/search")
async def search_kb(
    kb_id: str,
    query: str = Query(..., description="Search query"),
    method: str = Query("text", description="Search method (text, vector, hybrid)"),
    max_results: int = Query(5, ge=1, le=20),
    user_data: Optional[dict] = Depends(get_current_user)
):
    """
    Search knowledge base.
    
    Args:
        kb_id: Knowledge base ID (index name)
        query: Search query text
        method: Search method (text, vector, hybrid)
        max_results: Maximum results to return
        user_data: Optional authenticated user data
    
    Returns:
        Search results
    """
    try:
        user_id = user_data.get("user_id") if user_data else None
        
        logger.info(f"🔍 KB search: {kb_id}, query='{query}', user={user_id}")
        
        catalog_adapter = get_catalog_adapter()
        results = await catalog_adapter.search_knowledge_base(
            kb_id=kb_id,
            query=query,
            user_id=user_id,
            max_results=max_results,
            search_method=method
        )
        
        return {
            "kb_id": kb_id,
            "query": query,
            "method": method,
            "results": results,
            "count": len(results)
        }
        
    except Exception as e:
        logger.error(f"❌ Error searching KB: {e}")
        raise HTTPException(status_code=500, detail="Failed to search knowledge base")
