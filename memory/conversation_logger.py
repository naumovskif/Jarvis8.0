import sqlite3
import json
from datetime import datetime
from pathlib import Path
import sys
from threading import Lock

def get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent

BASE_DIR = get_base_dir()
DB_PATH = BASE_DIR / "memory" / "conversation_history.db"
_lock = Lock()

def _init_db() -> None:
    """Create database tables if they don't exist."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                user_text TEXT NOT NULL,
                jarvis_text TEXT NOT NULL,
                language TEXT DEFAULT 'en',
                memory_relevant BOOLEAN DEFAULT 0,
                created_date DATE DEFAULT CURRENT_DATE
            )
        """)
        
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_conversations_timestamp 
            ON conversations(timestamp)
        """)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS conversation_tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER NOT NULL,
                tag TEXT NOT NULL,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id),
                UNIQUE(conversation_id, tag)
            )
        """)
        
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_tags_tag 
            ON conversation_tags(tag)
        """)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS conversation_embeddings (
                conversation_id INTEGER PRIMARY KEY,
                embedding BLOB NOT NULL,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id)
            )
        """)
        
        conn.commit()

_init_db()

def log_conversation(
    user_text: str,
    jarvis_text: str,
    language: str = "en",
    memory_relevant: bool = False,
    tags: list = None
) -> int:
    """
    Store a conversation exchange in the database.
    
    Args:
        user_text: What the user said
        jarvis_text: What JARVIS responded
        language: Language code (en, fr, tr, etc.)
        memory_relevant: Whether this conversation contains memorable info
        tags: List of tags for categorization
    
    Returns:
        Conversation ID (int)
    """
    if not user_text or not jarvis_text:
        return -1
    
    user_text = user_text.strip()
    jarvis_text = jarvis_text.strip()
    
    if len(user_text) < 2:
        return -1
    
    with _lock:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            # Insert conversation
            cursor.execute("""
                INSERT INTO conversations 
                (user_text, jarvis_text, language, memory_relevant)
                VALUES (?, ?, ?, ?)
            """, (user_text, jarvis_text, language, memory_relevant))
            
            conversation_id = cursor.lastrowid
            
            # Add tags if provided
            if tags:
                for tag in tags:
                    if isinstance(tag, str) and tag.strip():
                        try:
                            cursor.execute("""
                                INSERT OR IGNORE INTO conversation_tags 
                                (conversation_id, tag)
                                VALUES (?, ?)
                            """, (conversation_id, tag.strip().lower()))
                        except sqlite3.IntegrityError:
                            pass
            
            conn.commit()
    
    return conversation_id

def get_conversation_history(limit: int = 100, offset: int = 0) -> list:
    """
    Get recent conversations.
    
    Args:
        limit: Number of conversations to return
        offset: Skip first N conversations
    
    Returns:
        List of conversations with metadata
    """
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, timestamp, user_text, jarvis_text, language, memory_relevant
            FROM conversations
            ORDER BY timestamp DESC
            LIMIT ? OFFSET ?
        """, (limit, offset))
        
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

def get_conversations_by_tag(tag: str, limit: int = 50) -> list:
    """
    Get conversations by tag.
    
    Args:
        tag: Tag to search for
        limit: Max results
    
    Returns:
        List of conversations with that tag
    """
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT DISTINCT c.id, c.timestamp, c.user_text, c.jarvis_text, c.language
            FROM conversations c
            JOIN conversation_tags ct ON c.id = ct.conversation_id
            WHERE ct.tag = ?
            ORDER BY c.timestamp DESC
            LIMIT ?
        """, (tag.lower(), limit))
        
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

def add_tags_to_conversation(conversation_id: int, tags: list) -> None:
    """
    Add tags to an existing conversation.
    
    Args:
        conversation_id: ID of conversation
        tags: List of tags to add
    """
    if not tags:
        return
    
    with _lock:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            for tag in tags:
                if isinstance(tag, str) and tag.strip():
                    try:
                        cursor.execute("""
                            INSERT OR IGNORE INTO conversation_tags
                            (conversation_id, tag)
                            VALUES (?, ?)
                        """, (conversation_id, tag.strip().lower()))
                    except sqlite3.IntegrityError:
                        pass
            
            conn.commit()

