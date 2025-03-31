from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from config import Config
import math
import logging

logger = logging.getLogger(__name__)

class QdrantManager:
    def __init__(self):
        self.client = QdrantClient(
            path=Config.QDRANT_LOCATION,
            force_disable_check_same_thread=True
        )
        self.collection_initialized = False
        
    def _ensure_collection(self, vector_size: int):
        try:
            self.client.recreate_collection(
                collection_name=Config.QDRANT_COLLECTION,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=Distance.COSINE
                )
            )
            self.collection_initialized = True
            logger.info(f"Created Qdrant collection with vector size {vector_size}")
        except Exception as e:
            logger.error(f"Collection creation failed: {str(e)}")
            raise

    def upsert_vectors(self, chunks: list, embeddings: list):
        if not chunks or len(embeddings) == 0:
            raise ValueError("No data provided for upsert")
            
        self._ensure_collection(embeddings.shape[1])
        
        points = [
            PointStruct(
                id=chunk["metadata"]["chunk_id"],
                vector=embeddings[idx].tolist(),
                payload={
                    "text": chunk["text"],
                    "pdf_name": chunk["metadata"]["pdf_name"],
                    "page": chunk["metadata"]["page"]
                }
            )
            for idx, chunk in enumerate(chunks)
        ]
        
        operation_info = self.client.upsert(
            collection_name=Config.QDRANT_COLLECTION,
            points=points,
            wait=True
        )
        
        # Verify insertion
        collection_info = self.client.get_collection(Config.QDRANT_COLLECTION)
        logger.info(f"Upserted {len(points)} vectors (total: {collection_info.points_count})")
        
    def vector_search(self, query_embedding: list, limit: int):
        if not self.collection_initialized:
            raise RuntimeError("Collection not initialized")
            
        return self.client.search(
            collection_name=Config.QDRANT_COLLECTION,
            query_vector=query_embedding,
            limit=limit,
            with_payload=True
        )
    
    def hybrid_search(self, query_embedding: list, keywords: list, keyword_db):
        vector_limit = math.ceil(Config.SIMILARITY_TOP_K * Config.HYBRID_SEARCH_RATIO)
        keyword_limit = max(1, Config.SIMILARITY_TOP_K - vector_limit)
        
        vector_results = self.vector_search(query_embedding, vector_limit)
        keyword_results = keyword_db.search(keywords, keyword_limit)
        
        return self._fuse_results(vector_results, keyword_results)
    
    def _fuse_results(self, vector_results, keyword_results):
        combined = {}
        
        # Process vector results
        for rank, result in enumerate(vector_results, 1):
            combined[result.id] = {
                "score": 1.0 / rank,
                "payload": result.payload,
                "id": result.id
            }
        
        # Process keyword results
        for rank, row in enumerate(keyword_results, 1):
            chunk_id = row[0]
            if chunk_id in combined:
                combined[chunk_id]["score"] += 1.0 / rank
            else:
                combined[chunk_id] = {
                    "score": 1.0 / rank,
                    "payload": {
                        "text": row[1],
                        "pdf_name": row[2],
                        "page": row[3]
                    },
                    "id": chunk_id
                }
        
        return sorted(
            combined.values(),
            key=lambda x: x["score"],
            reverse=True
        )[:Config.SIMILARITY_TOP_K]