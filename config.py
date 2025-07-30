from pathlib import Path

class Config:
    # --- Project Paths ---
    BASE_DIR = Path(__file__).parent
    PDF_DIRECTORY = BASE_DIR / "data"
    VECTOR_DB_DIR = BASE_DIR / "vector_db"
    MODEL_CACHE = BASE_DIR / "model_cache"
    EMBEDDING_STORAGE = VECTOR_DB_DIR / "embeddings"
    
    # --- File Definitions ---
    FILE_HASHES_JSON = "processed_files.json"
    KEYWORD_DB = str(VECTOR_DB_DIR / "keyword_search.db")
    KEYWORD_TABLE_NAME = "keyword_index" # Added this line

    # --- Qdrant Settings ---
    QDRANT_LOCATION = str(VECTOR_DB_DIR / "qdrant")
    QDRANT_COLLECTION = "document_chunks"

    # --- Embedding Model ---
    EMBEDDING_MODEL = "all-MiniLM-L6-v2"
    EMBEDDING_DIM = 384

    # --- Text Processing ---
    MIN_CHARS_PER_PAGE = 50
    MIN_SENTENCE_LENGTH = 5
    SENTENCES_PER_CHUNK = 5
    
    # --- Search Settings ---
    SIMILARITY_TOP_K = 10
    HYBRID_SEARCH_RATIO = 0.5

    # --- Chatbot (RAG) Settings ---
    OLLAMA_MODEL = "llama3.2:latest"
    CONTEXT_CHUNKS_FOR_RAG = 5 # Number of context chunks to feed the LLM
    RAG_PROMPT_TEMPLATE = """
    **Task:** You are an intelligent assistant. Use the following context from the user's documents to answer their question.

    **Context from Documents:**
    ---
    {context}
    ---

    **User's Question:**
    {question}

    **Instructions:**
    1.  Base your answer strictly on the provided context.
    2.  If the context does not contain the answer, state that you cannot find the information in the documents.
    3.  Do not make up information or use external knowledge.
    4.  Be concise and clear in your response.

    **Answer:**
    """
