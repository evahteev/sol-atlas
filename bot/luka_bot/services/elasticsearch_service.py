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

from luka_bot.core.config import settings


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
            # NotFoundError is expected for new/empty KBs
            error_name = type(e).__name__
            if "NotFoundError" in error_name or "index_not_found" in str(e):
                logger.debug(f"📊 Index {index_name} doesn't exist yet, returning empty list")
                return []
            
            logger.error(f"❌ Failed to get recent messages from {index_name}: {e}")
            return []
    
    async def get_group_weekly_stats(self, index_name: str) -> Dict[str, Any]:
        """
        Get weekly statistics for a group.
        
        Calculates statistics for the last 7 days including:
        - Number of unique users who posted
        - Total messages sent
        - Top most active members
        
        Args:
            index_name: Group KB index name
            
        Returns:
            Dict with:
            - unique_users_week: Number of unique users who posted last week
            - total_messages_week: Total messages last week
            - top_users_week: List of dicts with user_id, sender_name, message_count
        """
        from datetime import datetime, timedelta
        
        try:
            # Calculate date 7 days ago
            week_ago = datetime.utcnow() - timedelta(days=7)
            week_ago_str = week_ago.isoformat()
            
            # Query: Get unique users count, total messages, and top users for last week
            response = await self.client.search(
                index=index_name,
                body={
                    "size": 0,
                    "query": {
                        "range": {
                            "message_date": {
                                "gte": week_ago_str
                            }
                        }
                    },
                    "aggs": {
                        "unique_users": {
                            "cardinality": {
                                "field": "user_id.keyword"
                            }
                        },
                        "top_users": {
                            "terms": {
                                "field": "user_id.keyword",
                                "size": 10,
                                "order": {"_count": "desc"}
                            },
                            "aggs": {
                                "sender_name": {
                                    "terms": {
                                        "field": "sender_name.keyword",
                                        "size": 1
                                    }
                                }
                            }
                        }
                    }
                }
            )
            
            # Extract results
            unique_users = response['aggregations']['unique_users']['value']
            total_messages_week = response['hits']['total']['value']
            
            # Extract top users with names
            top_users_buckets = response['aggregations']['top_users']['buckets']
            top_users = []
            for bucket in top_users_buckets:
                user_id = bucket['key']
                message_count = bucket['doc_count']
                # Get sender name from nested aggregation
                sender_name = "Unknown"
                if bucket['sender_name']['buckets']:
                    sender_name = bucket['sender_name']['buckets'][0]['key']
                top_users.append({
                    "user_id": user_id,
                    "sender_name": sender_name,
                    "message_count": message_count
                })
            
            logger.debug(f"📊 Weekly stats for {index_name}: {unique_users} users, {total_messages_week} messages")
            
            return {
                "unique_users_week": unique_users,
                "total_messages_week": total_messages_week,
                "top_users_week": top_users
            }
            
        except Exception as e:
            # NotFoundError is expected for new/empty indices - not an error
            error_name = type(e).__name__
            if "NotFoundError" in error_name or "index_not_found" in str(e):
                logger.debug(f"📊 Index {index_name} not yet created (empty KB)")
            else:
                logger.error(f"❌ Failed to get weekly stats for {index_name}: {e}")
            
            return {
                "unique_users_week": 0,
                "total_messages_week": 0,
                "top_users_week": []
            }
    
    async def find_unanswered_questions_llm(
        self,
        index_name: str,
        lookback_days: int = 7,
        max_messages: int = 50,
        language: str = "en"
    ) -> List[Dict[str, Any]]:
        """
        Use LLM to analyze recent messages and identify unanswered questions.
        
        This is more robust than pattern matching as it understands context,
        conversation flow, and whether questions were actually answered.
        
        Args:
            index_name: Index name to analyze
            lookback_days: How many days back to analyze (default: 7)
            max_messages: Maximum number of messages to analyze
            language: Language for LLM prompt
            
        Returns:
            List of unanswered question dicts with:
            - question: The question text
            - sender: Who asked the question  
            - date: When it was asked
            - reason: Why it's considered unanswered (brief explanation)
        """
        try:
            from datetime import datetime, timedelta
            
            # Calculate date threshold
            date_threshold = datetime.utcnow() - timedelta(days=lookback_days)
            
            # Query for recent messages within date range
            response = await self.client.search(
                index=index_name,
                body={
                    "size": max_messages,
                    "sort": [{"message_date": {"order": "desc"}}],
                    "query": {
                        "range": {
                            "message_date": {
                                "gte": date_threshold.isoformat()
                            }
                        }
                    },
                    "_source": ["sender_name", "message_text", "message_date", "user_id"]
                }
            )
            
            messages = []
            for hit in response['hits']['hits']:
                source = hit['_source']
                messages.append({
                    "sender": source.get("sender_name", "Unknown"),
                    "text": source.get("message_text", ""),
                    "date": source.get("message_date", ""),
                    "user_id": source.get("user_id", "")
                })
            
            if not messages:
                logger.debug(f"❓ No messages found in {index_name} for unanswered questions analysis")
                return []
            
            # Reverse to chronological order (oldest to newest)
            messages.reverse()
            
            # Format messages for LLM analysis
            messages_text = []
            for i, msg in enumerate(messages, 1):
                date_str = msg['date'][:16] if msg['date'] else "Unknown date"
                messages_text.append(f"{i}. [{msg['sender']}, {date_str}]: {msg['text']}")
            
            conversation_text = "\n".join(messages_text)
            
            # Create LLM prompt based on language
            lang_instruction = "русском языке" if language == "ru" else "English"
            
            prompt = f"""Analyze this conversation from the last {lookback_days} days and identify questions that remain UNANSWERED.

IMPORTANT RULES:
- Only flag questions that were NOT answered by others in subsequent messages
- Look at the conversation flow, not just question marks
- A question is answered if someone provided information addressing it
- Skip questions that were answered with "I don't know" or similar definitive responses

Conversation:
{conversation_text}

TASKS:
1. Identify questions that were asked but NOT adequately answered
2. For each unanswered question, provide: the question text, who asked it, and why it's unanswered

Return your analysis in the following JSON format:
{{
  "unanswered_questions": [
    {{
      "question": "the question text",
      "sender": "sender name",
      "date": "approximate date",
      "reason": "why it's unanswered (max 50 words)"
    }}
  ]
}}

Return ONLY valid JSON. If no unanswered questions, return {{"unanswered_questions": []}}

Language: Respond in {lang_instruction}."""
            
            # Use LLM to analyze
            from luka_bot.services.llm_model_factory import create_llm_model_with_fallback
            from pydantic_ai import Agent
            from pydantic_ai.settings import ModelSettings
            
            # Create model with low temperature for consistent analysis
            model_settings = ModelSettings(
                temperature=0.2,
                max_tokens=800
            )
            
            model = await create_llm_model_with_fallback(
                context=f"unanswered_questions_{index_name}",
                model_settings=model_settings
            )
            
            agent = Agent(
                model=model,
                system_prompt=f"You are a conversation analysis expert. You identify unanswered questions in conversations. Be precise and only flag questions that truly lack answers. Respond in {language}."
            )
            
            logger.info(f"🤖 Analyzing {len(messages)} messages for unanswered questions using LLM...")
            result = await agent.run(prompt)
            
            # Parse LLM response
            import json
            try:
                # Extract JSON from LLM response
                response_text = result.output.strip()
                
                # Try to find JSON in the response (might be wrapped in markdown or text)
                if "```json" in response_text:
                    json_start = response_text.find("```json") + 7
                    json_end = response_text.find("```", json_start)
                    response_text = response_text[json_start:json_end].strip()
                elif "```" in response_text:
                    json_start = response_text.find("```") + 3
                    json_end = response_text.find("```", json_start)
                    response_text = response_text[json_start:json_end].strip()
                
                parsed = json.loads(response_text)
                unanswered = parsed.get("unanswered_questions", [])
                
                logger.info(f"✅ LLM identified {len(unanswered)} unanswered questions")
                return unanswered[:5]  # Return top 5
                
            except json.JSONDecodeError as e:
                logger.warning(f"⚠️ Failed to parse LLM response for unanswered questions: {e}")
                logger.debug(f"LLM response: {response_text}")
                return []
            
        except Exception as e:
            logger.warning(f"⚠️ Error finding unanswered questions with LLM: {e}")
            return []
    
    async def get_advanced_kb_stats(
        self,
        index_name: str,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        include_timeline: bool = False,
        include_hourly_activity: bool = False,
        include_hashtags: bool = False,
        include_media_breakdown: bool = False,
        include_user_engagement: bool = False,
        top_n: int = 5
    ) -> Dict[str, Any]:
        """
        Get advanced statistics using Elasticsearch aggregations.
        
        Args:
            index_name: Index to analyze
            date_from: Start date (None = all time)
            date_to: End date (None = now)
            include_timeline: Include daily message histogram
            include_hourly_activity: Include hourly distribution
            include_hashtags: Include top hashtags
            include_media_breakdown: Include media type distribution
            include_user_engagement: Include user engagement levels
            top_n: Number of top items to return
            
        Returns:
            Dict with requested statistics
        """
        try:
            from datetime import datetime
            
            # Build base query with date range filter
            query_dict = {}
            if date_from or date_to:
                query_dict = {
                    "range": {
                        "message_date": {}
                    }
                }
                if date_from:
                    query_dict["range"]["message_date"]["gte"] = date_from.isoformat()
                if date_to:
                    query_dict["range"]["message_date"]["lte"] = date_to.isoformat()
            else:
                query_dict = {"match_all": {}}
            
            # Build aggregations based on flags
            aggs = {}
            
            # Basic: Always include these
            aggs["unique_users"] = {
                "cardinality": {"field": "user_id.keyword"}
            }

            aggs["top_users"] = {
                "terms": {
                    "field": "user_id.keyword",
                    "size": top_n,
                    "order": {"_count": "desc"}
                },
                "aggs": {
                    "sender_name": {
                        "terms": {
                            "field": "sender_name.keyword",
                            "size": 1
                        }
                    }
                }
            }
            
            # Optional: Timeline (daily histogram)
            if include_timeline:
                aggs["timeline"] = {
                    "date_histogram": {
                        "field": "message_date",
                        "calendar_interval": "day",
                        "format": "yyyy-MM-dd",
                        "min_doc_count": 0
                    }
                }
            
            # Optional: Hourly activity pattern
            if include_hourly_activity:
                aggs["hourly_activity"] = {
                    "terms": {
                        "script": {
                            "source": "doc['message_date'].value.getHour()",
                            "lang": "painless"
                        },
                        "size": 24,
                        "order": {"_key": "asc"}
                    }
                }
            
            # Optional: Top hashtags
            if include_hashtags:
                aggs["top_hashtags"] = {
                    "terms": {
                        "field": "hashtags",
                        "size": top_n,
                        "order": {"_count": "desc"}
                    }
                }
            
            # Optional: Media type breakdown
            if include_media_breakdown:
                aggs["media_types"] = {
                    "terms": {
                        "field": "media_type",
                        "size": 10,
                        "missing": "text"  # Count text-only as "text"
                    }
                }
            
            # Optional: User engagement distribution
            if include_user_engagement:
                aggs["user_message_distribution"] = {
                    "terms": {
                        "field": "user_id.keyword",
                        "size": 1000  # Large enough to get all users
                    }
                }
            
            # Execute aggregation query
            response = await self.client.search(
                index=index_name,
                body={
                    "size": 0,  # We only want aggregations
                    "query": query_dict,
                    "aggs": aggs
                }
            )
            
            # Parse results
            results = {
                "total_messages": response['hits']['total']['value'],
                "unique_users": response['aggregations']['unique_users']['value']
            }
            
            # Parse top users
            top_users_buckets = response['aggregations']['top_users']['buckets']
            results["top_users"] = []
            for bucket in top_users_buckets:
                user_id = bucket['key']
                message_count = bucket['doc_count']
                sender_name = "Unknown"
                if bucket['sender_name']['buckets']:
                    sender_name = bucket['sender_name']['buckets'][0]['key']
                results["top_users"].append({
                    "user_id": user_id,
                    "sender_name": sender_name,
                    "message_count": message_count
                })
            
            # Parse timeline if requested
            if include_timeline:
                timeline_buckets = response['aggregations']['timeline']['buckets']
                results["timeline"] = [
                    {
                        "date": bucket['key_as_string'],
                        "message_count": bucket['doc_count']
                    }
                    for bucket in timeline_buckets
                ]
            
            # Parse hourly activity if requested
            if include_hourly_activity:
                hourly_buckets = response['aggregations']['hourly_activity']['buckets']
                results["hourly_activity"] = [
                    {
                        "hour": int(bucket['key']),
                        "message_count": bucket['doc_count']
                    }
                    for bucket in sorted(hourly_buckets, key=lambda x: x['key'])
                ]
            
            # Parse hashtags if requested
            if include_hashtags:
                hashtag_buckets = response['aggregations']['top_hashtags']['buckets']
                results["top_hashtags"] = [
                    {
                        "hashtag": bucket['key'],
                        "count": bucket['doc_count']
                    }
                    for bucket in hashtag_buckets
                ]
            
            # Parse media breakdown if requested
            if include_media_breakdown:
                media_buckets = response['aggregations']['media_types']['buckets']
                results["media_types"] = [
                    {
                        "type": bucket['key'],
                        "count": bucket['doc_count']
                    }
                    for bucket in media_buckets
                ]
            
            # Parse user engagement if requested
            if include_user_engagement:
                # Count users in each engagement level
                user_buckets = response['aggregations']['user_message_distribution']['buckets']
                engagement_levels = {
                    "one_time": 0,      # 1 message
                    "occasional": 0,    # 2-5 messages
                    "regular": 0,       # 6-20 messages
                    "active": 0,        # 21-50 messages
                    "very_active": 0    # 50+ messages
                }
                
                for bucket in user_buckets:
                    msg_count = bucket['doc_count']
                    if msg_count == 1:
                        engagement_levels["one_time"] += 1
                    elif 2 <= msg_count <= 5:
                        engagement_levels["occasional"] += 1
                    elif 6 <= msg_count <= 20:
                        engagement_levels["regular"] += 1
                    elif 21 <= msg_count <= 50:
                        engagement_levels["active"] += 1
                    else:
                        engagement_levels["very_active"] += 1
                
                results["user_engagement"] = engagement_levels
            
            logger.info(f"📊 Advanced stats for {index_name}: {results['total_messages']} messages, {results['unique_users']} users")
            return results
            
        except Exception as e:
            logger.error(f"❌ Error getting advanced stats for {index_name}: {e}")
            return {
                "total_messages": 0,
                "unique_users": 0,
                "top_users": [],
                "error": str(e)
            }
    
    async def delete_index(self, index_name: str) -> bool:
        """
        Delete an index and all its documents.
        
        Args:
            index_name: Index name to delete
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if index exists first
            exists = await self.client.indices.exists(index=index_name)
            
            if not exists:
                logger.warning(f"⚠️  Index {index_name} doesn't exist, nothing to delete")
                return True  # Return True as the desired state is achieved
            
            # Delete the index
            await self.client.indices.delete(index=index_name)
            logger.info(f"🗑️  Successfully deleted index: {index_name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to delete index {index_name}: {e}")
            return False
    
    async def get_unique_users_in_index(self, index_name: str) -> List[str]:
        """
        Get list of unique user IDs who have messages in an index.
        
        Args:
            index_name: ES index name
            
        Returns:
            List of user ID strings
        """
        try:
            if not self.client:
                await self._ensure_client()
            
            # Check if index exists
            exists = await self.client.indices.exists(index=index_name)
            if not exists:
                logger.warning(f"⚠️  Index {index_name} doesn't exist")
                return []
            
            # Use aggregation to get unique user_ids
            result = await self.client.search(
                index=index_name,
                body={
                    "size": 0,
                    "aggs": {
                        "unique_users": {
                            "terms": {
                                "field": "user_id.keyword",
                                "size": 10000  # Max users per group
                            }
                        }
                    }
                }
            )
            
            buckets = result["aggregations"]["unique_users"]["buckets"]
            user_ids = [bucket["key"] for bucket in buckets]
            
            logger.debug(f"Found {len(user_ids)} unique users in {index_name}")
            return user_ids
            
        except Exception as e:
            logger.error(f"❌ Error getting unique users from {index_name}: {e}")
            return []
    
    def get_metrics(self) -> Dict[str, int]:
        """Get service metrics."""
        return self.metrics.copy()
    
    async def close(self):
        """Close Elasticsearch client."""
        await self.client.close()
        logger.info("🔌 Elasticsearch client closed")


# Singleton instance
_elasticsearch_service: Optional[LukaElasticsearchService] = None


async def get_elasticsearch_service() -> LukaElasticsearchService:
    """
    Get or create Elasticsearch service singleton.
    
    Returns:
        LukaElasticsearchService instance
    """
    global _elasticsearch_service
    
    if _elasticsearch_service is None:
        _elasticsearch_service = LukaElasticsearchService()
        await _elasticsearch_service._ensure_templates()
        logger.info("✅ Elasticsearch service singleton created")
    
    return _elasticsearch_service
