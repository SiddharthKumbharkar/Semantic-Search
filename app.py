import streamlit as st
import time
import logging
from pathlib import Path
from PyPDF2 import PdfReader
from vector_store import VectorStore
from pdf_processor import PDFProcessor
from config import Config
from qdrant_client import QdrantClient
import asyncio

try:
    asyncio.get_running_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())

class QdrantManager:
    def __init__(self):
        # Connect to the running Qdrant instance instead of using local storage
        self.client = QdrantClient("localhost", port=6333)  # Use server mode

    def get_client(self):
        return self.client


# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Initialize VectorStore and PDFProcessor
vector_store = VectorStore()
processor = PDFProcessor()

# Streamlit UI
st.set_page_config(page_title="Document Search System", layout="wide")

st.title("📄 AI-Powered Document Search")
st.write("Upload PDFs, process them, and search for information.")

# Sidebar - Upload PDFs
st.sidebar.header("📂 Upload PDFs")
uploaded_files = st.sidebar.file_uploader("Upload PDFs", type=["pdf"], accept_multiple_files=True)

if uploaded_files:
    with st.spinner("Processing PDFs..."):
        pdf_paths = []
        for uploaded_file in uploaded_files:
            file_path = Path(Config.PDF_DIRECTORY) / uploaded_file.name
            with open(file_path, "wb") as f:
                f.write(uploaded_file.read())
            pdf_paths.append(file_path)

        st.sidebar.success(f"Uploaded {len(uploaded_files)} files successfully!")

        # Process and Index PDFs
        chunks = processor.process_pdfs()
        if chunks:
            vector_store.create_index(chunks)
            st.sidebar.success(f"Indexed {len(chunks)} document chunks!")

# Search Bar
st.subheader("🔍 Search Documents")
query = st.text_input("Enter your search query:")

if query:
    with st.spinner("Searching..."):
        start_time = time.time()
        results = vector_store.hybrid_search(query)
        duration = time.time() - start_time

        st.write(f"⏳ Found {len(results)} results in {duration:.2f} seconds")

        for i, res in enumerate(results, 1):
            payload = res["payload"]
            st.markdown(f"**{i}. [{payload['pdf_name']} - Page {payload['page']}]**")
            st.text(payload["text"][:300] + ("..." if len(payload["text"]) > 300 else ""))
            st.write("---")

# Footer
st.write("👨‍💻 Built with ❤️ using Streamlit")
# import requests

# QDRANT_URL = "http://localhost:6333"

# def check_qdrant_health():
#     try:
#         response = requests.get(f"{QDRANT_URL}/healthz")
#         response.raise_for_status()  # Raise error for bad status codes

#         print("Raw Response Content:", response.text)  # Print raw text instead of JSON parsing
#         if "healthz check passed" in response.text.lower():
#             print("✅ Qdrant server is running correctly!")
#         else:
#             print("⚠️ Unexpected response from Qdrant:", response.text)
    
#     except requests.exceptions.RequestException as e:
#         print("❌ Error connecting to Qdrant server:", e)

# if __name__ == "__main__":
#     check_qdrant_health()
