# import sys
# import time
# import socket
# import threading
# import queue
# import logging
# from pathlib import Path
# from PyPDF2 import PdfReader
# from vector_store import VectorStore
# from pdf_processor import PDFProcessor
# from config import Config
# import json
# import queue
# import asyncio
# import websockets

# async def send_response_to_websocket(response):
#     """Send search results back to the WebSocket client."""
#     uri = "ws://localhost:8765"  # Ensure port is correct
#     try:
#         print(f"Connecting to WebSocket server at {uri}")
#         async with websockets.connect(uri) as websocket:
#             json_data = json.dumps(response)
#             print(f"Sending data: {json_data}")
#             await websocket.send(json_data)
#             print("Data sent successfully")
#     except Exception as e:
#         print(f"Error sending response: {e}")


        
# def setup_logging():
#     logging.basicConfig(
#         level=logging.INFO,
#         format="%(asctime)s - %(levelname)s - %(message)s",
#         handlers=[
#             logging.FileHandler("semantic_search.log", encoding="utf-8"),
#             logging.StreamHandler()
#         ]
#     )
#     return logging.getLogger(__name__)

# def verify_pdf(pdf_path: Path) -> bool:
#     """Check if PDF contains extractable text"""
#     try:
#         with pdf_path.open('rb') as f:
#             if b"/Font" not in f.read(1000):
#                 print(f"Warning: {pdf_path.name} may be scanned PDF")
        
#         reader = PdfReader(pdf_path)
#         return any(page.extract_text() for page in reader.pages[:3])
#     except Exception as e:
#         print(f"Error verifying {pdf_path.name}: {str(e)}")
#         return False

# def check_pdfs() -> bool:
#     """Verify PDF directory contains valid files"""
#     print("\nChecking PDF directory...")
#     valid = False
    
#     if not Config.PDF_DIRECTORY.exists():
#         print(f"✖ Directory not found: {Config.PDF_DIRECTORY}")
#         return False
        
#     pdf_files = list(Config.PDF_DIRECTORY.glob("*.pdf")) + list(Config.PDF_DIRECTORY.glob("*.PDF"))
#     if not pdf_files:
#         print(f"✖ No PDFs found in {Config.PDF_DIRECTORY}")
#         return False
        
#     for pdf_file in pdf_files:
#         if verify_pdf(pdf_file):
#             print(f"✔ Valid PDF found: {pdf_file.name}")
#             valid = True
#         else:
#             print(f"✖ Invalid PDF (may be scanned): {pdf_file.name}")
    
#     return valid
# def start_tcp_server(input_queue):
#     """Start a TCP server to receive data from Node.js"""
#     server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#     server.bind(("127.0.0.1", 5000))
#     server.listen(5)
#     print("TCP Server Listening on port 5000...")

#     while True:
#         conn, addr = server.accept()
#         data = conn.recv(1024).decode("utf-8").strip()
#         if data:
#             print(f"Received from Node.js: {data}")
#             input_queue.put(data)
#         conn.close()

# # def search_loop(vector_store: VectorStore, input_queue: queue.Queue):
# #     """Interactive search interface with WebSocket input"""
# #     print("\nDocument Search System")
# #     print("Type 'exit' to quit\n")

# #     while True:
# #         try:
# #             if not input_queue.empty():
# #                 query = input_queue.get().strip()
# #                 print(f"Received query from Web: {query}")
# #             else:
# #                 query = input("Search query: ").strip()

# #             if query.lower() == "exit":
# #                 break
# #             if not query:
# #                 print("Please enter a query")
# #                 continue

# #             start_time = time.time()
# #             results = vector_store.hybrid_search(query)
# #             duration = time.time() - start_time

# #             print(f"\nFound {len(results)} results in {duration:.2f}s:")
# #             for i, res in enumerate(results, 1):
# #                 payload = res["payload"]
# #                 print(f"\n{i}. [{payload['pdf_name']} - Page {payload['page']}]")
# #                 print(payload["text"][:300].replace("\n", " ") + ("..." if len(payload["text"]) > 300 else ""))

