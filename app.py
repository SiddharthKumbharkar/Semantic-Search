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
                
                pdf_path = Config.PDF_DIRECTORY / pdf_name
                if pdf_path.exists():
                    with open(pdf_path, "rb") as f:
                        st.download_button(
                            label="Download Source PDF",
                            data=f.read(),
                            file_name=pdf_name,
                            mime="application/pdf",
                            key=f"search_download_{i}" # Unique key for search results
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

        # Save the conversation to history after the first user message
        if len(st.session_state.messages) == 2: # Assistant intro + first user message
            chat_title = prompt[:30] + "..." if len(prompt) > 30 else prompt
            st.session_state.history.append({"title": chat_title, "messages": st.session_state.messages.copy()})
            st.session_state.current_chat_index = len(st.session_state.history) - 1


        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response, sources = chatbot.generate_response(prompt)
                st.write(response)

                if sources:
                    st.subheader("Sources:")
                    for i, source in enumerate(sources): # Use enumerate for a unique index
                        pdf_name = source.get('pdf_name', 'N/A')
                        page_num = source.get('page', 0)
                        with st.container(border=True):
                            st.markdown(f"**PDF:** {pdf_name} - **Page:** {page_num}")
                            st.markdown(f"> {source.get('text', '')[:150]}...")
                            
                            pdf_path = Config.PDF_DIRECTORY / pdf_name
                            if pdf_path.exists():
                                with open(pdf_path, "rb") as f:
                                    st.download_button(
                                        label="Download Source",
                                        data=f.read(),
                                        file_name=pdf_name,
                                        mime="application/pdf",
                                        # Add the unique index 'i' to the key
                                        key=f"download_{pdf_name}_{page_num}_{i}"
                                    )
        
        st.session_state.messages.append({"role": "assistant", "content": response})
        # Update the history with the latest messages
        if st.session_state.current_chat_index is not None:
            st.session_state.history[st.session_state.current_chat_index]["messages"] = st.session_state.messages.copy()


def main():
    """Main function to run the Streamlit app."""
    st.set_page_config(page_title="Document Search & Chat", layout="wide")
    st.title("📄 Document Intelligence Engine")

    # Initialize session state for chat history
    if "history" not in st.session_state:
        st.session_state.history = []
    if "current_chat_index" not in st.session_state:
        st.session_state.current_chat_index = None
    
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
                with open(Config.PDF_DIRECTORY / uploaded_file.name, "wb") as f:
                    f.write(uploaded_file.getbuffer())
            st.success(f"Successfully uploaded {len(uploaded_files)} file(s)!")
            st.info("Click the 'Process All Documents' button to add them to the index.")
            st.rerun()

        if st.button("Process All Documents"):
            sync_and_process_pdfs()

        st.divider()
        st.header("Chat History")

        if st.button("New Chat"):
            st.session_state.messages = [{"role": "assistant", "content": "How can I help you with your documents?"}]
            st.session_state.current_chat_index = None
            st.rerun()
        
        for i, chat in enumerate(st.session_state.history):
            if st.button(chat["title"], key=f"chat_{i}"):
                st.session_state.messages = chat["messages"]
                st.session_state.current_chat_index = i
                st.rerun()


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
