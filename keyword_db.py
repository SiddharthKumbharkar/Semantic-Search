import sqlite3
from contextlib import closing
from config import Config
import logging

logger = logging.getLogger(__name__)

class KeywordDatabase:
    def __init__(self):
        self.conn = sqlite3.connect(Config.KEYWORD_DB)
        self._init_db()
    
    def _init_db(self):
        with closing(self.conn.cursor()) as cur:
            # Main table
            cur.execute(f"""
                CREATE TABLE IF NOT EXISTS {Config.KEYWORD_INDEX} (
                    id TEXT PRIMARY KEY,
                    text TEXT NOT NULL,
                    pdf_name TEXT NOT NULL,
                    page INTEGER NOT NULL,
                    keywords TEXT NOT NULL
                )
            """)
            
            # FTS virtual table
            cur.execute(f"""
                CREATE VIRTUAL TABLE IF NOT EXISTS fts_{Config.KEYWORD_INDEX} 
                USING fts5(text, keywords, content='{Config.KEYWORD_INDEX}', content_rowid='id')
            """)
            
            # Synchronization triggers
            cur.execute(f"""
                CREATE TRIGGER IF NOT EXISTS {Config.KEYWORD_INDEX}_after_insert
                AFTER INSERT ON {Config.KEYWORD_INDEX}
                BEGIN
                    INSERT INTO fts_{Config.KEYWORD_INDEX}(rowid, text, keywords)
                    VALUES (new.id, new.text, new.keywords);
                END;
            """)
            self.conn.commit()
    
    def insert_chunks(self, chunks: list):
        if not chunks:
            raise ValueError("No chunks provided for insertion")
            
        with closing(self.conn.cursor()) as cur:
            for chunk in chunks:
                keywords = self._extract_keywords(chunk["text"])
                try:
                    cur.execute(f"""
                        INSERT OR REPLACE INTO {Config.KEYWORD_INDEX}
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        chunk["metadata"]["chunk_id"],
                        chunk["text"],
                        chunk["metadata"]["pdf_name"],
                        chunk["metadata"]["page"],
                        keywords
                    ))
                except sqlite3.Error as e:
                    logger.error(f"Database error: {str(e)}")
                    raise
            self.conn.commit()
            logger.info(f"Inserted {len(chunks)} chunks into keyword database")
    
    def search(self, keywords: list, limit: int = Config.SIMILARITY_TOP_K):
        if not keywords:
            return []
            
        with closing(self.conn.cursor()) as cur:
            query = ' OR '.join(f'"{k}"' for k in keywords)
            cur.execute(f"""
                SELECT * FROM {Config.KEYWORD_INDEX}
                WHERE id IN (
                    SELECT rowid FROM fts_{Config.KEYWORD_INDEX}
                    WHERE fts_{Config.KEYWORD_INDEX} MATCH ?
                    ORDER BY bm25(fts_{Config.KEYWORD_INDEX})
                )
                LIMIT ?
            """, (query, limit))
            return cur.fetchall()
    
    def _extract_keywords(self, text: str) -> str:
        from collections import Counter
        words = [w.lower() for w in text.split() if len(w) > 3]
        if not words:
            return ""
        return ' '.join([w for w, _ in Counter(words).most_common(5)])
    
    def close(self):
        self.conn.close()