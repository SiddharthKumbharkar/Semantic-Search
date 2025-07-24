import sys
import time
import socket
import threading
import queue
import logging
from pathlib import Path
from PyPDF2 import PdfReader
from vector_store import VectorStore
from pdf_processor import PDFProcessor
from config import Config
import json
import asyncio
from drive_utils import get_drive_service, list_pdfs_in_folder, download_file
import subprocess
import os
from flask import Flask, request, jsonify
from flask_cors import CORS

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

def start_tcp_server(input_queue):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("127.0.0.1", 8080))
    server.listen(5)
    print("📡 TCP Server Listening on port 8080...")

    while True:
        conn, addr = server.accept()
        data = conn.recv(1024).decode("utf-8").strip()
        
        if data:
            print(f"Received query from Node.js: {data}")
            input_queue.put((data, conn))

async def search_loop(vector_store: VectorStore, input_queue: queue.Queue):
    print("\nDocument Search System")
    print("Waiting for queries from Node.js...\n")

    while True:
        try:
            if not input_queue.empty():
                query, conn = input_queue.get()
                print(f"Processing query: {query}")

                if query.lower() == "exit":
                    break

                start_time = time.time()
                results = vector_store.hybrid_search(query)
                duration = time.time() - start_time

                response = {
                    "query": query,
                    "time_taken": f"{duration:.2f}s",
                    "results": [
                        {
                            "pdf_name": res["payload"]["pdf_name"],
                            "page": res["payload"]["page"],
                            "text": res["payload"]["text"][:300] + ("..." if len(res["payload"]["text"]) > 300 else "")
                        }
                        for res in results
                    ]
                }

                json_response = json.dumps(response)
                conn.sendall(json_response.encode("utf-8"))
                conn.close()

        except Exception as e:
            print(f"\nError: {str(e)}")

def restart_backend():
    print("🧠 Restarting vector embedding process...")
    subprocess.Popen(["python", "main.py"])
    sys.exit(0)

def sync_pdfs_from_drive(known_file_ids):
    print("\n🔄 Checking Google Drive for new PDFs...")
    service = get_drive_service()
    drive_files = list_pdfs_in_folder(service)

    new_files_downloaded = False
    for file in drive_files:
        if file['id'] not in known_file_ids:
            downloaded = download_file(service, file['id'], file['name'])
            if downloaded:
                known_file_ids.add(file['id'])
                new_files_downloaded = True

    return new_files_downloaded

def start_drive_watcher(known_file_ids):
    def poll_loop():
        while True:
            try:
                if sync_pdfs_from_drive(known_file_ids):
                    print("🔁 New PDFs found. Restarting backend...")
                    restart_backend()
            except Exception as e:
                print(f"Drive watcher error: {e}")
            time.sleep(30)  # Poll every 30 seconds

    thread = threading.Thread(target=poll_loop, daemon=True)
    thread.start()

def create_flask_app(vector_store):
    app = Flask(__name__)
    CORS(app)

    @app.route('/generate', methods=['POST'])
    def generate():
        data = request.get_json()
        query = data.get('query')
        filter_val = data.get('filter')
        if not query:
            return jsonify({"error": "Missing query"}), 400
        try:
            results = vector_store.hybrid_search(query)
            formatted = [
                {
                    "pdf_name": res["payload"]["pdf_name"],
                    "page": res["payload"]["page"],
                    "text": res["payload"]["text"][:300] + ("..." if len(res["payload"]["text"]) > 300 else "")
                }
                for res in results
            ]
            return jsonify({"results": formatted})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    return app

async def main():
    input_queue = queue.Queue()
    logger = setup_logging()

    # Track downloaded files (in-memory)
    known_file_ids = set()

    # Start watching Google Drive in background
    start_drive_watcher(known_file_ids)

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

        # Start Flask API for semantic search
        app = create_flask_app(vector_store)
        print("Starting Flask API on port 5002...")
        app.run(host='0.0.0.0', port=5002)

        # Optionally, you can still start the TCP server and search loop if needed
        # threading.Thread(target=start_tcp_server, args=(input_queue,), daemon=True).start()
        # await search_loop(vector_store, input_queue)

    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        sys.exit(1)
    finally:
        if vector_store:
            vector_store.close()
        logger.info("System shutdown")

if __name__ == "__main__":
    asyncio.run(main())