def mark_memory_relevant(conversation_id: int) -> None:
    """Mark a conversation as containing memorable information."""
    with _lock:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("""
                UPDATE conversations
                SET memory_relevant = 1
                WHERE id = ?
            """, (conversation_id,))
            conn.commit()

def get_conversation_count() -> int:
    """Get total number of conversations stored."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM conversations")
        return cursor.fetchone()[0]

def get_all_tags() -> list:
    """Get all unique tags in the database."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT tag FROM conversation_tags
            ORDER BY tag
        """)
        return [row[0] for row in cursor.fetchall()]

def store_embedding(conversation_id: int, embedding: bytes) -> None:
    """
    Store embedding vector for a conversation.
    
    Args:
        conversation_id: ID of conversation
        embedding: Embedding vector as bytes
    """
    with _lock:
        with sqlite3.connect(DB_PATH) as conn:
            try:
                conn.execute("""
                    INSERT OR REPLACE INTO conversation_embeddings
                    (conversation_id, embedding)
                    VALUES (?, ?)
                """, (conversation_id, embedding))
                conn.commit()
            except Exception as e:
                print(f"[ConvLogger] ⚠️ Failed to store embedding: {e}")

def get_embedding(conversation_id: int) -> bytes:
    """
    Retrieve embedding vector for a conversation.
    
    Args:
        conversation_id: ID of conversation
    
    Returns:
        Embedding bytes or None
    """
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT embedding FROM conversation_embeddings
            WHERE conversation_id = ?
        """, (conversation_id,))
        
        row = cursor.fetchone()
        return row[0] if row else None

def get_conversations_without_embeddings(limit: int = 100) -> list:
    """
    Get conversations that don't have embeddings yet.
    Used for batch processing during indexing.
    """
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT c.id, c.user_text, c.jarvis_text
            FROM conversations c
            LEFT JOIN conversation_embeddings e ON c.id = e.conversation_id
            WHERE e.conversation_id IS NULL
            ORDER BY c.timestamp DESC
            LIMIT ?
        """, (limit,))
        
        return [dict(row) for row in cursor.fetchall()]

def search_by_date(start_date: str, end_date: str) -> list:
    """
    Get conversations within a date range.
    
    Args:
        start_date: YYYY-MM-DD format
        end_date: YYYY-MM-DD format
    
    Returns:
        List of conversations in date range
    """
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, timestamp, user_text, jarvis_text
            FROM conversations
            WHERE DATE(timestamp) BETWEEN ? AND ?
            ORDER BY timestamp DESC
        """, (start_date, end_date))
        
        return [dict(row) for row in cursor.fetchall()]

def get_statistics() -> dict:
    """Get statistics about stored conversations."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM conversations")
        total = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM conversations WHERE memory_relevant = 1")
        relevant = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM conversation_embeddings")
        indexed = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT tag) FROM conversation_tags")
        unique_tags = cursor.fetchone()[0]
        
        return {
            "total_conversations": total,
            "memory_relevant": relevant,
            "indexed": indexed,
            "unique_tags": unique_tags,
            "db_size_kb": DB_PATH.stat().st_size / 1024 if DB_PATH.exists() else 0
        }

def cleanup_old_conversations(days: int = 365) -> int:
    """
    Archive/delete conversations older than N days.
    
    Args:
        days: Keep conversations from last N days
    
    Returns:
        Number of conversations deleted
    """
    with _lock:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            # First delete embeddings for old conversations
            cursor.execute("""
                DELETE FROM conversation_embeddings
                WHERE conversation_id IN (
                    SELECT id FROM conversations
                    WHERE DATE(timestamp) < DATE('now', ? || ' days')
                )
            """, (f"-{days}",))
            
            # Delete tags
            cursor.execute("""
                DELETE FROM conversation_tags
                WHERE conversation_id IN (
                    SELECT id FROM conversations
                    WHERE DATE(timestamp) < DATE('now', ? || ' days')
                )
            """, (f"-{days}",))
            
            # Finally delete conversations
            cursor.execute("""
                DELETE FROM conversations
                WHERE DATE(timestamp) < DATE('now', ? || ' days')
            """, (f"-{days}",))
            
            deleted = cursor.rowcount
            conn.commit()
    
    return deleted