# #         except KeyboardInterrupt:
# #             print("\nSearch cancelled")
# #             break
# #         except Exception as e:
# #             print(f"\nError: {str(e)}")

# # def search_loop(vector_store: VectorStore, input_queue: queue.Queue):
# #     """Interactive search interface with auto-enter"""
# #     print("\nDocument Search System")
# #     print("Type 'exit' to quit\n")

# #     while True:
# #         try:
# #             if not input_queue.empty():
# #                 query = input_queue.get().strip()
# #                 print(f"Received query from Web: {query}")

# #                 if query.lower() == "exit":
# #                     break
# #                 if not query:
# #                     print("Please enter a query")
# #                     continue

# #                 # Simulate pressing "Enter" automatically
# #                 sys.stdout.write("\n")
# #                 sys.stdout.flush()

# #                 start_time = time.time()
# #                 results = vector_store.hybrid_search(query)
# #                 duration = time.time() - start_time

# #                 print(f"\nFound {len(results)} results in {duration:.2f}s:")
# #                 for i, res in enumerate(results, 1):
# #                     payload = res["payload"]
# #                     print(f"\n{i}. [{payload['pdf_name']} - Page {payload['page']}]")
# #                     print(payload["text"][:300].replace("\n", " ") + ("..." if len(payload["text"]) > 300 else ""))
# #                 print("terminate")

# #         except KeyboardInterrupt:
# #             print("\nSearch cancelled")
# #             break
# #         except Exception as e:
# #             print(f"\nError: {str(e)}")
       
# # def search_loop(vector_store: VectorStore, input_queue: queue.Queue):
# #     """Interactive search interface with WebSocket output."""
# #     print("\nDocument Search System")
# #     print("Type 'exit' to quit\n")

# #     while True:
# #         try:
# #             if not input_queue.empty():
# #                 query = input_queue.get().strip()
# #                 print(f"Received query from Web: {query}")

# #                 if query.lower() == "exit":
# #                     break
# #                 if not query:
# #                     print("Please enter a query")
# #                     continue

# #                 # Perform search
# #                 start_time = time.time()
# #                 results = vector_store.hybrid_search(query)
# #                 duration = time.time() - start_time

# #                 # Format response
# #                 response = {
# #                     "query": query,
# #                     "time_taken": f"{duration:.2f}s",
# #                     "results": [
# #                         {
# #                             "pdf_name": res["payload"]["pdf_name"],
# #                             "page": res["payload"]["page"],
# #                             "text": res["payload"]["text"][:300] + ("..." if len(res["payload"]["text"]) > 300 else "")
# #                         }
# #                         for res in results
# #                     ]
# #                 }

# #                 # Send the response asynchronously
# #                 print(f"Sending response to WebSocket: {response}")
# #                 asyncio.create_task(send_response_to_websocket(response))


# #         except KeyboardInterrupt:
# #             print("\nSearch cancelled")
# #             break
# #         except Exception as e:
# #             print(f"\nError: {str(e)}")
   
# async def search_loop(vector_store: VectorStore, input_queue: queue.Queue):
#     """Interactive search interface with WebSocket output."""
#     print("\nDocument Search System")
#     print("Type 'exit' to quit\n")

#     while True:
#         try:
#             if not input_queue.empty():
#                 query = input_queue.get().strip()
#                 print(f"Received query from Web: {query}")

#                 if query.lower() == "exit":
#                     break
#                 if not query:
#                     print("Please enter a query")
#                     continue

#                 # Perform search
#                 start_time = time.time()
#                 results = vector_store.hybrid_search(query)
#                 duration = time.time() - start_time

