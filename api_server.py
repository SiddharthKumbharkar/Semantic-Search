#!/usr/bin/env python3
"""
API Server for Semantic Search and Chatbot
Handles requests from the Next.js frontend
"""

import sys
import json
import logging
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
        return False

def handle_search_request(data):
    """Handle search requests"""
    try:
        query = data.get('query', '')
        if not query:
            return {"error": "No query provided"}
        
        results = vector_store.hybrid_search(query)
        return {"results": results}
    except Exception as e:
        logger.error(f"Search error: {e}")
        return {"error": str(e)}

def handle_chatbot_request(data):
    """Handle chatbot requests"""
    try:
        query = data.get('query', '')
        if not query:
            return {"error": "No query provided"}
        
        response, sources = chatbot.generate_response(query)
        return {
            "response": response,
            "sources": sources
        }
    except Exception as e:
        logger.error(f"Chatbot error: {e}")
        return {"error": str(e)}

def handle_process_request(data):
    """Handle document processing requests"""
    try:
        files = data.get('files', [])
        if not files:
            return {"error": "No files provided"}
        
        from pdf_processor import PDFProcessor
        processor = PDFProcessor()
        chunks = processor.process_pdfs()
        
        if chunks:
            vector_store.create_index(chunks)
            return {
                "success": True,
                "message": f"Successfully processed {len(chunks)} document chunks",
                "chunks_count": len(chunks)
            }
        else:
            return {
                "success": True,
                "message": "No new documents to process",
                "chunks_count": 0
            }
    except Exception as e:
        logger.error(f"Process error: {e}")
        return {"error": str(e)}

def main():
    """Main function to handle command line requests"""
    if len(sys.argv) < 3:
        print(json.dumps({"error": "Usage: python api_server.py <endpoint> <json_data>"}))
        sys.exit(1)
    
    endpoint = sys.argv[1]
    data_json = sys.argv[2]
    
    try:
        data = json.loads(data_json)
    except json.JSONDecodeError:
        print(json.dumps({"error": "Invalid JSON data"}))
        sys.exit(1)
    
    # Initialize backend
    if not initialize_backend():
        print(json.dumps({"error": "Failed to initialize backend"}))
        sys.exit(1)
    
    # Handle request based on endpoint
    if endpoint == 'search':
        result = handle_search_request(data)
    elif endpoint == 'chatbot':
        result = handle_chatbot_request(data)
    elif endpoint == 'process':
        result = handle_process_request(data)
    else:
        result = {"error": f"Unknown endpoint: {endpoint}"}
    
    # Output result as JSON
    print(json.dumps(result))

if __name__ == "__main__":
    main() 