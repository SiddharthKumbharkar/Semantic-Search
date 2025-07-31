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

    def hybrid_search(self, query: str, accessible_docs: list = None) -> list:
        """Perform optimized hybrid search combining semantic and keyword search"""
        try:
            # Optimize: Use smaller limits for faster response
            semantic_limit = 10  # Reduced from 20
            keyword_limit = 5    # Reduced from 20
            
            # Get semantic search results first (usually more relevant)
            semantic_results = self.qdrant.search(query, limit=semantic_limit)
            
            # Only do keyword search if semantic results are insufficient
            if len(semantic_results) < 5:
                keywords = self._extract_keywords_from_query(query)
                keyword_results = self.keyword_db.search(keywords, limit=keyword_limit)
                
                # Combine results with semantic results having higher priority
                combined_results = self._combine_results(semantic_results, keyword_results)
            else:
                combined_results = semantic_results
            
            # Filter by accessible documents if specified
            if accessible_docs is not None:
                combined_results = self._filter_by_accessible_docs(combined_results, accessible_docs)
            
            # Return top results (reduced from 10 to 8 for faster response)
            return combined_results[:8]
            
        except Exception as e:
            logger.error(f"Hybrid search failed: {str(e)}")
            return []

    def _extract_keywords_from_query(self, query: str) -> list:
        """Extract important keywords from the query for keyword search"""
        try:
            import nltk
            from nltk.tokenize import word_tokenize
            from collections import Counter
            
            # Download required NLTK data
            nltk.download('punkt', quiet=True)
            
            # Tokenize and filter words
            words = word_tokenize(query.lower())
            # Keep only alphanumeric words with length > 2
            keywords = [word for word in words if word.isalnum() and len(word) > 2]
            
            # Get the most common keywords (reduced from 5 to 3 for speed)
            keyword_counts = Counter(keywords)
            top_keywords = [word for word, count in keyword_counts.most_common(3)]
            
            return top_keywords
            
        except Exception as e:
            logger.error(f"Error extracting keywords: {e}")
            # Fallback: return the query words as keywords
            return query.lower().split()

    def _filter_by_accessible_docs(self, results: list, accessible_docs: list) -> list:
        """Filter results to only include accessible documents"""
        if not accessible_docs:
            return results
        
        filtered_results = []
        for result in results:
            # Extract document name from result
            doc_name = None
            if 'payload' in result and 'pdf_name' in result['payload']:
                doc_name = result['payload']['pdf_name']
            elif 'metadata' in result and 'source' in result['metadata']:
                doc_name = result['metadata']['source']
            
            if doc_name and doc_name in accessible_docs:
                filtered_results.append(result)
        
        return filtered_results

    def _combine_results(self, semantic_results: list, keyword_results: list) -> list:
        """Combine and rank semantic and keyword search results"""
        try:
            # Create a combined results list
            combined = []
            
            # Add semantic results with higher weight
            for result in semantic_results:
                if isinstance(result, dict):
                    result['score'] = result.get('score', 0.8)  # Default high score for semantic
                    combined.append(result)
            
            # Add keyword results with lower weight
            for result in keyword_results:
                if isinstance(result, dict):
                    result['score'] = result.get('score', 0.6)  # Default lower score for keyword
                    combined.append(result)
            
            # Remove duplicates based on content
            seen = set()
            unique_results = []
            for result in combined:
                # Create a unique key based on content
                content = result.get('text', '') or result.get('payload', {}).get('text', '')
                key = hash(content)
                
                if key not in seen:
                    seen.add(key)
                    unique_results.append(result)
            
            # Sort by score (highest first)
            unique_results.sort(key=lambda x: x.get('score', 0), reverse=True)
            
            return unique_results
            
        except Exception as e:
            logger.error(f"Error combining results: {str(e)}")
            # Return semantic results as fallback
            return semantic_results if semantic_results else keyword_results
            
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