#                 # Format response
#                 response = {
#                     "query": query,
#                     "time_taken": f"{duration:.2f}s",
#                     "results": [
#                         {
#                             "pdf_name": res["payload"]["pdf_name"],
#                             "page": res["payload"]["page"],
#                             "text": res["payload"]["text"][:300] + ("..." if len(res["payload"]["text"]) > 300 else "")
#                         }
#                         for res in results
#                     ]
#                 }

#                 # Send response
#                 print(f"Sending response to WebSocket: {response}")
#                 await send_response_to_websocket(response)  # Ensure it's awaited properly

#         except KeyboardInterrupt:
#             print("\nSearch cancelled")
#             break
#         except Exception as e:
#             print(f"\nError: {str(e)}")
              
# # def main():
# #     import threading
# #     input_queue = queue.Queue()

# #     logger = setup_logging()
# #     vector_store = None

# #     try:
# #         if not check_pdfs():
# #             sys.exit("No valid PDFs found. Exiting.")

# #         logger.info("Initializing system...")
# #         vector_store = VectorStore()
# #         processor = PDFProcessor()

# #         logger.info("Processing documents...")
# #         chunks = processor.process_pdfs()
# #         if chunks:
# #             logger.info(f"Indexing {len(chunks)} chunks...")
# #             vector_store.create_index(chunks)
# #         else:
# #             logger.info("No new documents to process")

# #         # Start the TCP server in a separate thread
# #         threading.Thread(target=start_tcp_server, args=(input_queue,), daemon=True).start()

# #         search_loop(vector_store, input_queue)

# #     except Exception as e:
# #         logger.error(f"Fatal error: {str(e)}")
# #         sys.exit(1)
# #     finally:
# #         if vector_store:
# #             vector_store.close()
# #         logger.info("System shutdown")

# async def main():
#     input_queue = queue.Queue()
#     logger = setup_logging()
#     vector_store = None

#     try:
#         if not check_pdfs():
#             sys.exit("No valid PDFs found. Exiting.")

#         logger.info("Initializing system...")
#         vector_store = VectorStore()
#         processor = PDFProcessor()

#         logger.info("Processing documents...")
#         chunks = processor.process_pdfs()
#         if chunks:
#             logger.info(f"Indexing {len(chunks)} chunks...")
#             vector_store.create_index(chunks)
#         else:
#             logger.info("No new documents to process")

#         # Start TCP server in separate thread
#         threading.Thread(target=start_tcp_server, args=(input_queue,), daemon=True).start()

#         # Run search loop asynchronously
#         await search_loop(vector_store, input_queue)

#     except Exception as e:
#         logger.error(f"Fatal error: {str(e)}")
#         sys.exit(1)
#     finally:
#         if vector_store:
#             vector_store.close()
#         logger.info("System shutdown")

# if __name__ == "__main__":
#     import asyncio
#     asyncio.run(main())  # Ensure the event loop is managed correctly

# if __name__ == "__main__":
#     time.sleep(1)
#     main()

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

def start_tcp_server(input_queue):
    """Start a TCP server to receive queries from Node.js and return search results."""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("127.0.0.1", 5000))
    server.listen(5)
    print("TCP Server Listening on port 5000...")

    while True:
        conn, addr = server.accept()
        data = conn.recv(1024).decode("utf-8").strip()
        
        if data:
            print(f"Received query from Node.js: {data}")
            input_queue.put((data, conn))  # Pass connection to send response

async def search_loop(vector_store: VectorStore, input_queue: queue.Queue):
    """Interactive search interface with WebSocket output."""
    print("\nDocument Search System")
    print("Waiting for queries from Node.js...\n")

    while True:
        try:
            if not input_queue.empty():
                query, conn = input_queue.get()
                print(f"Processing query: {query}")

                if query.lower() == "exit":
                    break

                # Perform search
                start_time = time.time()
                results = vector_store.hybrid_search(query)
                duration = time.time() - start_time

                # Format response
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

                # Send the response back to Node.js over TCP
                json_response = json.dumps(response)
                conn.sendall(json_response.encode("utf-8"))
                conn.close()  # Close connection after sending data

        except Exception as e:
            print(f"\nError: {str(e)}")

