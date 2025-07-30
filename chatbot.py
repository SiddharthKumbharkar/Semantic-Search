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
            logger.error(f"Ollama model '{self.model_name}' not found. Please run 'ollama pull {self.model_name}'")
            raise RuntimeError(f"Ollama model '{self.model_name}' not found.") from e

    def generate_response(self, query: str):
        """Generate a response using the RAG pipeline."""
        if not query:
            return "Please ask a question.", []

        # 1. Retrieve context from the vector store
        logger.info(f"Retrieving context for query: '{query}'")
        retrieved_chunks = self.vector_store.get_context_for_rag(query)

        if not retrieved_chunks:
            return "I could not find any relevant information in your documents to answer this question.", []

        # 2. Format the context
        context_str = "\n\n---\n\n".join([chunk['text'] for chunk in retrieved_chunks])
        
        # 3. Create the prompt
        prompt = self.prompt_template.format(context=context_str, question=query)
        
        logger.info("Generating response from LLM...")
        try:
            # 4. Generate response from Ollama
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
            return f"An error occurred while communicating with the language model: {e}", []

