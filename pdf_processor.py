import os
import re
import logging
import hashlib
import json
from pathlib import Path
from typing import List, Dict
from PyPDF2 import PdfReader
from tqdm import tqdm
import nltk
from nltk.tokenize import sent_tokenize
from config import Config

nltk.download('punkt', quiet=True)
logger = logging.getLogger(__name__)

class PDFProcessor:
    @staticmethod
    def get_file_hash(filepath: str) -> str:
        with open(filepath, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()

    @staticmethod
    def get_processed_files() -> Dict[str, str]:
        hash_file = Path(Config.VECTOR_DB_DIR) / Config.FILE_HASHES_JSON
        if hash_file.exists():
            with open(hash_file, 'r') as f:
                return json.load(f)
        return {}

    @staticmethod
    def save_processed_files(processed: Dict[str, str]):
        Path(Config.VECTOR_DB_DIR).mkdir(parents=True, exist_ok=True)
        hash_file = Path(Config.VECTOR_DB_DIR) / Config.FILE_HASHES_JSON
        with open(hash_file, 'w') as f:
            json.dump(processed, f)

    @staticmethod
    def extract_text_from_pdf(pdf_path: str) -> List[Dict]:
        try:
            print(f"\n🔍 Analyzing: {os.path.basename(pdf_path)}")
            reader = PdfReader(pdf_path)
            pages_text = []
            
            for page_num, page in enumerate(reader.pages, start=1):
                text = page.extract_text()
                if text:
                    print(f"📄 Page {page_num}: {len(text.strip())} characters")
                    if len(text.strip()) >= Config.MIN_CHARS_PER_PAGE:
                        pages_text.append({
                            "text": text,
                            "page": page_num,
                            "pdf_name": os.path.basename(pdf_path)
                        })
                    else:
                        print(f"⚠️ Skipping page {page_num} - insufficient text")
                else:
                    print(f"❌ No text extracted from page {page_num}")
            
            return pages_text
        except Exception as e:
            print(f"🔥 Extraction failed: {str(e)}")
            return []

    @staticmethod
    def clean_text(text: str) -> str:
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'(\w)-\s+(\w)', r'\1\2', text)
        return text.strip()

    @staticmethod
    def chunk_text(pages_text: List[Dict]) -> List[Dict]:
        chunks = []
        print(f"\n✂️ Creating chunks from {len(pages_text)} pages...")
        
        for page in pages_text:
            clean_text = PDFProcessor.clean_text(page["text"])
            sentences = sent_tokenize(clean_text)
            print(f"📝 Page {page['page']} has {len(sentences)} sentences")
            
            valid_sentences = [s for s in sentences if len(s.split()) >= Config.MIN_SENTENCE_LENGTH]
            print(f"✅ Keeping {len(valid_sentences)} valid sentences")
            
            if not valid_sentences:
                print(f"⚠️ No valid sentences on page {page['page']}")
                continue
                
            # Dynamic chunking based on content
            min_chunk_size = max(1, len(valid_sentences) // 3)  # Aim for 3 chunks per page
            for i in range(0, len(valid_sentences), min_chunk_size):
                chunk_text = ' '.join(valid_sentences[i:i+min_chunk_size])
                print(f"✂️ Chunk {i//min_chunk_size+1}: {chunk_text[:50]}...")
                chunks.append({
                    "text": chunk_text,
                    "metadata": {
                        "pdf_name": page["pdf_name"],
                        "page": page["page"],
                        "chunk_id": hashlib.md5(f"{page['pdf_name']}_{page['page']}_{i}".encode()).hexdigest()
                    }
                })
        
        print(f"\n📦 Created {len(chunks)} total chunks")
        return chunks

    @staticmethod
    def process_pdfs_in_directory(directory: str = Config.PDF_DIRECTORY) -> List[dict]:
        Path(Config.VECTOR_DB_DIR).mkdir(parents=True, exist_ok=True)
        processed_files = PDFProcessor.get_processed_files()
        current_files = {}
        all_chunks = []

        if not os.path.exists(directory):
            raise FileNotFoundError(f"PDF directory not found: {directory}")
            
        pdf_files = [f for f in os.listdir(directory) if f.lower().endswith('.pdf')]
        if not pdf_files:
            logger.warning(f"No PDF files found in {directory}")
            return []

        for pdf_file in tqdm(pdf_files, desc="Processing PDFs"):
            pdf_path = os.path.join(directory, pdf_file)
            file_hash = PDFProcessor.get_file_hash(pdf_path)
            
            if pdf_file in processed_files and processed_files[pdf_file] == file_hash:
                continue
                
            try:
                pages_text = PDFProcessor.extract_text_from_pdf(pdf_path)
                if not pages_text:
                    logger.warning(f"No text extracted from {pdf_file}")
                    continue
                    
                chunks = PDFProcessor.chunk_text(pages_text)
                if not chunks:
                    logger.warning(f"No valid chunks created from {pdf_file}")
                    continue
                    
                all_chunks.extend(chunks)
                current_files[pdf_file] = file_hash
                logger.info(f"Processed: {pdf_file} ({len(chunks)} chunks)")
                
            except Exception as e:
                logger.error(f"Error processing {pdf_file}: {str(e)}")
                continue
        
        if current_files:
            processed_files.update(current_files)
            PDFProcessor.save_processed_files(processed_files)
        
        logger.info(f"Total chunks processed: {len(all_chunks)}")
        return all_chunks