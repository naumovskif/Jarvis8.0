"""
SQLite-based memory system for JARVIS.
Replaces JSON with efficient database with indexing and full-text search.
"""

import sqlite3
import json
import threading
from pathlib import Path
from typing import Optional, List, Tuple, Dict, Any
from datetime import datetime, timedelta
import sys
import hashlib


def get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent


BASE_DIR = get_base_dir()
MEMORY_DB_PATH = BASE_DIR / "memory" / "jarvis_memory.db"
MEMORY_DB_PATH.parent.mkdir(parents=True, exist_ok=True)


class MemoryDatabase:
    """
    SQLite database for persistent memory with:
    - Efficient indexing
    - Full-text search
    - Automatic cleanup
    - Transaction support
    - Thread safety
    """

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or MEMORY_DB_PATH
        self._lock = threading.Lock()
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Get thread-local database connection."""
        conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        """Initialize database schema."""
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Main conversations table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    user_text TEXT NOT NULL,
                    jarvis_response TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    user_tokens INTEGER DEFAULT 0,
                    response_tokens INTEGER DEFAULT 0,
                    model TEXT,
                    embedding_hash TEXT UNIQUE
                )
            """)
            
            # Memory entries (facts, preferences, projects, relationships)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS memory_entries (
                    id TEXT PRIMARY KEY,
                    category TEXT NOT NULL,
                    key TEXT NOT NULL,
                    value TEXT NOT NULL,
                    embedding TEXT,
                    updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    confidence REAL DEFAULT 1.0,
                    source_conversation_id TEXT
                )
            """)
            
            # Embeddings cache
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS embedding_cache (
                    hash TEXT PRIMARY KEY,
                    text TEXT NOT NULL,
                    embedding TEXT NOT NULL,
                    created DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Indexes for performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_conv_timestamp 
                ON conversations(timestamp DESC)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_conv_user_text 
                ON conversations(user_text)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_memory_category 
                ON memory_entries(category)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_memory_key 
                ON memory_entries(category, key)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_memory_updated 
                ON memory_entries(updated DESC)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_embedding_hash 
                ON embedding_cache(hash)
            """)
            
            # Full-text search table
            cursor.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS fts_conversations 
                USING fts5(user_text, jarvis_response)
            """)
            
            conn.commit()
            conn.close()
            print("[MemoryDB] ✅ Database initialized")

    def add_conversation(
        self,
        user_text: str,
        jarvis_response: str,
        model: str = "unknown",
        embedding_hash: Optional[str] = None,
    ) -> str:
        """Add conversation to database. Returns conversation ID."""
        conv_id = hashlib.md5(
            f"{user_text}{jarvis_response}{datetime.now().isoformat()}".encode()
        ).hexdigest()
        
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            try:
                cursor.execute("""
                    INSERT INTO conversations 
                    (id, user_text, jarvis_response, model, embedding_hash)
                    VALUES (?, ?, ?, ?, ?)
                """, (conv_id, user_text, jarvis_response, model, embedding_hash))
                
                # Also add to FTS
                cursor.execute("""
                    INSERT INTO fts_conversations (user_text, jarvis_response)
                    VALUES (?, ?)
                """, (user_text, jarvis_response))
                
                conn.commit()
            except sqlite3.IntegrityError:
                pass
            finally:
                conn.close()
        
        return conv_id

    def get_conversations(
        self,
        limit: int = 100,
        days: Optional[int] = None,
        search_text: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieve conversations with optional filtering."""
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            try:
                if search_text:
                    # Full-text search
                    cursor.execute("""
                        SELECT c.* FROM conversations c
                        INNER JOIN fts_conversations fts ON c.rowid = fts.rowid
                        WHERE fts MATCH ?
                        ORDER BY c.timestamp DESC
                        LIMIT ?
                    """, (f'"{search_text}"', limit))
                elif days:
                    cutoff = datetime.now() - timedelta(days=days)
                    cursor.execute("""
                        SELECT * FROM conversations
                        WHERE timestamp > ?
                        ORDER BY timestamp DESC
                        LIMIT ?
                    """, (cutoff.isoformat(), limit))
                else:
                    cursor.execute("""
                        SELECT * FROM conversations
                        ORDER BY timestamp DESC
                        LIMIT ?
                    """, (limit,))
                
                return [dict(row) for row in cursor.fetchall()]
            finally:
                conn.close()

    def add_memory_entry(
        self,
        category: str,
        key: str,
        value: str,
        source_id: Optional[str] = None,
        confidence: float = 1.0,
    ) -> None:
        """Add or update a memory entry."""
        entry_id = f"{category}:{key}"
        
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            try:
                cursor.execute("""
                    INSERT OR REPLACE INTO memory_entries
                    (id, category, key, value, source_conversation_id, confidence)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (entry_id, category, key, value, source_id, confidence))
                
                conn.commit()
            finally:
                conn.close()

    def get_memory_entries(
        self,
        category: Optional[str] = None,
        days: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieve memory entries with optional filtering."""
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            try:
                if category and days:
                    cutoff = datetime.now() - timedelta(days=days)
                    cursor.execute("""
                        SELECT * FROM memory_entries
                        WHERE category = ? AND updated > ?
                        ORDER BY updated DESC
                    """, (category, cutoff.isoformat()))
                elif category:
                    cursor.execute("""
                        SELECT * FROM memory_entries
                        WHERE category = ?
                        ORDER BY updated DESC
                    """, (category,))
                elif days:
                    cutoff = datetime.now() - timedelta(days=days)
                    cursor.execute("""
                        SELECT * FROM memory_entries
                        WHERE updated > ?
                        ORDER BY updated DESC
                    """, (cutoff.isoformat(),))
                else:
                    cursor.execute("""
                        SELECT * FROM memory_entries
                        ORDER BY updated DESC
                    """)
                
                return [dict(row) for row in cursor.fetchall()]
            finally:
                conn.close()

    def cache_embedding(self, text: str, embedding: List[float]) -> None:
        """Cache an embedding."""
        hash_key = hashlib.md5(text.encode()).hexdigest()
        embedding_json = json.dumps(embedding)
        
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            try:
                cursor.execute("""
                    INSERT OR IGNORE INTO embedding_cache (hash, text, embedding)
                    VALUES (?, ?, ?)
                """, (hash_key, text, embedding_json))
                
                conn.commit()
            finally:
                conn.close()

    def get_embedding(self, text: str) -> Optional[List[float]]:
        """Retrieve cached embedding."""
        hash_key = hashlib.md5(text.encode()).hexdigest()
        
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            try:
                cursor.execute("""
                    SELECT embedding FROM embedding_cache WHERE hash = ?
                """, (hash_key,))
                
                row = cursor.fetchone()
                if row:
                    return json.loads(row['embedding'])
                return None
            finally:
                conn.close()

    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            try:
                cursor.execute("SELECT COUNT(*) as count FROM conversations")
                conv_count = cursor.fetchone()['count']
                
                cursor.execute("SELECT COUNT(*) as count FROM memory_entries")
                mem_count = cursor.fetchone()['count']
                
                cursor.execute("SELECT COUNT(*) as count FROM embedding_cache")
                emb_count = cursor.fetchone()['count']
                
                db_size = self.db_path.stat().st_size / (1024 * 1024) if self.db_path.exists() else 0
                
                return {
                    "conversations": conv_count,
                    "memory_entries": mem_count,
                    "embeddings_cached": emb_count,
                    "db_size_mb": round(db_size, 2),
                }
            finally:
                conn.close()

    def cleanup_old_conversations(self, days: int = 365) -> int:
        """Delete conversations older than N days. Returns count deleted."""
        cutoff = datetime.now() - timedelta(days=days)
        
        with self._lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            try:
                cursor.execute("""
                    DELETE FROM conversations WHERE timestamp < ?
                """, (cutoff.isoformat(),))
                
                deleted = cursor.rowcount
                conn.commit()
                return deleted
            finally:
                conn.close()

    def vacuum(self) -> None:
        """Optimize database."""
        with self._lock:
            conn = self._get_connection()
            conn.execute("VACUUM")
            conn.close()


# Global instance
_memory_db: Optional[MemoryDatabase] = None
_db_lock = threading.Lock()


def get_memory_db() -> MemoryDatabase:
    """Get or create global memory database."""
    global _memory_db
    if _memory_db is None:
        with _db_lock:
            if _memory_db is None:
                _memory_db = MemoryDatabase()
    return _memory_db
