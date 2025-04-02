import sys
import time
import logging
from pathlib import Path
from PyPDF2 import PdfReader
from vector_store import VectorStore
from pdf_processor import PDFProcessor
from config import Config

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler("semantic_search.log", encoding="utf-8"),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def verify_pdf(pdf_path: Path) -> bool:
    """Check if PDF contains extractable text"""
    try:
        with pdf_path.open('rb') as f:
            if b"/Font" not in f.read(1000):
                print(f"Warning: {pdf_path.name} may be scanned PDF")
        
        reader = PdfReader(pdf_path)
        return any(page.extract_text() for page in reader.pages[:3])
    except Exception as e:
        print(f"Error verifying {pdf_path.name}: {str(e)}")
        return False

def check_pdfs() -> bool:
    """Verify PDF directory contains valid files"""
    print("\nChecking PDF directory...")
    valid = False
    
    if not Config.PDF_DIRECTORY.exists():
        print(f"✖ Directory not found: {Config.PDF_DIRECTORY}")
        return False
        
    pdf_files = list(Config.PDF_DIRECTORY.glob("*.pdf")) + list(Config.PDF_DIRECTORY.glob("*.PDF"))
    if not pdf_files:
        print(f"✖ No PDFs found in {Config.PDF_DIRECTORY}")
        return False
        
    for pdf_file in pdf_files:
        if verify_pdf(pdf_file):
            print(f"✔ Valid PDF found: {pdf_file.name}")
            valid = True
        else:
            print(f"✖ Invalid PDF (may be scanned): {pdf_file.name}")
    
    return valid

def search_loop(vector_store: VectorStore):
    """Interactive search interface"""
    print("\nDocument Search System")
    print("Type 'exit' to quit\n")
    
    while True:
        try:
            query = input("Search query: ").strip()
            if query.lower() == 'exit':
                break
            if not query:
                print("Please enter a query")
                continue
                
            start_time = time.time()
            results = vector_store.hybrid_search(query)
            duration = time.time() - start_time
            
            print(f"\nFound {len(results)} results in {duration:.2f}s:")
            for i, res in enumerate(results, 1):
                payload = res['payload']
                print(f"\n{i}. [{payload['pdf_name']} - Page {payload['page']}]")
                print(payload['text'][:300].replace('\n', ' ') + ("..." if len(payload['text']) > 300 else ""))
                
        except KeyboardInterrupt:
            print("\nSearch cancelled")
            break
        except Exception as e:
            print(f"\nError: {str(e)}")

def main():
    logger = setup_logging()
    vector_store = None
    
    try:
        if not check_pdfs():
            sys.exit("No valid PDFs found. Exiting.")
            
        logger.info("Initializing system...")
        vector_store = VectorStore()
        processor = PDFProcessor()
        
        logger.info("Processing documents...")
        chunks = processor.process_pdfs()
        if chunks:
            logger.info(f"Indexing {len(chunks)} chunks...")
            vector_store.create_index(chunks)
        else:
            logger.info("No new documents to process")
        
        search_loop(vector_store)
        
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        sys.exit(1)
    finally:
        if vector_store:
            vector_store.close()
        logger.info("System shutdown")

if __name__ == "__main__":
    time.sleep(1)  # Ensure logging is ready
    main()