import streamlit as st
import time
import logging
from pathlib import Path

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

def initialize_and_process_pdfs(_vector_store):
    """Checks for new PDFs and processes them."""
    with st.spinner("Checking for new documents and updating index..."):
        processor = PDFProcessor()
        chunks = processor.process_pdfs()
        if chunks:
            logger.info(f"Indexing {len(chunks)} new chunks...")
            _vector_store.create_index(chunks)
            st.success(f"Successfully indexed {len(chunks)} new document chunks!")
            time.sleep(2)
        else:
            logger.info("No new documents to process.")
            st.info("Your document index is already up to date.")
            time.sleep(1)

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
            with st.expander(f"**{i}. {payload.get('pdf_name', 'N/A')} - Page {payload.get('page', 'N/A')}** (Score: {res.get('score', 0):.4f})"):
                st.markdown(payload.get('text', 'No text available.'))

def render_chatbot_interface(chatbot):
    """Renders the RAG chatbot UI."""
    st.header("Document Chatbot")
    st.write("Ask questions about your documents. The chatbot will use the indexed content to find answers.")

    # Initialize chat history in session state
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "How can I help you with your documents?"}]

    # Display chat messages
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    # Handle user input
    if prompt := st.chat_input("Ask a question..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

        # Generate and display bot response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response, sources = chatbot.generate_response(prompt)
                st.write(response)

                if sources:
                    st.subheader("Sources:")
                    for source in sources:
                        with st.container(border=True):
                            st.markdown(f"**PDF:** {source['pdf_name']} - **Page:** {source['page']}")
                            st.markdown(f"> {source['text'][:150]}...")
        
        st.session_state.messages.append({"role": "assistant", "content": response})


def main():
    """Main function to run the Streamlit app."""
    st.set_page_config(page_title="Document Search & Chat", layout="wide")
    st.title("📄 Document Intelligence Engine")
    st.write("A powerful tool to search and chat with your PDF documents.")

    # --- Initialization ---
    try:
        vector_store = get_vector_store()
        chatbot = get_chatbot(vector_store)
        initialize_and_process_pdfs(vector_store)
    except Exception as e:
        st.error(f"Failed to initialize the application: {e}")
        logger.error(f"Initialization failed: {e}", exc_info=True)
        return

    # --- Main Interface ---
    st.sidebar.title("Navigation")
    app_mode = st.sidebar.radio("Choose a mode:", ["Hybrid Search", "Chatbot"])

    if app_mode == "Hybrid Search":
        render_search_interface(vector_store)
    elif app_mode == "Chatbot":
        render_chatbot_interface(chatbot)

if __name__ == "__main__":
    # Ensure PDF directory exists
    Config.PDF_DIRECTORY.mkdir(parents=True, exist_ok=True)
    main()
