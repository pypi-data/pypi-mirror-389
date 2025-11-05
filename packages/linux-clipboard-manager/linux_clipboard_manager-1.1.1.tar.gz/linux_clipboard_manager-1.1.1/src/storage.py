"""
Storage engine for clipboard history using SQLite
"""
import sqlite3
import hashlib
import json
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from pathlib import Path


class ClipboardStorage:
    """Manages clipboard history storage with SQLite"""
    
    def __init__(self, db_path: str):
        """Initialize storage
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.create_tables()
    
    def create_tables(self):
        """Create database tables if they don't exist"""
        cursor = self.conn.cursor()
        
        # Main clipboard history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS clipboard_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content_hash TEXT UNIQUE NOT NULL,
                content TEXT NOT NULL,
                content_type TEXT,
                app_name TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_favorite INTEGER DEFAULT 0,
                use_count INTEGER DEFAULT 0,
                metadata TEXT
            )
        """)
        
        # Index for faster searches
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_timestamp 
            ON clipboard_history(timestamp DESC)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_content_hash 
            ON clipboard_history(content_hash)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_content_type 
            ON clipboard_history(content_type)
        """)
        
        # Full-text search virtual table
        cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS clipboard_fts 
            USING fts5(content, content=clipboard_history, content_rowid=id)
        """)
        
        # Triggers to keep FTS table in sync
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS clipboard_ai AFTER INSERT ON clipboard_history BEGIN
                INSERT INTO clipboard_fts(rowid, content) VALUES (new.id, new.content);
            END
        """)
        
        cursor.execute("""
            CREATE TRIGGER IF NOT EXISTS clipboard_ad AFTER DELETE ON clipboard_history BEGIN
                DELETE FROM clipboard_fts WHERE rowid = old.id;
            END
        """)
        
        self.conn.commit()
    
    def save_clip(self, content: str, content_type: str = None, 
                  app_name: str = None, metadata: Dict = None) -> Optional[int]:
        """Save clipboard content
        
        Args:
            content: Clipboard content
            content_type: Type of content (url, email, code, text, image)
            app_name: Name of application where content was copied
            metadata: Additional metadata as dict
            
        Returns:
            Row ID if saved, None if duplicate
        """
        if not content or len(content.strip()) == 0:
            return None
        
        content_hash = self._hash_content(content)
        cursor = self.conn.cursor()
        
        try:
            # Check if content already exists
            cursor.execute(
                "SELECT id, use_count FROM clipboard_history WHERE content_hash = ?",
                (content_hash,)
            )
            existing = cursor.fetchone()
            
            if existing:
                # Update use count and timestamp
                cursor.execute("""
                    UPDATE clipboard_history 
                    SET use_count = use_count + 1, 
                        timestamp = CURRENT_TIMESTAMP 
                    WHERE id = ?
                """, (existing['id'],))
                self.conn.commit()
                return existing['id']
            
            # Insert new entry
            metadata_json = json.dumps(metadata) if metadata else None
            cursor.execute("""
                INSERT INTO clipboard_history 
                (content_hash, content, content_type, app_name, metadata)
                VALUES (?, ?, ?, ?, ?)
            """, (content_hash, content, content_type, app_name, metadata_json))
            
            self.conn.commit()
            return cursor.lastrowid
            
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return None
    
    def get_history(self, limit: int = 100, offset: int = 0, 
                    content_type: str = None) -> List[Dict]:
        """Get clipboard history
        
        Args:
            limit: Maximum number of entries to return
            offset: Number of entries to skip
            content_type: Filter by content type
            
        Returns:
            List of clipboard entries
        """
        cursor = self.conn.cursor()
        
        query = "SELECT * FROM clipboard_history"
        params = []
        
        if content_type:
            query += " WHERE content_type = ?"
            params.append(content_type)
        
        query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]
    
    def search(self, query: str, limit: int = 50) -> List[Dict]:
        """Search clipboard history
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of matching clipboard entries
        """
        cursor = self.conn.cursor()
        
        # Use FTS for full-text search
        cursor.execute("""
            SELECT h.* FROM clipboard_history h
            INNER JOIN clipboard_fts fts ON h.id = fts.rowid
            WHERE content MATCH ?
            ORDER BY h.timestamp DESC
            LIMIT ?
        """, (query, limit))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_favorites(self) -> List[Dict]:
        """Get favorite clipboard entries"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM clipboard_history 
            WHERE is_favorite = 1 
            ORDER BY timestamp DESC
        """)
        return [dict(row) for row in cursor.fetchall()]
    
    def toggle_favorite(self, clip_id: int) -> bool:
        """Toggle favorite status
        
        Args:
            clip_id: Clipboard entry ID
            
        Returns:
            New favorite status
        """
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT is_favorite FROM clipboard_history WHERE id = ?",
            (clip_id,)
        )
        row = cursor.fetchone()
        
        if row:
            new_status = 0 if row['is_favorite'] else 1
            cursor.execute(
                "UPDATE clipboard_history SET is_favorite = ? WHERE id = ?",
                (new_status, clip_id)
            )
            self.conn.commit()
            return bool(new_status)
        
        return False
    
    def delete_clip(self, clip_id: int):
        """Delete clipboard entry
        
        Args:
            clip_id: Clipboard entry ID
        """
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM clipboard_history WHERE id = ?", (clip_id,))
        self.conn.commit()
    
    def clear_all(self):
        """Clear all clipboard entries"""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM clipboard_history")
        self.conn.commit()
    
    def cleanup_old_entries(self, max_entries: int = 1000):
        """Remove old entries to maintain size limit
        
        Args:
            max_entries: Maximum number of entries to keep
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            DELETE FROM clipboard_history 
            WHERE id NOT IN (
                SELECT id FROM clipboard_history 
                WHERE is_favorite = 1
                UNION
                SELECT id FROM (
                    SELECT id FROM clipboard_history 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                )
            )
        """, (max_entries,))
        self.conn.commit()
    
    def get_stats(self) -> Dict:
        """Get storage statistics"""
        cursor = self.conn.cursor()
        
        cursor.execute("SELECT COUNT(*) as total FROM clipboard_history")
        total = cursor.fetchone()['total']
        
        cursor.execute("SELECT COUNT(*) as favorites FROM clipboard_history WHERE is_favorite = 1")
        favorites = cursor.fetchone()['favorites']
        
        cursor.execute("SELECT content_type, COUNT(*) as count FROM clipboard_history GROUP BY content_type")
        by_type = {row['content_type']: row['count'] for row in cursor.fetchall()}
        
        return {
            'total': total,
            'favorites': favorites,
            'by_type': by_type
        }
    
    def _hash_content(self, content: str) -> str:
        """Generate hash for content deduplication"""
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()