async def main():
    input_queue = queue.Queue()
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

        # Start TCP server in separate thread
        threading.Thread(target=start_tcp_server, args=(input_queue,), daemon=True).start()

        # Run search loop asynchronously
        await search_loop(vector_store, input_queue)

    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        sys.exit(1)
    finally:
        if vector_store:
            vector_store.close()
        logger.info("System shutdown")

if __name__ == "__main__":
    asyncio.run(main())


# import sys
# import time
# import logging
# from pathlib import Path
# from fastapi import FastAPI, HTTPException
# from pydantic import BaseModel
# from PyPDF2 import PdfReader
# from vector_store import VectorStore
# from pdf_processor import PDFProcessor
# from config import Config
# from sentence_transformers import SentenceTransformer
# from qdrant_client import QdrantClient

# app = FastAPI()
 
# class QueryRequest(BaseModel):
#     query: str

# # class VectorStore:
# #     def __init__(self):
# #         self.client = QdrantClient("localhost", port=6333)

# #     def close(self):
# #         self.client.close()  # Ensure this method exists

# # class VectorStore:
# #     def __init__(self):
# #         self.client = QdrantClient("localhost", port=6333)

# #     def close(self):
# #         self.client.close()  # Ensure this method exists

# #     def hybrid_search(self, query):
# #         return self.client.search(collection_name="your_collection", query_vector=query, limit=5)
     


# # class VectorStore:
# #     def __init__(self):
# #         self.client = QdrantClient("localhost", port=6333)
# #         self.embedder = SentenceTransformer("all-MiniLM-L6-v2")  # Load embedding model

# #     def hybrid_search(self, query):
# #         query_vector = self.embedder.encode(query).tolist()  # Convert text to vector
# #         return self.client.search(
# #             collection_name="document_chunk",
# #             query_vector=query_vector,  # Pass vector instead of text
# #             limit=5
# #         )
   
# from qdrant_client.models import Distance, VectorParams
# from sentence_transformers import SentenceTransformer

# class VectorStore:
#     def __init__(self):
#         self.client = QdrantClient("localhost", port=6333)
#         self.embedder = SentenceTransformer("all-MiniLM-L6-v2")  # Load embedding model
#         self.collection_name = "document_chunks"

#         # Ensure collection exists before searching
#         self.ensure_collection()

#     def ensure_collection(self):
#         """Check if collection exists, create it if missing"""
#         collections = self.client.get_collections().collections
#         if not any(col.name == self.collection_name for col in collections):
#             self.client.create_collection(
#                 collection_name=self.collection_name,
#                 vectors_config=VectorParams(size=384, distance=Distance.COSINE)
#             )
#             print(f"✅ Collection `{self.collection_name}` created.")

#     def hybrid_search(self, query):
#         query_vector = self.embedder.encode(query).tolist()  # Convert text to vector
#         return self.client.search(
#             collection_name=self.collection_name,
#             query_vector=query_vector,  # Pass vector instead of text
#             limit=5
#         )

# def setup_logging():
#     logging.basicConfig(
#         level=logging.INFO,
#         format="%(asctime)s - %(levelname)s - %(message)s",
#         handlers=[
#             logging.FileHandler("semantic_search.log", encoding="utf-8"),
#             logging.StreamHandler()
#         ]
#     )
#     return logging.getLogger(__name__)

# def verify_pdf(pdf_path: Path) -> bool:
#     try:
#         with pdf_path.open('rb') as f:
#             if b"/Font" not in f.read(1000):
#                 print(f"Warning: {pdf_path.name} may be scanned PDF")
        
#         reader = PdfReader(pdf_path)
#         return any(page.extract_text() for page in reader.pages[:3])
#     except Exception as e:
#         print(f"Error verifying {pdf_path.name}: {str(e)}")
#         return False

