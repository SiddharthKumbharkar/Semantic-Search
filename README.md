# Semantic Search Engine - AI-Powered Document Intelligence

A powerful semantic search engine that combines vector embeddings, keyword search, and AI-powered chatbots to provide intelligent document search and question-answering capabilities. Built with Python, it features both a command-line interface and a modern Streamlit web application.

## 🚀 Features

### Core Search Capabilities

- **🔍 Hybrid Search**: Combines semantic vector search with traditional keyword search for optimal results
- **📄 PDF Processing**: Intelligent text extraction and chunking from PDF documents
- **🧠 Vector Embeddings**: Uses sentence-transformers for semantic understanding
- **⚡ Fast Retrieval**: Optimized search with caching and performance monitoring
- **🎯 Context-Aware**: Maintains document context and page references

### AI-Powered Features

- **🤖 RAG Chatbot**: Retrieval-Augmented Generation for intelligent Q&A
- **💬 Conversational Interface**: Natural language interaction with your documents
- **📚 Source Attribution**: Always shows which documents and pages contain the information
- **🔄 Real-time Processing**: Live document indexing and search capabilities

### User Interfaces

- **🖥️ Command Line**: Interactive terminal-based search interface
- **🌐 Web Application**: Modern Streamlit-based web interface
- **📱 Responsive Design**: Works on desktop and mobile devices
- **📊 Performance Metrics**: Real-time search performance monitoring

### Advanced Features

- **💾 Embedding Caching**: Intelligent caching system for faster subsequent searches
- **🔧 Configurable**: Highly customizable search parameters and models
- **📈 Scalable**: Built with Qdrant vector database for enterprise-scale deployment
- **🛡️ Access Control**: Document-level access control (framework ready)

## 🛠️ Tech Stack

### Core Technologies

- **Python 3.8+**: Main programming language
- **Streamlit**: Web application framework
- **Qdrant**: Vector database for semantic search
- **SQLite**: Keyword search database with FTS5
- **Sentence Transformers**: Embedding generation

### AI & ML Libraries

- **sentence-transformers**: Text embeddings (all-MiniLM-L6-v2)
- **Ollama**: Local LLM integration (Llama2)
- **PyPDF2**: PDF text extraction
- **NLTK**: Natural language processing
- **NumPy**: Numerical computations

### Data Processing

- **tqdm**: Progress bars for long operations
- **hashlib**: Content hashing for deduplication
- **pathlib**: Modern file system operations
- **json**: Data serialization and caching

## 📋 Prerequisites

Before you begin, ensure you have the following installed:

### Required Software

- **Python 3.8 or higher**
- **pip** (Python package manager)
- **Git** (for cloning the repository)

### Optional (for full functionality)

- **Ollama** (for AI chatbot features)

  ```bash
  # Install Ollama (macOS/Linux)
  curl -fsSL https://ollama.ai/install.sh | sh

  # Pull the required model
  ollama pull llama2:latest
  ```

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd ai_docs/Semantic-Search
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Prepare Your Documents

Place your PDF files in the `data/` directory:

```bash
mkdir -p data
# Copy your PDF files to the data directory
cp /path/to/your/documents/*.pdf data/
```

### 4. Run the Application

#### Option A: Web Interface (Recommended)

```bash
streamlit run app.py
```

Then open your browser to `http://localhost:8501`

#### Option B: Command Line Interface

```bash
python main.py
```

### 5. First-Time Setup

1. **Upload Documents**: Use the web interface to upload PDF files
2. **Process Documents**: Click "Process All Documents" to index them
3. **Start Searching**: Use either the search interface or chatbot

## 📁 Project Structure

```
Semantic-Search/
├── app.py                    # Streamlit web application
├── main.py                   # Command-line interface
├── api_server.py             # API server for external integration
├── config.py                 # Configuration settings
├── requirements.txt          # Python dependencies
├── config.yaml              # Qdrant configuration
├──
├── data/                    # PDF documents directory
│   ├── *.pdf               # Your PDF files
│   └── static/             # Static file serving
├──
├── vector_db/              # Vector database storage
│   ├── qdrant/             # Qdrant database files
│   ├── embeddings/         # Cached embeddings
│   └── keyword_search.db   # SQLite keyword database
├──
├── model_cache/            # Downloaded ML models
│   └── models--sentence-transformers--all-MiniLM-L6-v2/
├──
├── Core Modules:
├── vector_store.py         # Vector search and embedding management
├── pdf_processor.py        # PDF text extraction and chunking
├── chatbot.py             # RAG chatbot implementation
├── qdrant_manager.py      # Qdrant database operations
├── keyword_db.py          # SQLite keyword search
└──
└── Utilities:
    ├── resetdb.py         # Database reset utility
    ├── test_api.py        # API testing
    └── test_performance.py # Performance benchmarking
```

