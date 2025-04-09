from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from config import Config
import logging
import math

logger = logging.getLogger(__name__)

class QdrantManager:
    def __init__(self):
        self.client = QdrantClient(url="http://localhost:6333")
        self._ensure_collection(Config.EMBEDDING_DIM)

    def _ensure_collection(self, vector_size: int):
        """Create or validate collection exists"""
        try:
            print(f"Collection name: {Config.QDRANT_COLLECTION}")
            collection_info = self.client.get_collection(Config.QDRANT_COLLECTION)
            if (collection_info.config.params.vectors.size != vector_size or
                collection_info.config.params.vectors.distance != Distance.COSINE):
                raise ValueError("Collection configuration mismatch")
        except Exception:
            logger.info(f"Collection {Config.QDRANT_COLLECTION} not found or invalid. Creating...")
            self.client.recreate_collection(
                collection_name=Config.QDRANT_COLLECTION,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=Distance.COSINE
                )
            )

    def upsert_vectors(self, chunks: list, embeddings: list):
        """Store vectors in Qdrant"""
        print("Upserting vectors to Qdrant...")
        points = [
            PointStruct(
                id=chunk["metadata"]["chunk_id"],
                vector=embedding,
                payload={
                    "text": chunk["text"],
                    "pdf_name": chunk["metadata"]["pdf_name"],
                    "page": chunk["metadata"]["page"]
                }
            )
            for chunk, embedding in zip(chunks, embeddings)
        ]
        
        operation_info = self.client.upsert(
            collection_name=Config.QDRANT_COLLECTION,
            points=points,
            wait=True
        )
        logger.info(f"Upserted {len(points)} vectors")

    def vector_search(self, query_embedding: list, limit: int):
        """Perform vector search"""
        print("Performing vector search...")
        return self.client.search(
            collection_name=Config.QDRANT_COLLECTION,
            query_vector=query_embedding,
            limit=limit,
            with_payload=True
        )

    def hybrid_search(self, query_embedding: list, keywords: list, keyword_db):
        """Combine vector and keyword search results"""
        print("Performing hybrid search...")
        vector_limit = math.ceil(Config.SIMILARITY_TOP_K * Config.HYBRID_SEARCH_RATIO)
        keyword_limit = max(1, Config.SIMILARITY_TOP_K - vector_limit)
        
        vector_results = self.vector_search(query_embedding, vector_limit)
        keyword_results = keyword_db.search(keywords, keyword_limit)
        
        return self._fuse_results(vector_results, keyword_results)

    @staticmethod
    def _fuse_results(vector_results, keyword_results):
        """Combine and rank results"""
        print("Combine and rank results")
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
        print("Combined results",combined.values())
        return sorted(combined.values(), key=lambda x: x["score"], reverse=True)[:Config.SIMILARITY_TOP_K]