# def check_pdfs() -> bool:
#     print("\nChecking PDF directory...")
#     valid = False
    
#     if not Config.PDF_DIRECTORY.exists():
#         print(f"✖ Directory not found: {Config.PDF_DIRECTORY}")
#         return False
        
#     pdf_files = list(Config.PDF_DIRECTORY.glob("*.pdf")) + list(Config.PDF_DIRECTORY.glob("*.PDF"))
#     if not pdf_files:
#         print(f"✖ No PDFs found in {Config.PDF_DIRECTORY}")
#         return False
        
#     for pdf_file in pdf_files:
#         if verify_pdf(pdf_file):
#             print(f"✔ Valid PDF found: {pdf_file.name}")
#             valid = True
#         else:
#             print(f"✖ Invalid PDF (may be scanned): {pdf_file.name}")
    
#     return valid

# logger = setup_logging()
# vector_store = None

# try:
#     if not check_pdfs():
#         sys.exit("No valid PDFs found. Exiting.")
        
#     logger.info("Initializing system...")
#     vector_store = VectorStore()
#     processor = PDFProcessor()
    
#     logger.info("Processing documents...")
#     chunks = processor.process_pdfs()
#     if chunks:
#         logger.info(f"Indexing {len(chunks)} chunks...")
#         vector_store.create_index(chunks)
#     else:
#         logger.info("No new documents to process")
    
# except Exception as e:
#     logger.error(f"Fatal error: {str(e)}")
#     sys.exit(1)

# # @app.post("/generate")
# # def generate_search(request: QueryRequest):
# #     if not request.query.strip():
# #         raise HTTPException(status_code=400, detail="Query cannot be empty")
    
# #     try:
# #         start_time = time.time()
# #         results = vector_store.hybrid_search(request.query)
# #         duration = time.time() - start_time
        
# #         logger.info(f"Found {len(results)} results for query: {request.query} in {duration:.2f}s")
        
# #         for i, res in enumerate(results, 1):
# #             payload = res['payload']
# #             logger.info(f"{i}. [{payload['pdf_name']} - Page {payload['page']}] {payload['text'][:300]}...")
        
# #         return {"query": request.query, "results": results, "time_taken": duration}
        
# #     except Exception as e:
# #         logger.error(f"Error processing query: {str(e)}")
# #         raise HTTPException(status_code=500, detail="Internal Server Error")


# # @app.post("/generate")
# # def generate_search(request: QueryRequest):
# #     if not request.query.strip():
# #         raise HTTPException(status_code=400, detail="Query cannot be empty")

# #     try:
# #         vector_store = VectorStore()  # Ensure correct initialization
# #         start_time = time.time()
# #         results = vector_store.hybrid_search(request.query)
# #         duration = time.time() - start_time

# #         logger.info(f"Found {len(results)} results for query: {request.query} in {duration:.2f}s")

# #         return {"query": request.query, "results": results, "time_taken": duration}

# #     except Exception as e:
# #         logger.error(f"Error processing query: {str(e)}")
# #         raise HTTPException(status_code=500, detail="Internal Server Error")

# @app.post("/generate")
# def generate_search(request: QueryRequest):
#     if not request.query.strip():
#         raise HTTPException(status_code=400, detail="Query cannot be empty")

#     try:
#         vector_store = VectorStore()  # Ensure correct initialization
#         start_time = time.time()
#         results = vector_store.hybrid_search(request.query)  # Now uses embeddings
#         duration = time.time() - start_time

#         logger.info(f"Found {len(results)} results for query: {request.query} in {duration:.2f}s")

#         return {"query": request.query, "results": results, "time_taken": duration}

#     except Exception as e:
#         logger.error(f"Error processing query: {str(e)}")
#         raise HTTPException(status_code=500, detail="Internal Server Error")

# @app.on_event("shutdown")
# def shutdown_event():
#     global vector_store
#     if vector_store:
#         vector_store.close()

#     logger.info("System shutdown")