## ⚙️ Configuration

### Main Configuration (`config.py`)

```python
class Config:
    # Embedding Model
    EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # Sentence transformer model
    EMBEDDING_DIM = 384                    # Vector dimensions

    # Text Processing
    MIN_CHARS_PER_PAGE = 50               # Minimum characters per page
    MIN_SENTENCE_LENGTH = 5               # Minimum words per sentence
    SENTENCES_PER_CHUNK = 5               # Sentences per chunk

    # Search Settings
    SIMILARITY_TOP_K = 8                  # Number of results to return
    HYBRID_SEARCH_RATIO = 0.7             # Semantic vs keyword ratio

    # Chatbot Settings
    OLLAMA_MODEL = "llama2:latest"        # Local LLM model
    CONTEXT_CHUNKS_FOR_RAG = 3            # Context chunks for RAG
```

### Qdrant Configuration (`config.yaml`)

```yaml
storage:
  snapshot_path: "./qdrant_db/snapshots"
  payload_indexing_threshold: 100
service:
  http_port: 6333
  grpc_port: 6334
cluster:
  enabled: false
```

## 🔧 API Usage

### Command Line API

```bash
# Search for documents
python api_server.py search '{"query": "machine learning algorithms", "userId": "user1"}'

# Chat with documents
python api_server.py chatbot '{"query": "What is the main topic?", "userId": "user1"}'

# Process documents
python api_server.py process '{"files": ["document1.pdf", "document2.pdf"]}'
```

### Python API Integration

```python
from vector_store import VectorStore
from chatbot import Chatbot

# Initialize components
vector_store = VectorStore()
chatbot = Chatbot(vector_store)

# Perform search
results = vector_store.hybrid_search("your search query")
print(f"Found {len(results)} results")

# Chat with documents
response, sources = chatbot.generate_response("What is this document about?")
print(f"Response: {response}")
print(f"Sources: {len(sources)} documents")
```

## 🎯 Usage Examples

### Basic Search

```python
# Initialize the vector store
from vector_store import VectorStore
vs = VectorStore()

# Search for information
results = vs.hybrid_search("artificial intelligence applications")
for result in results:
    print(f"Document: {result['payload']['pdf_name']}")
    print(f"Page: {result['payload']['page']}")
    print(f"Text: {result['payload']['text'][:200]}...")
    print(f"Score: {result['score']:.4f}")
```

### Document Processing

```python
from pdf_processor import PDFProcessor

# Process PDFs
processor = PDFProcessor()
chunks = processor.process_pdfs()
print(f"Processed {len(chunks)} document chunks")

# Index the chunks
vs.create_index(chunks)
```

### Chatbot Interaction

```python
from chatbot import Chatbot

# Initialize chatbot
chatbot = Chatbot(vector_store)

# Ask questions
response, sources = chatbot.generate_response(
    "What are the key findings in the research papers?"
)

print(f"Answer: {response}")
print(f"Based on {len(sources)} source documents")
```

## 🔍 Search Features

### Hybrid Search Algorithm

1. **Semantic Search**: Uses vector embeddings to find semantically similar content
2. **Keyword Search**: Traditional keyword matching with SQLite FTS5
3. **Result Fusion**: Combines results using Reciprocal Rank Fusion (RRF)
4. **Score Optimization**: Balances semantic relevance with keyword precision

### Search Optimization

- **Embedding Caching**: Reuses computed embeddings for faster searches
- **Batch Processing**: Processes multiple documents efficiently
- **Score Thresholding**: Filters low-quality results automatically
- **Context Preservation**: Maintains document and page context

## 🤖 Chatbot Features

### RAG (Retrieval-Augmented Generation)

1. **Query Understanding**: Analyzes user questions semantically
2. **Context Retrieval**: Finds relevant document chunks
3. **Response Generation**: Uses local LLM (Ollama) for answers
4. **Source Attribution**: Always provides document sources

### Fallback Mode

- Works without Ollama installation
- Provides context-based responses
- Maintains source attribution
- Graceful degradation of functionality

## 📊 Performance Optimization

### Caching Strategy

- **Embedding Cache**: Stores computed embeddings in JSON files
- **Model Caching**: Reuses loaded sentence transformer models
- **Result Caching**: Caches search results for repeated queries

### Database Optimization

- **Vector Indexing**: Qdrant's optimized vector search
- **FTS5 Indexing**: SQLite full-text search for keywords
- **Batch Operations**: Efficient bulk insertions and updates

