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

    def _initialize_embedding_model(self):
        """Initialize the embedding model"""
        if self.model is None:
            logger.info("Initializing embedding model...")
            try:
                self.model = SentenceTransformer(
                    Config.EMBEDDING_MODEL,
                    device='cpu',
                    cache_folder=str(Config.MODEL_CACHE)
                )
            except Exception as e:
                logger.error(f"Failed to initialize model: {str(e)}")
                raise

    def _load_embedding_cache(self):
        """Load cached embeddings from disk"""
        cache_dir = Config.EMBEDDING_STORAGE
        cache_dir.mkdir(parents=True, exist_ok=True)
        if not self.embedding_cache:
            logger.info("Loading embedding cache...")
            for file in cache_dir.glob("*.json"):
                try:
                    with open(file, 'r') as f:
                        data = json.load(f)
                        if data.get('model') == Config.EMBEDDING_MODEL:
                            self.embedding_cache[file.stem] = np.array(data['embedding'])
                except Exception as e:
                    logger.error(f"Error loading {file.name}: {str(e)}")

    def create_index(self, chunks: list):
        """Index documents with their embeddings and keywords"""
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

    def _generate_embeddings(self, chunks: list) -> list:
        """Generate embeddings with caching"""
        embeddings_map = {}
        texts_to_embed = []
        chunks_to_embed_map = {}

        for chunk in chunks:
            chunk_id = chunk["metadata"]["chunk_id"]
            if chunk_id in self.embedding_cache:
                embeddings_map[chunk_id] = self.embedding_cache[chunk_id]
            else:
                texts_to_embed.append(chunk["text"])
                chunks_to_embed_map[chunk["text"]] = chunk_id

        if texts_to_embed:
            logger.info(f"Generating embeddings for {len(texts_to_embed)} new chunks...")
            new_embeddings = self.model.encode(
                texts_to_embed,
                convert_to_numpy=True,
                batch_size=32,
                show_progress_bar=True
            )
            
            for text, embedding in zip(texts_to_embed, new_embeddings):
                chunk_id = chunks_to_embed_map[text]
                self._save_embedding(chunk_id, embedding)
                embeddings_map[chunk_id] = embedding
        
        return [embeddings_map[chunk["metadata"]["chunk_id"]] for chunk in chunks]


    def _save_embedding(self, chunk_id: str, embedding: np.ndarray):
        """Save embedding to cache"""
        try:
            cache_path = Config.EMBEDDING_STORAGE / f"{chunk_id}.json"
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
            query_embed = self.model.encode(query)
            keywords = self.keyword_db._extract_keywords(query).split()
            return self.qdrant.hybrid_search(
                query_embed, 
                keywords, 
                self.keyword_db
            )
        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            return []
            
    def get_context_for_rag(self, query: str) -> list[dict]:
        """Retrieve relevant document chunks for RAG context."""
        if not query or not query.strip():
            return []
        try:
            query_embedding = self.model.encode(query)
            search_results = self.qdrant.vector_search(
                query_embedding=query_embedding,
                limit=Config.CONTEXT_CHUNKS_FOR_RAG
            )
            return [result.payload for result in search_results]
        except Exception as e:
            logger.error(f"RAG context retrieval failed: {str(e)}")
            return []

    def close(self):
        """Cleanup resources"""
        try:
            self.keyword_db.close()
            logger.info("Resources released successfully")
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
