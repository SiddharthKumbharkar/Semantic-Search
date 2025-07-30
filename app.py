import streamlit as st
import time
import logging
from pathlib import Path
import shutil
from urllib.parse import quote

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("semantic_search.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Import project modules after logging is configured
from config import Config
from vector_store import VectorStore
from pdf_processor import PDFProcessor
from chatbot import Chatbot

@st.cache_resource
def get_vector_store():
    """Initializes and returns the VectorStore object."""
    logger.info("Initializing VectorStore...")
    return VectorStore()

@st.cache_resource
def get_chatbot(_vector_store):
    """Initializes and returns the Chatbot object."""
    logger.info("Initializing Chatbot...")
    return Chatbot(_vector_store)

def sync_and_process_pdfs():
    """
    Processes PDFs from the data directory. This is a user-triggered action.
    """
    with st.spinner("Processing documents and updating index..."):
        data_files = set(p.name for p in Config.PDF_DIRECTORY.glob("*.pdf"))
        if not data_files:
            st.warning("No PDF files found in the 'data' directory. Please upload files first.")
            return
        
        # Clear cached resources to force re-initialization with new data
        st.cache_resource.clear()
        
        vector_store = get_vector_store()
        processor = PDFProcessor()
        chunks = processor.process_pdfs()

        if chunks:
            logger.info(f"Indexing {len(chunks)} document chunks...")
            vector_store.create_index(chunks)
            st.success(f"Successfully indexed {len(chunks)} document chunks!")
        else:
            logger.info("No new document chunks to index.")
            st.info("No new documents to process.")

    st.success("Processing complete!")


def render_search_interface(vector_store):
    """Renders the hybrid search UI."""
    st.header("Hybrid Search")
    st.write("Search through your documents using a combination of keyword and semantic search.")
    
    query = st.text_input("Enter your search query:", key="search_query")

    if query:
        with st.spinner("Searching..."):
            start_time = time.time()
            results = vector_store.hybrid_search(query)
            duration = time.time() - start_time

        st.write(f"Found **{len(results)}** results in **{duration:.2f}s**.")
        
        for i, res in enumerate(results, 1):
            payload = res.get('payload', {})
            pdf_name = payload.get('pdf_name', 'N/A')
            page_num = payload.get('page', 0)
            
            with st.expander(f"**{i}. {pdf_name} - Page {page_num}** (Score: {res.get('score', 0):.4f})"):
                st.markdown(payload.get('text', 'No text available.'))
                
                # Using st.download_button as a more reliable alternative
                pdf_path = Config.PDF_DIRECTORY / pdf_name
                if pdf_path.exists():
                    with open(pdf_path, "rb") as f:
                        st.download_button(
                            label="Download Source PDF",
                            data=f.read(),
                            file_name=pdf_name,
                            mime="application/pdf"
                        )

def render_chatbot_interface(chatbot):
    """Renders the RAG chatbot UI."""
    st.header("Document Chatbot")
    st.write("Ask questions about your documents. The chatbot will use the indexed content to find answers.")

    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "How can I help you with your documents?"}]

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    if prompt := st.chat_input("Ask a question..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response, sources = chatbot.generate_response(prompt)
                st.write(response)

                if sources:
                    st.subheader("Sources:")
                    for source in sources:
                        pdf_name = source.get('pdf_name', 'N/A')
                        page_num = source.get('page', 0)
                        with st.container(border=True):
                            st.markdown(f"**PDF:** {pdf_name} - **Page:** {page_num}")
                            st.markdown(f"> {source.get('text', '')[:150]}...")
                            
                            # Using st.download_button as a more reliable alternative
                            pdf_path = Config.PDF_DIRECTORY / pdf_name
                            if pdf_path.exists():
                                with open(pdf_path, "rb") as f:
                                    st.download_button(
                                        label="Download Source",
                                        data=f.read(),
                                        file_name=pdf_name,
                                        mime="application/pdf",
                                        key=f"download_{pdf_name}_{page_num}"
                                    )
        
        st.session_state.messages.append({"role": "assistant", "content": response})

def main():
    """Main function to run the Streamlit app."""
    st.set_page_config(page_title="Document Search & Chat", layout="wide")
    st.title("📄 Document Intelligence Engine")
    
    # --- Sidebar for Document Management ---
    with st.sidebar:
        st.header("Document Management")
        
        uploaded_files = st.file_uploader(
            "Upload PDF documents",
            type="pdf",
            accept_multiple_files=True
        )
        if uploaded_files:
            for uploaded_file in uploaded_files:
                # Save the uploaded file to the data directory
                with open(Config.PDF_DIRECTORY / uploaded_file.name, "wb") as f:
                    f.write(uploaded_file.getbuffer())
            st.success(f"Successfully uploaded {len(uploaded_files)} file(s)!")
            st.info("Click the 'Process All Documents' button to add them to the index.")
            # Rerun to update the file list below
            st.rerun()

        if st.button("Process All Documents"):
            sync_and_process_pdfs()

        st.divider()
        st.header("Existing Documents")
        
        pdf_files = sorted(list(Config.PDF_DIRECTORY.glob("*.pdf")))
        if not pdf_files:
            st.write("No documents found.")
        else:
            for pdf_file in pdf_files:
                # Using st.download_button for a more reliable experience
                with open(pdf_file, "rb") as f:
                    st.download_button(
                        label=pdf_file.name,
                        data=f.read(),
                        file_name=pdf_file.name,
                        mime="application/pdf",
                        key=f"view_{pdf_file.name}"
                    )


    # --- Main Interface ---
    st.sidebar.title("Navigation")
    app_mode = st.sidebar.radio("Choose a mode:", ["Hybrid Search", "Chatbot"])

    try:
        vector_store = get_vector_store()
        chatbot = get_chatbot(vector_store)
        
        if app_mode == "Hybrid Search":
            render_search_interface(vector_store)
        elif app_mode == "Chatbot":
            render_chatbot_interface(chatbot)

    except Exception as e:
        st.error(f"An error occurred during app execution: {e}")
        logger.error(f"Application error: {e}", exc_info=True)

if __name__ == "__main__":
    # Ensure necessary directories exist on startup
    Config.PDF_DIRECTORY.mkdir(parents=True, exist_ok=True)
    main()