### Memory Management

- **Lazy Loading**: Models loaded only when needed
- **Resource Cleanup**: Proper connection and resource management
- **Progress Tracking**: Real-time progress indicators for long operations

## 🛡️ Security & Access Control

### Document Access Framework

```python
# Filter results by accessible documents
accessible_docs = ["document1.pdf", "document2.pdf"]
results = vector_store.hybrid_search(query, accessible_docs)

# Chatbot with access control
response, sources = chatbot.generate_response(query, accessible_docs)
```

### Security Features

- **Input Validation**: Sanitizes all user inputs
- **Error Handling**: Graceful error handling and logging
- **Resource Limits**: Prevents resource exhaustion
- **Access Logging**: Comprehensive activity logging

## 🚀 Deployment

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run web application
streamlit run app.py

# Run command line interface
python main.py
```

### Production Deployment

```bash
# Install production dependencies
pip install -r requirements.txt

# Set up Qdrant server (optional)
docker run -p 6333:6333 qdrant/qdrant

# Run with production settings
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
```

### Docker Deployment (Optional)

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port", "8501", "--server.address", "0.0.0.0"]
```

## 🔧 Troubleshooting

### Common Issues

#### 1. PDF Processing Errors

```bash
# Check if PDFs are valid
python -c "from PyPDF2 import PdfReader; print('PDF library working')"

# Verify PDF files
ls -la data/*.pdf
```

#### 2. Model Download Issues

```bash
# Clear model cache
rm -rf model_cache/

# Reinstall sentence-transformers
pip uninstall sentence-transformers
pip install sentence-transformers
```

#### 3. Database Issues

```bash
# Reset databases
python resetdb.py

# Check Qdrant status
python -c "from qdrant_manager import QdrantManager; QdrantManager()"
```

#### 4. Ollama Connection Issues

```bash
# Check Ollama status
ollama list

# Pull required model
ollama pull llama2:latest

# Test Ollama connection
ollama run llama2:latest "Hello"
```

### Performance Issues

- **Slow Search**: Check embedding cache, reduce search limits
- **Memory Usage**: Monitor model loading, use smaller batch sizes
- **Storage**: Clean up old embeddings, optimize database

## 📈 Monitoring & Logging

### Logging Configuration

```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("semantic_search.log"),
        logging.StreamHandler()
    ]
)
```

### Performance Monitoring

- **Search Latency**: Track search response times
- **Memory Usage**: Monitor embedding and model memory
- **Database Performance**: Track Qdrant and SQLite performance
- **Error Rates**: Monitor and log error frequencies

## 🤝 Contributing

### Development Setup

```bash
# Clone repository
git clone <repository-url>
cd Semantic-Search

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -r requirements.txt
pip install pytest black flake8  # Development tools
```

### Code Style

- Follow PEP 8 guidelines
- Use type hints where possible
- Add docstrings to all functions
- Include error handling and logging

### Testing

```bash
# Run API tests
python test_api.py

# Run performance tests
python test_performance.py

# Test specific components
python -c "from vector_store import VectorStore; vs = VectorStore(); print('Vector store working')"
```

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

### Getting Help

- **Documentation**: Check this README and inline code comments
- **Issues**: Create GitHub issues for bugs and feature requests
- **Logs**: Check `semantic_search.log` for detailed error information

### Common Commands

```bash
# Check system status
python -c "import sys; print(f'Python: {sys.version}')"

# Test core functionality
python -c "from config import Config; print('Config loaded')"

# Verify dependencies
pip list | grep -E "(sentence-transformers|qdrant|streamlit)"
```

## 🔮 Roadmap

### Upcoming Features

- **Multi-format Support**: DOCX, TXT, HTML document processing
- **Advanced RAG**: Multi-turn conversations and context memory
- **API Endpoints**: RESTful API for external integrations
- **User Management**: Multi-user support with authentication
- **Advanced Analytics**: Search analytics and usage statistics

### Performance Improvements

- **GPU Acceleration**: CUDA support for faster embeddings
- **Distributed Search**: Multi-node Qdrant deployment
- **Advanced Caching**: Redis-based caching layer
- **Streaming Processing**: Real-time document processing

### Enterprise Features

- **SSO Integration**: Single sign-on authentication
- **Audit Logging**: Comprehensive activity tracking
- **Backup & Recovery**: Automated backup systems
- **Scalability**: Horizontal scaling capabilities

---

**Semantic Search Engine** - Intelligent document search powered by AI. Built with ❤️ using Python and modern ML technologies.
