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
        self.table_name = Config.KEYWORD_TABLE_NAME
        # The fix is here: allow the connection to be used across threads
        self.conn = sqlite3.connect(Config.KEYWORD_DB, check_same_thread=False)
        self._init_db()
    
    def _init_db(self):
        with closing(self.conn.cursor()) as cur:
            logger.info(f"Recreating keyword database schema for table: {self.table_name}")
            cur.execute(f"DROP TABLE IF EXISTS {self.table_name}")
            cur.execute(f"DROP TABLE IF EXISTS fts_{self.table_name}")

            cur.execute(f"""
                CREATE TABLE {self.table_name} (
                    rowid INTEGER PRIMARY KEY,
                    id TEXT UNIQUE NOT NULL,
                    text TEXT NOT NULL,
                    pdf_name TEXT NOT NULL,
                    page INTEGER NOT NULL,
                    keywords TEXT NOT NULL
                )
            """)
            
            cur.execute(f"""
                CREATE VIRTUAL TABLE fts_{self.table_name} USING fts5(
                    keywords,
                    content='{self.table_name}',
                    content_rowid='rowid',
                    tokenize='porter'
                )
            """)
            
            cur.execute(f"""
                CREATE TRIGGER {self.table_name}_ai AFTER INSERT ON {self.table_name}
                BEGIN
                    INSERT INTO fts_{self.table_name}(rowid, keywords)
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
                        INSERT INTO {self.table_name}
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
                    FROM {self.table_name} k
                    WHERE k.rowid IN (
                        SELECT rowid FROM fts_{self.table_name}
                        WHERE fts_{self.table_name} MATCH ?
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
