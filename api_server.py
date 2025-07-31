#!/usr/bin/env python3
"""
API Server for Semantic Search and Chatbot
Handles requests from the Next.js frontend
"""

import sys
import json
import logging
import time
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Add the current directory to Python path
sys.path.append(str(Path(__file__).parent))

from config import Config
from vector_store import VectorStore
from chatbot import Chatbot

# Global instances
vector_store = None
chatbot = None

def initialize_backend():
    """Initialize the vector store and chatbot"""
    global vector_store, chatbot
    try:
        vector_store = VectorStore()
        chatbot = Chatbot(vector_store)
        logger.info("Backend initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize backend: {e}")
        # Don't fail completely, just log the error
        return False

def handle_search_request(data):
    """Handle search requests with performance monitoring"""
    start_time = time.time()
    try:
        query = data.get('query', '')
        userId = data.get('userId')
        accessLevel = data.get('accessLevel')
        
        if not query:
            return {"error": "No query provided"}
        
        if not vector_store:
            return {"error": "Search service not available"}
        
        # Get accessible documents for user
        accessible_docs = get_accessible_documents(userId, accessLevel)
        
        # Perform search
        results = vector_store.hybrid_search(query, accessible_docs)
        
        response_time = time.time() - start_time
        logger.info(f"Search completed in {response_time:.2f}s for query: '{query}'")
        
        return {"results": results}
    except Exception as e:
        logger.error(f"Search error: {e}")
        return {"error": str(e)}

def handle_chatbot_request(data):
    """Handle chatbot requests with performance monitoring"""
    start_time = time.time()
    try:
        query = data.get('query', '')
        userId = data.get('userId')
        accessLevel = data.get('accessLevel')
        
        if not query:
            return {"error": "No query provided"}
        
        if not chatbot:
            return {"error": "Chatbot service not available"}
        
        # Get accessible documents for user
        accessible_docs = get_accessible_documents(userId, accessLevel)
        
        # Generate response
        response, sources = chatbot.generate_response(query, accessible_docs)
        
        response_time = time.time() - start_time
        logger.info(f"Chatbot response generated in {response_time:.2f}s for query: '{query}'")
        
        return {
            "response": response,
            "sources": sources
        }
    except Exception as e:
        logger.error(f"Chatbot error: {e}")
        return {"error": str(e)}

def get_accessible_documents(userId, accessLevel=None):
    """Get list of accessible documents for user"""
    try:
        # This would typically query your database
        # For now, we'll return all documents if no access level specified
        if not accessLevel or accessLevel == 'all':
            return None  # Return None to search all documents
        
        # In a real implementation, you would:
        # 1. Query your database for documents the user has access to
        # 2. Filter by access level if specified
        # 3. Return list of accessible document names/paths
        
        logger.info(f"Getting accessible documents for user {userId} with access level {accessLevel}")
        
        # For now, return all documents since we don't have proper access control implemented
        # This should be replaced with actual database query
        from pathlib import Path
        data_dir = Path(__file__).parent / "data"
        accessible_docs = [f.name for f in data_dir.glob('*.pdf')]
        
        logger.info(f"Returning {len(accessible_docs)} accessible documents")
        
        return accessible_docs
        
    except Exception as e:
        logger.error(f"Error getting accessible documents: {e}")
        return None

def handle_process_request(data):
    """Handle document processing requests"""
    try:
        files = data.get('files', [])
        logger.info(f"Processing request received for files: {files}")
        
        if not files:
            return {"error": "No files provided"}
        
        # Check if files exist in data directory
        from pathlib import Path
        data_dir = Path(__file__).parent / "data"
        logger.info(f"Data directory: {data_dir}")
        logger.info(f"Files in data directory: {list(data_dir.glob('*.pdf'))}")
        
        from pdf_processor import PDFProcessor
        processor = PDFProcessor()
        chunks = processor.process_pdfs()
        
        logger.info(f"Processed {len(chunks)} chunks")
        
        if chunks and vector_store:
            vector_store.create_index(chunks)
            return {
                "success": True,
                "message": f"Successfully processed {len(chunks)} document chunks",
                "chunks_count": len(chunks)
            }
        elif chunks:
            return {
                "success": True,
                "message": f"Successfully processed {len(chunks)} document chunks (vector store not available)",
                "chunks_count": len(chunks)
            }
        else:
            return {
                "success": False,
                "message": "No documents found to process"
            }
    except Exception as e:
        logger.error(f"Process error: {e}")
        return {"error": str(e)}

def main():
    """Main function to handle command line requests"""
    if len(sys.argv) < 3:
        print("Usage: python api_server.py <endpoint> <data>")
        sys.exit(1)
    
    endpoint = sys.argv[1]
    data_json = sys.argv[2]
    
    try:
        data = json.loads(data_json)
    except json.JSONDecodeError:
        print("Invalid JSON data")
        sys.exit(1)
    
    # Initialize backend (don't fail if it doesn't work)
    initialize_backend()
    
    # Handle request based on endpoint
    if endpoint == "search":
        result = handle_search_request(data)
    elif endpoint == "chatbot":
        result = handle_chatbot_request(data)
    elif endpoint == "process":
        result = handle_process_request(data)
    else:
        result = {"error": f"Unknown endpoint: {endpoint}"}
    
    print(json.dumps(result))

if __name__ == "__main__":
    main() 