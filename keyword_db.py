import sqlite3
from contextlib import closing
from config import Config
import logging
from collections import Counter
import nltk
from nltk.tokenize import word_tokenize

nltk.download('punkt', quiet=True)
logger = logging.getLogger(__name__)

class KeywordDatabase:
    def __init__(self):
        self.conn = sqlite3.connect(Config.KEYWORD_DB)
        self._init_db()
    
    def _init_db(self):
        with closing(self.conn.cursor()) as cur:
            cur.execute(f"DROP TABLE IF EXISTS {Config.KEYWORD_INDEX}")
            cur.execute(f"DROP TABLE IF EXISTS fts_{Config.KEYWORD_INDEX}")
            
            cur.execute(f"""
                CREATE TABLE {Config.KEYWORD_INDEX} (
                    rowid INTEGER PRIMARY KEY,
                    id TEXT UNIQUE NOT NULL,
                    text TEXT NOT NULL,
                    pdf_name TEXT NOT NULL,
                    page INTEGER NOT NULL,
                    keywords TEXT NOT NULL
                )
            """)
            
            cur.execute(f"""
                CREATE VIRTUAL TABLE fts_{Config.KEYWORD_INDEX} USING fts5(
                    keywords,
                    content='{Config.KEYWORD_INDEX}',
                    content_rowid='rowid',
                    tokenize='porter'
                )
            """)
            
            cur.execute(f"""
                CREATE TRIGGER {Config.KEYWORD_INDEX}_ai AFTER INSERT ON {Config.KEYWORD_INDEX}
                BEGIN
                    INSERT INTO fts_{Config.KEYWORD_INDEX}(rowid, keywords)
                    VALUES (new.rowid, new.keywords);
                END;
            """)
            self.conn.commit()

    def insert_chunks(self, chunks: list):
        with closing(self.conn.cursor()) as cur:
            for chunk in chunks:
                keywords = self._extract_keywords(chunk["text"])
                try:
                    cur.execute(f"""
                        INSERT INTO {Config.KEYWORD_INDEX}
                        (id, text, pdf_name, page, keywords)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        chunk["metadata"]["chunk_id"],
                        chunk["text"],
                        chunk["metadata"]["pdf_name"],
                        chunk["metadata"]["page"],
                        keywords
                    ))
                except sqlite3.Error as e:
                    logger.error(f"DB insert error: {str(e)}")
            self.conn.commit()

    def search(self, keywords: list, limit: int):
        with closing(self.conn.cursor()) as cur:
            query = ' OR '.join(keywords)
            try:
                cur.execute(f"""
                    SELECT k.id, k.text, k.pdf_name, k.page
                    FROM {Config.KEYWORD_INDEX} k
                    WHERE k.rowid IN (
                        SELECT rowid FROM fts_{Config.KEYWORD_INDEX}
                        WHERE fts_{Config.KEYWORD_INDEX} MATCH ?
                    )
                    LIMIT ?
                """, (query, limit))
                return cur.fetchall()
            except sqlite3.Error as e:
                logger.error(f"Search error: {str(e)}")
                return []

    def _extract_keywords(self, text: str) -> str:
        words = [w.lower() for w in word_tokenize(text) if w.isalnum() and len(w) > 3]
        return ' '.join([w for w, _ in Counter(words).most_common(5)])

    def close(self):
        self.conn.close()