from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from config import Config
import logging
import math

logger = logging.getLogger(__name__)

class QdrantManager:
    def __init__(self):
        self.client = QdrantClient(
            path=str(Config.VECTOR_DB_DIR / "qdrant"),
            force_disable_check_same_thread=True
        )
        self._ensure_collection(Config.EMBEDDING_DIM)
        self._model = None  # Cache the embedding model

    def _ensure_collection(self, vector_size: int):
        """Create or validate collection exists."""
        try:
            self.client.get_collection(Config.QDRANT_COLLECTION)
        except Exception:
            self.client.recreate_collection(
                collection_name=Config.QDRANT_COLLECTION,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
            )

    def _get_embedding_model(self):
        """Get or create the embedding model (cached)"""
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(Config.EMBEDDING_MODEL)
        return self._model

    def upsert_vectors(self, chunks: list, embeddings: list):
        """Store vectors in Qdrant."""
        points = [
            PointStruct(
                id=chunk["metadata"]["chunk_id"],
                vector=embedding,
                payload={
                    "text": chunk["text"],
                    "pdf_name": chunk["metadata"]["pdf_name"],
                    "page": chunk["metadata"]["page"],
                }
            )
            for chunk, embedding in zip(chunks, embeddings)
        ]
        
        self.client.upsert(
            collection_name=Config.QDRANT_COLLECTION,
            points=points,
            wait=True
        )
        logger.info(f"Upserted {len(points)} vectors")

    def vector_search(self, query_embedding: list, limit: int):
        """Perform vector search without access level filtering."""
        return self.client.search(
            collection_name=Config.QDRANT_COLLECTION,
            query_vector=query_embedding,
            limit=limit,
            with_payload=True
        )

    def search(self, query: str, limit: int = 10):
        """Perform optimized semantic search using query text."""
        try:
            # Use cached model
            model = self._get_embedding_model()
            
            # Encode the query
            query_embedding = model.encode(query).tolist()
            
            # Perform vector search with optimized parameters
            results = self.client.search(
                collection_name=Config.QDRANT_COLLECTION,
                query_vector=query_embedding,
                limit=limit,
                with_payload=True,
                score_threshold=0.3  # Add score threshold for better quality
            )
            
            # Convert to expected format
            formatted_results = []
            for result in results:
                formatted_results.append({
                    'id': result.id,
                    'payload': result.payload,
                    'score': result.score
                })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Search error: {e}")
            return []

    def hybrid_search(self, query_embedding: list, keywords: list, keyword_db):
        """Combine vector and keyword search results."""
        vector_limit = math.ceil(Config.SIMILARITY_TOP_K * Config.HYBRID_SEARCH_RATIO)
        keyword_limit = max(1, Config.SIMILARITY_TOP_K - vector_limit)
        
        vector_results = self.vector_search(query_embedding, vector_limit)
        keyword_results = keyword_db.search(keywords, keyword_limit)
        
        return self._fuse_results(vector_results, keyword_results)

    @staticmethod
    def _fuse_results(vector_results, keyword_results):
        """Combine and rank results using Reciprocal Rank Fusion."""
        combined = {}
        
        # Process vector results
        for rank, result in enumerate(vector_results, 1):
            combined[result.id] = {
                "score": 1.0 / (rank + 60), # RRF constant k=60
                "payload": result.payload,
                "id": result.id
            }
        
        # Process keyword results
        for rank, row in enumerate(keyword_results, 1):
            chunk_id = row[0]
            if chunk_id in combined:
                combined[chunk_id]["score"] += 1.0 / (rank + 60)
            else:
                combined[chunk_id] = {
                    "score": 1.0 / (rank + 60),
                    "payload": {
                        "text": row[1],
                        "pdf_name": row[2],
                        "page": row[3],
                    },
                    "id": chunk_id
                }
        
        return sorted(combined.values(), key=lambda x: x["score"], reverse=True)[:Config.SIMILARITY_TOP_K]
