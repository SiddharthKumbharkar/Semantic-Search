import os

class Config:
    # Directory Configuration
    PDF_DIRECTORY = os.path.abspath("pdfs")
    VECTOR_DB_DIR = os.path.abspath("vector_db")
    MODEL_CACHE = os.path.abspath("model_cache")
    
    # PDF Processing
    FILE_HASHES_JSON = "processed_files.json"
    MAX_PAGES_TO_PROCESS = None  # Process all pages
    MIN_SENTENCE_LENGTH = 3      # Minimum words per sentence
    SENTENCES_PER_CHUNK = 3      # Sentences per chunk
    MIN_CHARS_PER_PAGE = 100     # Skip pages with less text
    
    # Qdrant Configuration
    QDRANT_LOCATION = os.path.abspath("qdrant_db")
    QDRANT_COLLECTION = "pdf_chunks"
    HYBRID_SEARCH_RATIO = 0.7    # 70% vector, 30% keyword
    SIMILARITY_TOP_K = 5         # Number of results to return
    
    # Keyword Database
    KEYWORD_DB = os.path.abspath("keywords.db")
    KEYWORD_INDEX = "pdf_keywords"
    
    # Embedding Model
    EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DIM = 384          # Dimension for all-MiniLM-L6-v2