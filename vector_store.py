import os
import json
import time
import logging
import numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer
from qdrant_manager import QdrantManager
from keyword_db import KeywordDatabase
from config import Config

logger = logging.getLogger(__name__)

class VectorStore:
    def __init__(self):
        self.model = None
        self.qdrant = QdrantManager()
        self.keyword_db = KeywordDatabase()
        self.embedding_cache = {}
        self._initialize()

    def _initialize(self):
        """Initialize all components"""
        self._initialize_embedding_model()
        self._load_embedding_cache()
        self._initialize_qdrant_collection()

    def _initialize_embedding_model(self):
        """Initialize the embedding model"""
        logger.info("Initializing embedding model...")
        start_time = time.time()
        try:
            self.model = SentenceTransformer(
                Config.EMBEDDING_MODEL,
                device='cpu',
                cache_folder=Config.MODEL_CACHE
            )
            # Verify model works
            test_embed = self.model.encode(["test"])
            if test_embed.shape[1] != Config.EMBEDDING_DIM:
                raise ValueError(
                    f"Model dimension mismatch. Expected {Config.EMBEDDING_DIM}, "
                    f"got {test_embed.shape[1]}"
                )
            logger.info(f"Model initialized in {time.time()-start_time:.2f}s")
        except Exception as e:
            logger.error(f"Failed to initialize model: {str(e)}")
            raise

    def _load_embedding_cache(self):
        """Load cached embeddings from disk"""
        if not os.path.exists(Config.EMBEDDING_STORAGE):
            return

        logger.info("Loading embedding cache...")
        for file in Path(Config.EMBEDDING_STORAGE).glob("*.json"):
            try:
                with open(file, 'r') as f:
                    data = json.load(f)
                    if data.get('model') == Config.EMBEDDING_MODEL:
                        self.embedding_cache[file.stem] = np.array(data['embedding'])
            except Exception as e:
                logger.error(f"Error loading {file.name}: {str(e)}")

    def _initialize_qdrant_collection(self):
        """Ensure Qdrant collection is ready"""
        try:
            self.qdrant._ensure_collection(Config.EMBEDDING_DIM)
        except Exception as e:
            logger.error(f"Failed to initialize Qdrant collection: {str(e)}")
            raise

    def create_index(self, chunks: list):
        """Index documents with their embeddings"""
        if not chunks:
            logger.warning("No chunks provided for indexing")
            return

        try:
            embeddings = self._generate_embeddings(chunks)
            self.qdrant.upsert_vectors(chunks, embeddings)
            self.keyword_db.insert_chunks(chunks)
            logger.info(f"Indexed {len(chunks)} chunks successfully")
        except Exception as e:
            logger.error(f"Indexing failed: {str(e)}")
            raise

    def _generate_embeddings(self, chunks: list) -> np.ndarray:
        """Generate embeddings with caching"""
        embeddings = []
        texts_to_embed = []
        chunk_ids_to_embed = []

        # Separate cached and new chunks
        for chunk in chunks:
            chunk_id = chunk["metadata"]["chunk_id"]
            if chunk_id in self.embedding_cache:
                embeddings.append(self.embedding_cache[chunk_id])
            else:
                texts_to_embed.append(chunk["text"])
                chunk_ids_to_embed.append(chunk_id)

        # Process new chunks
        if texts_to_embed:
            logger.info(f"Generating embeddings for {len(texts_to_embed)} new chunks...")
            new_embeddings = self.model.encode(
                texts_to_embed,
                convert_to_numpy=True,
                batch_size=32,
                show_progress_bar=True
            )
            
            # Cache new embeddings
            for idx, chunk_id in enumerate(chunk_ids_to_embed):
                embedding = new_embeddings[idx]
                self._save_embedding(chunk_id, embedding)
                embeddings.append(embedding)

        return np.array(embeddings)

    def _save_embedding(self, chunk_id: str, embedding: np.ndarray):
        """Save embedding to cache"""
        try:
            cache_path = os.path.join(Config.EMBEDDING_STORAGE, f"{chunk_id}.json")
            with open(cache_path, 'w') as f:
                json.dump({
                    'embedding': embedding.tolist(),
                    'timestamp': time.time(),
                    'model': Config.EMBEDDING_MODEL
                }, f)
            self.embedding_cache[chunk_id] = embedding
        except Exception as e:
            logger.error(f"Failed to save embedding {chunk_id}: {str(e)}")

    def hybrid_search(self, query: str) -> list:
        """Perform hybrid search"""
        if not query or not query.strip():
            return []

        try:
            query_embed = self.model.encode([query], convert_to_numpy=True)[0]
            keywords = self.keyword_db._extract_keywords(query).split()
            return self.qdrant.hybrid_search(query_embed, keywords, self.keyword_db)
        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            return []

    def close(self):
        """Cleanup resources"""
        try:
            self.keyword_db.close()
            if hasattr(self.model, "close"):
                self.model.close()
            logger.info("Resources released successfully")
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")