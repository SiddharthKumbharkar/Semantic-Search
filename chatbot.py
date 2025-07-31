import ollama
import logging
from config import Config

logger = logging.getLogger(__name__)

class Chatbot:
    def __init__(self, vector_store):
        self.vector_store = vector_store
        self.model_name = Config.OLLAMA_MODEL
        self.prompt_template = Config.RAG_PROMPT_TEMPLATE
        self._verify_model()

    def _verify_model(self):
        """Check if the Ollama model is available."""
        try:
            ollama.show(self.model_name)
            logger.info(f"Successfully connected to Ollama model: {self.model_name}")
        except Exception as e:
            logger.warning(f"Ollama model '{self.model_name}' not found. Using fallback mode.")
            logger.warning(f"Please run 'ollama pull {self.model_name}' to enable full functionality.")
            # Don't raise error, just log warning

    def generate_response(self, query: str, accessible_docs: list = None):
        """Generate a response using the RAG pipeline."""
        if not query:
            return "Please ask a question.", []

        # 1. Retrieve context from the vector store
        logger.info(f"Retrieving context for query: '{query}'")
        retrieved_chunks = self.vector_store.get_context_for_rag(query)

        if not retrieved_chunks:
            return "I could not find any relevant information in your documents to answer this question.", []

        # 2. Filter chunks by accessible documents if specified
        if accessible_docs is not None:
            retrieved_chunks = self._filter_chunks_by_access(retrieved_chunks, accessible_docs)
            if not retrieved_chunks:
                return "I could not find any relevant information in your accessible documents to answer this question.", []

        # 3. Format the context
        context_str = "\n\n---\n\n".join([chunk['text'] for chunk in retrieved_chunks])
        
        # 4. Create the prompt
        prompt = self.prompt_template.format(context=context_str, question=query)
        
        logger.info("Generating response from LLM...")
        try:
            # 5. Generate response from Ollama
            response = ollama.generate(
                model=self.model_name,
                prompt=prompt
            )
            
            # Extract the text part of the response
            response_text = response.get('response', 'Sorry, I encountered an error.').strip()
            
            # Return the response and the source chunks
            return response_text, retrieved_chunks

        except Exception as e:
            logger.error(f"Error generating response from Ollama: {e}")
            # Fallback: return a simple response based on the context
            return self._generate_fallback_response(query, context_str), retrieved_chunks

    def _generate_fallback_response(self, query: str, context: str) -> str:
        """Generate a simple fallback response when Ollama is not available."""
        # Create a more professional and concise fallback response
        context_summary = context[:800] + "..." if len(context) > 800 else context
        
        return f"""Based on the available documents, here's what I found regarding your question: "{query}"

{context_summary}

This information is extracted directly from your documents. For more detailed AI-powered responses, please ensure Ollama is properly configured."""

    def _filter_chunks_by_access(self, chunks: list, accessible_docs: list) -> list:
        """Filter chunks to only include those from accessible documents"""
        if not accessible_docs:
            return chunks
        
        filtered_chunks = []
        for chunk in chunks:
            # Extract document name from chunk
            doc_name = None
            if 'metadata' in chunk and 'source' in chunk['metadata']:
                doc_name = chunk['metadata']['source']
            elif 'pdf_name' in chunk:
                doc_name = chunk['pdf_name']
            
            if doc_name and doc_name in accessible_docs:
                filtered_chunks.append(chunk)
        
        return filtered_chunks

