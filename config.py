import os
from pathlib import Path

# config.py (correction)
class Config:
    # Correct base directory (parent of config.py's directory)
    BASE_DIR = Path(__file__).parent  # Changed from .parent.parent
    PDF_DIRECTORY = BASE_DIR / "pdfs"
    # ... rest of config remains the same ...
    
    # Qdrant configuration
    QDRANT_LOCATION = BASE_DIR / "qdrant_db"
    QDRANT_COLLECTION = "document_chunks"
    
    # Embedding model
    EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DIM = 384
    
    # Processing parameters
    MIN_CHARS_PER_PAGE = 100
    MIN_SENTENCE_LENGTH = 3
    SENTENCES_PER_CHUNK = 3
    SIMILARITY_TOP_K = 5
    HYBRID_SEARCH_RATIO = 0.7
    
    # Other directories
    EMBEDDING_STORAGE = BASE_DIR / "embedding_storage"
    MODEL_CACHE = BASE_DIR / "model_cache"
    VECTOR_DB_DIR = BASE_DIR / "vector_db"
    KEYWORD_DB = BASE_DIR / "keywords.db"
    KEYWORD_INDEX = "document_keywords"
    FILE_HASHES_JSON = "processed_files.json"
    
    # Create required directories
    for dir_path in [PDF_DIRECTORY, EMBEDDING_STORAGE, MODEL_CACHE, QDRANT_LOCATION, VECTOR_DB_DIR]:
        dir_path.mkdir(parents=True, exist_ok=True)