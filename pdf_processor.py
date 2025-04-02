import os
import json
import hashlib
import logging
from pathlib import Path
from PyPDF2 import PdfReader
from config import Config
import nltk
from nltk.tokenize import sent_tokenize
from tqdm import tqdm

nltk.download('punkt', quiet=True)
logger = logging.getLogger(__name__)

class PDFProcessor:
    @staticmethod
    def get_file_hash(filepath: str) -> str:
        """Generate MD5 hash of file contents"""
        with open(filepath, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()

    @staticmethod
    def get_processed_files() -> dict:
        """Get dictionary of processed files and their hashes"""
        hash_file = Path(Config.VECTOR_DB_DIR) / Config.FILE_HASHES_JSON
        if hash_file.exists():
            with open(hash_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    @staticmethod
    def save_processed_files(processed: dict):
        """Save processed files dictionary"""
        Path(Config.VECTOR_DB_DIR).mkdir(parents=True, exist_ok=True)
        hash_file = Path(Config.VECTOR_DB_DIR) / Config.FILE_HASHES_JSON
        with open(hash_file, 'w', encoding='utf-8') as f:
            json.dump(processed, f)

    def extract_text_from_pdf(self, pdf_path: str) -> list:
        """Extract text from PDF with error handling"""
        try:
            reader = PdfReader(pdf_path)
            pages_text = []
            for page_num, page in enumerate(reader.pages, start=1):
                text = page.extract_text()
                if text and len(text.strip()) >= Config.MIN_CHARS_PER_PAGE:
                    pages_text.append({
                        "pdf_name": os.path.basename(pdf_path),
                        "page": page_num,
                        "text": text.strip()
                    })
            return pages_text
        except Exception as e:
            logger.error(f"Error extracting text from {pdf_path}: {str(e)}")
            return []

    def chunk_text(self, pages_text: list) -> list:
        """Split text into chunks"""
        chunks = []
        for page in pages_text:
            sentences = sent_tokenize(page["text"])
            valid_sentences = [s for s in sentences if len(s.split()) >= Config.MIN_SENTENCE_LENGTH]
            
            # Fallback to word-based chunking if no valid sentences
            if not valid_sentences:
                words = page["text"].split()
                chunk_size = Config.MIN_SENTENCE_LENGTH * Config.SENTENCES_PER_CHUNK
                for i in range(0, len(words), chunk_size):
                    chunk_text = ' '.join(words[i:i+chunk_size])
                    chunk_id = hashlib.md5(f"{page['pdf_name']}_{page['page']}_{i}".encode()).hexdigest()
                    chunks.append({
                        "text": chunk_text,
                        "metadata": {
                            "pdf_name": page["pdf_name"],
                            "page": page["page"],
                            "chunk_id": chunk_id
                        }
                    })
                continue
                
            # Sentence-based chunking
            for i in range(0, len(valid_sentences), Config.SENTENCES_PER_CHUNK):
                chunk_text = ' '.join(valid_sentences[i:i+Config.SENTENCES_PER_CHUNK])
                chunk_id = hashlib.md5(f"{page['pdf_name']}_{page['page']}_{i}".encode()).hexdigest()
                chunks.append({
                    "text": chunk_text,
                    "metadata": {
                        "pdf_name": page["pdf_name"],
                        "page": page["page"],
                        "chunk_id": chunk_id
                    }
                })
        return chunks

    def process_pdfs(self) -> list:
        """Process all PDFs in the directory"""
        processed_files = self.get_processed_files()
        current_files = {}
        all_chunks = []
        
        if not Config.PDF_DIRECTORY.exists():
            logger.error(f"PDF directory not found: {Config.PDF_DIRECTORY}")
            return []
            
        pdf_files = list(Config.PDF_DIRECTORY.glob("*.pdf")) + list(Config.PDF_DIRECTORY.glob("*.PDF"))
        if not pdf_files:
            logger.warning(f"No PDF files found in {Config.PDF_DIRECTORY}")
            return []
            
        for pdf_file in tqdm(pdf_files, desc="Processing PDFs"):
            file_hash = self.get_file_hash(pdf_file)
            if pdf_file.name in processed_files and processed_files[pdf_file.name] == file_hash:
                continue
                
            pages_text = self.extract_text_from_pdf(pdf_file)
            if not pages_text:
                continue
                
            chunks = self.chunk_text(pages_text)
            all_chunks.extend(chunks)
            current_files[pdf_file.name] = file_hash
            
        if current_files:
            processed_files.update(current_files)
            self.save_processed_files(processed_files)
            
        return all_chunks