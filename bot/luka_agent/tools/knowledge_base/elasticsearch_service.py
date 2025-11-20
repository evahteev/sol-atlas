"""
Elasticsearch service for Luka bot knowledge base.

This service provides:
- Index template management (user KB, group KB, topics)
- Message indexing (immediate, no embeddings)
- Multiple search methods (text, vector, hybrid)
- Async embedding generation support
- RAG-ready search results

Architecture:
- Phase 1: Immediate text indexing (no embeddings)
- Phase 2: Async embedding generation via Camunda
- Phase 3: Full RAG with hybrid search
"""
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from elasticsearch import AsyncElasticsearch
from elasticsearch.helpers import async_bulk
from loguru import logger

from luka_agent.core.config import settings


class LukaElasticsearchService:
    """
    Manages Elasticsearch operations for Luka KB.
    
    Features:
    - Template management for user/group/topic indices
    - Immediate message indexing (text only)
    - Multiple search methods (text, vector, hybrid)
    - Metrics tracking
    """
    
    def __init__(self):
        """Initialize Elasticsearch client and ensure templates exist."""
        self.client = AsyncElasticsearch(
            settings.ELASTICSEARCH_URL,
            request_timeout=settings.ELASTICSEARCH_TIMEOUT,
            verify_certs=settings.ELASTICSEARCH_VERIFY_CERTS
        )
        self.metrics = {
            "messages_indexed": 0,
            "messages_failed": 0,
            "searches_performed": 0,
            "search_errors": 0
        }
        logger.info(f"🔧 Elasticsearch service initialized: {settings.ELASTICSEARCH_URL}")
    
    async def list_indices(self, pattern: str) -> List[Dict[str, Any]]:
        """
        List all indices matching a pattern.
        
        Args:
            pattern: Index pattern with wildcards (e.g., "tg-kb-user-*")
        
        Returns:
            List of dicts with index info: {name, doc_count, size_bytes}
        """
        try:
            # Get indices matching pattern
            indices_response = await self.client.cat.indices(
                index=pattern,
                format="json",
                h="index,docs.count,store.size"
            )
            
            if not indices_response:
                return []
            
            # Format response
            result = []
            for idx in indices_response:
                result.append({
                    "name": idx.get("index", ""),
                    "doc_count": int(idx.get("docs.count", 0)),
                    "size_bytes": idx.get("store.size", "0b")
                })
            
            logger.debug(f"Found {len(result)} indices matching pattern: {pattern}")
            return result
            
        except Exception as e:
            logger.warning(f"Error listing indices with pattern {pattern}: {e}")
            return []
    
    async def _ensure_templates(self):
        """
        Create index templates for Luka KB indices.
        
        Templates:
        - tg-kb-user-* : User knowledge base messages
        - tg-kb-group-*: Group knowledge base messages
        - tg-topics-*  : Topic clusters (user and group)
        """
        # User KB template
        user_kb_template = {
            "index_patterns": [f"{settings.ELASTICSEARCH_USER_KB_PREFIX}*"],
            "priority": 200,
            "template": {
                "settings": {
                    "number_of_shards": 1,
                    "number_of_replicas": 0,
                    "analysis": {
                        "analyzer": {
                            "default": {
                                "type": "standard"
                            }
                        }
                    }
                },
                "mappings": {
                    "properties": {
                        "message_id": {"type": "keyword"},
                        "user_id": {"type": "keyword"},
                        "thread_id": {"type": "keyword"},
                        "role": {"type": "keyword"},  # user|assistant|system
                        "message_text": {"type": "text", "analyzer": "standard"},
                        "message_date": {"type": "date"},
                        "sender_name": {
                            "type": "text",
                            "fields": {
                                "keyword": {"type": "keyword"}
                            }
                        },
                        "sender_username": {"type": "keyword"},
                        "reply_to_message_id": {"type": "keyword"},
                        "mentions": {"type": "keyword"},
                        "hashtags": {"type": "keyword"},
                        "urls": {"type": "keyword"},
                        "media_type": {"type": "keyword"},
                        "insert_ts": {"type": "date"},
                        
                        # Enhanced thread context
                        "thread_type": {"type": "keyword"},
                        "thread_owner_id": {"type": "keyword"},
                        "thread_name": {"type": "text"},
                        "agent_name": {"type": "keyword"},
                        "agent_description": {"type": "text"},
                        "llm_provider": {"type": "keyword"},
                        "model_name": {"type": "keyword"},
                        "system_prompt": {"type": "text"},
                        "enabled_tools": {"type": "keyword"},
                        "disabled_tools": {"type": "keyword"},
                        "knowledge_bases": {"type": "keyword"},
                        "thread_language": {"type": "keyword"},
                        "conversation_summary": {"type": "text"},
                        "message_count": {"type": "integer"},
                        "process_instance_id": {"type": "keyword"},
                        "active_workflows": {"type": "keyword"},
                        
                        # Vector field (populated async)
                        "message_vector": {
                            "type": "dense_vector",
                            "dims": settings.EMBEDDING_DIMENSIONS,
                            "index": True,
                            "similarity": "cosine"
                        },
                        "vector_generated": {"type": "boolean"}
                    }
                }
            }
        }
        
        # Group KB template (same structure as user KB)
        group_kb_template = {
            "index_patterns": [f"{settings.ELASTICSEARCH_GROUP_KB_PREFIX}*"],
            "priority": 200,
            "template": {
                "settings": {
                    "number_of_shards": 1,
                    "number_of_replicas": 0,
                    "analysis": {
                        "analyzer": {
                            "default": {
                                "type": "standard"
                            }
                        }
                    }
                },
                "mappings": {
                    "properties": {
                        "message_id": {"type": "keyword"},
                        "group_id": {"type": "keyword"},
                        "user_id": {"type": "keyword"},
                        "role": {"type": "keyword"},  # user|assistant|system
                        "thread_id": {"type": "keyword"},  # Topic ID for filtering
                        "message_text": {"type": "text", "analyzer": "standard"},
                        "message_date": {"type": "date"},
                        "sender_name": {
                            "type": "text",
                            "fields": {
                                "keyword": {"type": "keyword"}
                            }
                        },
                        "sender_username": {"type": "keyword"},
                        "reply_to_message_id": {"type": "keyword"},
                        "mentions": {"type": "keyword"},
                        "hashtags": {"type": "keyword"},
                        "urls": {"type": "keyword"},
                        "media_type": {"type": "keyword"},
                        "insert_ts": {"type": "date"},
                        
                        # Enhanced thread context
                        "thread_type": {"type": "keyword"},
                        "thread_owner_id": {"type": "keyword"},
                        "thread_name": {"type": "text"},
                        "agent_name": {"type": "keyword"},
                        "agent_description": {"type": "text"},
                        "llm_provider": {"type": "keyword"},
                        "model_name": {"type": "keyword"},
                        "system_prompt": {"type": "text"},
                        "enabled_tools": {"type": "keyword"},
                        "disabled_tools": {"type": "keyword"},
                        "knowledge_bases": {"type": "keyword"},
                        "thread_language": {"type": "keyword"},
                        "conversation_summary": {"type": "text"},
                        "message_count": {"type": "integer"},
                        "process_instance_id": {"type": "keyword"},
                        "active_workflows": {"type": "keyword"},
                        
                        "message_vector": {
                            "type": "dense_vector",
                            "dims": settings.EMBEDDING_DIMENSIONS,
                            "index": True,
                            "similarity": "cosine"
                        },
                        "vector_generated": {"type": "boolean"}
                    }
                }
            }
        }
        
        # Topics template
        topics_template = {
            "index_patterns": [f"{settings.ELASTICSEARCH_TOPICS_PREFIX}*"],
            "priority": 200,
            "template": {
                "settings": {
                    "number_of_shards": 1,
                    "number_of_replicas": 0
                },
                "mappings": {
                    "properties": {
                        "topic_id": {"type": "keyword"},
                        "topic_name": {"type": "text"},
                        "topic_vector": {
                            "type": "dense_vector",
                            "dims": settings.EMBEDDING_DIMENSIONS,
                            "index": True,
                            "similarity": "cosine"
                        },
                        "message_count": {"type": "integer"},
                        "first_message_date": {"type": "date"},
                        "last_message_date": {"type": "date"},
                        "participants": {"type": "keyword"},
                        "keywords": {"type": "keyword"},
                        "summary": {"type": "text"}
                    }
                }
            }
        }
        
        try:
            await self.client.indices.put_index_template(
                name="luka-user-kb-template",
                body=user_kb_template
            )
            await self.client.indices.put_index_template(
                name="luka-group-kb-template",
                body=group_kb_template
            )
            await self.client.indices.put_index_template(
                name="luka-topics-template",
                body=topics_template
            )
            logger.info("✅ Elasticsearch templates created/updated")
        except Exception as e:
            logger.error(f"❌ Failed to create templates: {e}")
            raise
    
    async def _log_new_index(self, index_name: str):
        """
        Log that a new index will be auto-created.
        
        Indices are auto-created by Elasticsearch on first document insert
        using the matching template based on prefix:
        - tg-kb-user-* → luka-user-kb-template  
        - tg-kb-group-* → luka-group-kb-template
        
        This method just provides visibility for debugging.
        """
        logger.debug(f"📊 Index {index_name} will be auto-created on first insert (using template)")
    
    async def index_message_immediate(
        self,
        index_name: str,
        message_data: Dict,
        document_id: str
    ) -> bool:
        """
        Index a single message immediately (no embedding).
        
        Args:
            index_name: e.g., "tg-kb-user-922705" or "tg-kb-group-123456"
            message_data: Message fields (text, date, sender, etc.)
            document_id: Pre-generated document ID for ES and Camunda correlation
        
        Returns:
            True if successful
        """
        try:
            doc = {
                **message_data,
                "insert_ts": datetime.utcnow().isoformat(),
                "vector_generated": False  # Mark for async processing
            }
            
            await self.client.index(
                index=index_name,
                id=document_id,
                document=doc,
                refresh=settings.INDEX_REFRESH_IMMEDIATE
            )
            
            self.metrics["messages_indexed"] += 1
            logger.debug(f"📝 Indexed message {document_id} to {index_name}")
            return True
            
        except Exception as e:
            self.metrics["messages_failed"] += 1
            logger.error(f"❌ Failed to index message {document_id}: {e}")
            return False
    
    async def bulk_index_messages(
        self,
        index_name: str,
        messages: List[Dict]
    ) -> Tuple[int, int]:
        """
        Bulk index messages (no embeddings).
        
        Args:
            index_name: Target index name
            messages: List of message dicts with 'message_id' key
        
        Returns:
            (success_count, error_count)
        """
        actions = []
        for msg in messages:
            actions.append({
                "_index": index_name,
                "_id": msg["message_id"],
                "_source": {
                    **msg,
                    "insert_ts": datetime.utcnow().isoformat(),
                    "vector_generated": False
                }
            })
        
        try:
            success, errors = await async_bulk(
                self.client,
                actions,
                refresh=settings.INDEX_REFRESH_IMMEDIATE
            )
            
            self.metrics["messages_indexed"] += success
            self.metrics["messages_failed"] += len(errors)
            
            logger.info(f"📚 Bulk indexed {success} messages to {index_name}, {len(errors)} errors")
            return success, len(errors)
            
        except Exception as e:
            logger.error(f"❌ Bulk indexing failed: {e}")
            return 0, len(messages)
    
    async def search_messages_text(
        self,
        index_name: str,
        query_text: str,
        min_score: float = None,
        max_results: int = None
    ) -> List[Dict]:
        """
        Full-text search with fuzzy matching (BM25).
        
        Use case: Fast keyword search
        Response time: ~50-100ms
        
        Args:
            index_name: Index to search
            query_text: Search query
            min_score: Minimum relevance score (default from settings)
            max_results: Max results to return (default from settings)
        
        Returns:
            List of {'score': float, 'doc': dict} results
        """
        min_score = min_score or settings.DEFAULT_MIN_SCORE
        max_results = max_results or settings.DEFAULT_MAX_RESULTS
        
        body = {
            "query": {
                "match": {
                    "message_text": {
                        "query": query_text,
                        "fuzziness": "AUTO"
                    }
                }
            },
            "_source": {
                "excludes": ["message_vector"]
            },
            "size": max_results,
            "min_score": min_score
        }
        
        try:
            response = await self.client.search(index=index_name, body=body)
            
            self.metrics["searches_performed"] += 1
            
            total_found = response["hits"]["total"]["value"]
            hits = response["hits"]["hits"]
            
            logger.info(
                f"🔍 Text search: found {total_found} total, returning {len(hits)} results"
            )
            
            return [
                {'score': hit['_score'], 'doc': hit['_source']}
                for hit in hits
            ]
            
        except Exception as e:
            # NotFoundError is expected for new/empty KBs - not an error, just no results yet
            error_name = type(e).__name__
            if "NotFoundError" in error_name or "index_not_found" in str(e):
                logger.debug(f"📊 Index {index_name} doesn't exist yet (new KB), returning empty results")
                return []
            
            # Real error (connection issues, query syntax, etc.)
            self.metrics["search_errors"] += 1
            logger.error(f"❌ Text search failed: {e}")
            return []
    
    async def search_messages_vector(
        self,
        index_name: str,
        query_vector: List[float],
        min_score: Optional[float] = None,
        max_results: int = None
    ) -> List[Dict]:
        """
        Vector similarity search (k-NN with cosine similarity).
        
        Use case: Semantic similarity search
        Response time: ~100-200ms
        Requires: Embeddings generated
        
        Args:
            index_name: Index to search
            query_vector: Embedding vector of the query
            min_score: Minimum similarity score
            max_results: Max results to return
        
        Returns:
            List of {'score': float, 'doc': dict} results
        """
        # Check if index exists before searching
        exists = await self.client.indices.exists(index=index_name)
        if not exists:
            logger.debug(f"📊 Index {index_name} doesn't exist yet, returning empty results")
            return []
        
        max_results = max_results or settings.DEFAULT_MAX_RESULTS
        
        body = {
            "knn": {
                "field": "message_vector",
                "query_vector": query_vector,
                "k": max_results,
                "num_candidates": 10000
            },
            "_source": {
                "excludes": ["message_vector"]
            }
        }
        
        try:
            response = await self.client.search(index=index_name, body=body)
            
            self.metrics["searches_performed"] += 1
            
            total_found = response["hits"]["total"]["value"]
            hits = response["hits"]["hits"]
            
            logger.info(
                f"🔍 Vector search: found {total_found} total, returning {len(hits)} results"
            )
            
            results = [
                {"doc": hit["_source"], "score": hit["_score"]}
                for hit in hits
                if not min_score or hit["_score"] > min_score
            ]
            
            return results
            
        except Exception as e:
            # NotFoundError is expected for new/empty KBs
            error_name = type(e).__name__
            if "NotFoundError" in error_name or "index_not_found" in str(e):
                logger.debug(f"📊 Index {index_name} doesn't exist yet, returning empty results")
                return []
            
            self.metrics["search_errors"] += 1
            logger.error(f"❌ Vector search failed: {e}")
            return []
    
    async def search_messages_hybrid(
        self,
        index_name: str,
        query_text: str,
        query_vector: List[float],
        min_score: Optional[float] = None,
        max_results: int = None
    ) -> List[Dict]:
        """
        Hybrid search: BM25 + vector similarity (BEST for production RAG).
        
        Use case: Production RAG queries
        Response time: ~150-250ms
        Formula: 0.5 * cosine_similarity + 0.5 * log(1 + bm25_score)
        
        Args:
            index_name: Index to search
            query_text: Text query for BM25
            query_vector: Embedding vector for similarity
            min_score: Minimum combined score
            max_results: Max results to return
        
        Returns:
            List of {'score': float, 'doc': dict} results
        """
        # Check if index exists before searching
        exists = await self.client.indices.exists(index=index_name)
        if not exists:
            logger.debug(f"📊 Index {index_name} doesn't exist yet, returning empty results")
            return []
        
        max_results = max_results or settings.DEFAULT_MAX_RESULTS
        
        body = {
            "query": {
                "script_score": {
                    "query": {
                        "match": {
                            "message_text": {
                                "query": query_text,
                                "fuzziness": "AUTO"
                            }
                        }
                    },
                    "script": {
                        "source": """
                            double cosine = cosineSimilarity(params.query_vector, 'message_vector');
                            double bm25 = Math.log(1 + _score);
                            return 0.5 * cosine + 0.5 * bm25;
                        """,
                        "params": {
                            "query_vector": query_vector
                        }
                    }
                }
            },
            "_source": {
                "excludes": ["message_vector"]
            },
            "size": max_results
        }
        
        try:
            response = await self.client.search(index=index_name, body=body)
            
            self.metrics["searches_performed"] += 1
            
            total_found = response["hits"]["total"]["value"]
            hits = response["hits"]["hits"]
            
            logger.info(
                f"🔍 Hybrid search: found {total_found} total, returning {len(hits)} results"
            )
            
            results = [
                {"doc": hit["_source"], "score": hit["_score"]}
                for hit in hits
                if not min_score or hit["_score"] > min_score
            ]
            
            return results
            
        except Exception as e:
            # NotFoundError is expected for new/empty KBs
            error_name = type(e).__name__
            if "NotFoundError" in error_name or "index_not_found" in str(e):
                logger.debug(f"📊 Index {index_name} doesn't exist yet, returning empty results")
                return []
            
            self.metrics["search_errors"] += 1
            logger.error(f"❌ Hybrid search failed: {e}")
            return []
    
    async def search_topics_vector(
        self,
        index_name: str,
        query_vector: List[float],
        min_score: Optional[float] = None,
        max_results: int = None
    ) -> List[Dict]:
        """
        Search topic clusters by vector similarity.
        
        Use case: High-level conversation discovery
        Index: tg-topics-*
        
        Args:
            index_name: Topics index name
            query_vector: Embedding vector of the query
            min_score: Minimum similarity score
            max_results: Max results to return
        
        Returns:
            List of {'score': float, 'doc': dict} results
        """
        max_results = max_results or settings.DEFAULT_MAX_RESULTS
        
        body = {
            "knn": {
                "field": "topic_vector",
                "query_vector": query_vector,
                "k": max_results,
                "num_candidates": 10000
            },
            "_source": {
                "excludes": ["topic_vector"]
            }
        }
        
        try:
            response = await self.client.search(index=index_name, body=body)
            
            self.metrics["searches_performed"] += 1
            
            total_found = response["hits"]["total"]["value"]
            hits = response["hits"]["hits"]
            
            logger.info(
                f"🔍 Topic search: found {total_found} total, returning {len(hits)} results"
            )
            
            results = [
                {"doc": hit["_source"], "score": hit["_score"]}
                for hit in hits
                if not min_score or hit["_score"] > min_score
            ]
            
            return results
            
        except Exception as e:
            self.metrics["search_errors"] += 1
            logger.error(f"❌ Topic search failed: {e}")
            return []
    
    async def get_unprocessed_messages(
        self,
        index_name: str,
        batch_size: int = 100
    ) -> List[Dict]:
        """
        Get messages that need vector generation (for async worker).
        
        Args:
            index_name: Index to query
            batch_size: Max messages to return
        
        Returns:
            List of message dicts with '_id' field
        """
        try:
            response = await self.client.search(
                index=index_name,
                body={
                    "query": {
                        "term": {"vector_generated": False}
                    },
                    "size": batch_size
                }
            )
            
            return [
                {**hit["_source"], "_id": hit["_id"]}
                for hit in response["hits"]["hits"]
            ]
            
        except Exception as e:
            logger.error(f"❌ Failed to get unprocessed messages: {e}")
            return []
    
    async def get_index_stats(self, index_name: str) -> Dict[str, Any]:
        """
        Get statistics for an index.
        
        Args:
            index_name: Index name
        
        Returns:
            Dict with count, size_bytes, etc.
        """
        try:
            # Get document count
            count_response = await self.client.count(index=index_name)
            message_count = count_response['count']
            
            # Get index size
            stats_response = await self.client.indices.stats(index=index_name)
            size_bytes = stats_response['_all']['total']['store']['size_in_bytes']
            
            return {
                "message_count": message_count,
                "size_bytes": size_bytes,
                "size_mb": size_bytes / (1024 * 1024)
            }
            
        except Exception as e:
            # NotFoundError is expected for new/empty indices - not an error
            error_name = type(e).__name__
            if "NotFoundError" in error_name or "index_not_found" in str(e):
                logger.debug(f"📊 Index {index_name} not yet created (empty KB)")
            else:
                logger.error(f"❌ Failed to get index stats for {index_name}: {e}")
            
            return {
                "message_count": 0,
                "size_bytes": 0,
                "size_mb": 0.0
            }
    
    async def get_recent_messages(
        self,
        index_name: str,
        limit: int = 10
    ) -> List[dict]:
        """
        Get the most recent messages from an index.
        
        Used for building group context in user-group threads.
        
        Args:
            index_name: Index name (e.g., "tg-kb-group-1001234567")
            limit: Number of recent messages to fetch
            
        Returns:
            List of message dicts with sender_name, message_text, message_date
        """
        try:
            # Query for most recent messages, sorted by message_date desc
            response = await self.client.search(
                index=index_name,
                body={
                    "size": limit,
                    "sort": [
                        {"message_date": {"order": "desc"}}
                    ],
                    "query": {
                        "match_all": {}
                    },
                    "_source": ["sender_name", "message_text", "message_date", "user_id"]
                }
            )
            
            messages = []
            for hit in response['hits']['hits']:
                source = hit['_source']
                messages.append({
                    "sender_name": source.get("sender_name", "Unknown"),
                    "message_text": source.get("message_text", ""),
                    "message_date": source.get("message_date", ""),
                    "user_id": source.get("user_id", "")
                })
            
            # Reverse to get chronological order (oldest to newest)
            messages.reverse()
            
            logger.debug(f"📚 Fetched {len(messages)} recent messages from {index_name}")
            return messages
            
        except Exception as e:
            # NotFoundError is expected for new/empty indices
            error_name = type(e).__name__
            if "NotFoundError" in error_name or "index_not_found" in str(e):
                logger.debug(f"📊 Index {index_name} doesn't exist yet, returning empty list")
                return []
                
            logger.error(f"❌ Failed to get recent messages from {index_name}: {e}")
            return []


def get_elasticsearch_service() -> LukaElasticsearchService:
    """Factory function to get Elasticsearch service instance."""
    return LukaElasticsearchService()
