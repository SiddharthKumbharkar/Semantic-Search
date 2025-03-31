from sentence_transformers import SentenceTransformer
from qdrant_manager import QdrantManager
from keyword_db import KeywordDatabase
from config import Config
import numpy as np
import logging
import time

logger = logging.getLogger(__name__)

class VectorStore:
    def __init__(self):
        self.model = None
        self.qdrant = QdrantManager()
        self.keyword_db = KeywordDatabase()
        self._initialize_model()

    def _initialize_model(self):
        logger.info("Initializing embedding model...")
        start_time = time.time()
        try:
            self.model = SentenceTransformer(
                Config.EMBEDDING_MODEL,
                device='cpu',
                cache_folder=Config.MODEL_CACHE
            )
            # Verify embedding
            test_embed = self.model.encode(["test"])
            if test_embed.shape[1] != Config.EMBEDDING_DIM:
                raise ValueError(f"Unexpected embedding dimension: {test_embed.shape[1]}")
            logger.info(f"Model initialized in {time.time()-start_time:.2f}s")
        except Exception as e:
            logger.error(f"Model initialization failed: {str(e)}")
            raise

    def _generate_embeddings(self, chunks: list) -> np.ndarray:
        if not chunks:
            raise ValueError("No chunks provided for embedding")
            
        texts = [chunk["text"] for chunk in chunks]
        logger.info(f"Generating embeddings for {len(texts)} chunks...")
        
        try:
            embeddings = self.model.encode(
                texts,
                convert_to_numpy=True,
                batch_size=32,
                show_progress_bar=True
            )
            if embeddings.shape[0] != len(chunks):
                raise ValueError("Mismatch between chunks and embeddings count")
            return embeddings
        except Exception as e:
            logger.error(f"Embedding generation failed: {str(e)}")
            raise

    def create_index(self, chunks: list):
        if not chunks:
            logger.warning("No chunks provided for indexing")
            return
            
        try:
            # Generate embeddings
            embeddings = self._generate_embeddings(chunks)
            
            # Insert into Qdrant
            self.qdrant.upsert_vectors(chunks, embeddings)
            
            # Build keyword index
            self.keyword_db.insert_chunks(chunks)
            
            logger.info("Indexing completed successfully")
        except Exception as e:
            logger.error(f"Indexing failed: {str(e)}")
            raise

    def hybrid_search(self, query: str) -> list:
        if not query:
            return []
            
        try:
            # Generate query embedding
            query_embed = self.model.encode([query], convert_to_numpy=True)[0]
            
            # Extract keywords
            keywords = self.keyword_db._extract_keywords(query).split()
            if not keywords:
                logger.warning("No keywords extracted from query")
                return []
                
            # Perform search
            return self.qdrant.hybrid_search(query_embed, keywords, self.keyword_db)
        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            return []

    def close(self):
        self.keyword_db.close()
        if hasattr(self.model, 'close'):
            self.model.close()