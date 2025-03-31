from vector_store import VectorStore
from pdf_processor import PDFProcessor
from config import Config
import logging
import os
import sys
from PyPDF2 import PdfReader

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("semantic_search.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def verify_pdf_content(pdf_path: str) -> bool:
    """Verify a PDF contains extractable text"""
    try:
        print(f"\n🔬 Testing PDF: {os.path.basename(pdf_path)}")
        with open(pdf_path, 'rb') as f:
            # Quick check for text layers
            if b'/Font' not in f.read(1000):
                print("⚠️ Warning: No fonts detected - may be scanned PDF")
                return False
        
        reader = PdfReader(pdf_path)
        for i, page in enumerate(reader.pages[:3]):  # Check first 3 pages
            text = page.extract_text()
            if text and len(text.strip()) > 100:
                print(f"✅ Page {i+1} contains text ({len(text)} chars)")
                return True
        print("❌ No sufficient text found in first 3 pages")
        return False
    except Exception as e:
        print(f"🔥 Verification failed: {str(e)}")
        return False

def initialize_system():
    """Initialize all components with validation"""
    try:
        # Create required directories
        os.makedirs(Config.VECTOR_DB_DIR, exist_ok=True)
        os.makedirs(Config.MODEL_CACHE, exist_ok=True)
        
        return VectorStore()
    except Exception as e:
        logger.error(f"Initialization failed: {str(e)}")
        raise

def process_pdfs(vector_store):
    """Process PDFs with progress tracking"""
    try:
        # Force reprocess all files
        logger.info("Processing PDF files...")
        chunks = PDFProcessor.process_pdfs_in_directory()
        if not chunks:
            logger.error("No chunks created from PDFs")
            return False
            
        logger.info(f"Created {len(chunks)} chunks from PDFs")
        vector_store.create_index(chunks)
        return True
    except Exception as e:
        logger.error(f"PDF processing failed: {str(e)}")
        return False

def search_loop(vector_store):
    """Interactive search interface"""
    logger.info("Entering search loop. Type 'exit' to quit.")
    
    while True:
        try:
            query = input("\nEnter your search query (or 'exit' to quit): ").strip()
            
            if query.lower() == 'exit':
                break
                
            if not query:
                print("Please enter a search query")
                continue
                
            start_time = time.time()
            results = vector_store.hybrid_search(query)
            search_time = time.time() - start_time
            
            print(f"\nSearch completed in {search_time:.2f} seconds")
            print(f"Found {len(results)} results:")
            
            for i, res in enumerate(results, 1):
                print(f"\n{i}. [PDF: {res['payload']['pdf_name']} | Page: {res['payload']['page']}]")
                print(res["payload"]["text"][:500] + ("..." if len(res["payload"]["text"]) > 500 else ""))
                
        except KeyboardInterrupt:
            print("\nOperation cancelled by user")
            break
        except Exception as e:
            print(f"\nError during search: {str(e)}")
            continue

def main():
    try:
        # Verify system requirements
        if not verify_pdfs():
            sys.exit(1)
            
        # Initialize
        vector_store = initialize_system()
        
        # Process PDFs
        if not process_pdfs(vector_store):
            sys.exit(1)
            
        # Start search interface
        search_loop(vector_store)
        
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        sys.exit(1)
    finally:
        try:
            vector_store.close()
        except:
            pass

if __name__ == "__main__":
    import time
    time.sleep(1)  # Ensure logs are initialized
    main()