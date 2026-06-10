import sqlite3
import uuid
import os
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "users.db"

def init_db_tables():
    """Initializes history and memory tables in the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Conversations table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')
    
    # 2. Messages table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
        )
    ''')
    
    # 3. Memories table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            fact TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')
    
    # Indexes for performance
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_conversations_user ON conversations(user_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(conversation_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_memories_user ON memories(user_id)')
    
    conn.commit()
    conn.close()

def get_user_id_by_email(email: str) -> int:
    """Helper to get user ID from email."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

def create_conversation(user_email: str, title: str = None) -> str:
    """Creates a new conversation for the user and returns its ID."""
    user_id = get_user_id_by_email(user_email)
    if not user_id:
        raise ValueError(f"User not found for email: {user_email}")
        
    conv_id = str(uuid.uuid4())
    if not title:
        title = "New Chat"
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO conversations (id, user_id, title) VALUES (?, ?, ?)",
        (conv_id, user_id, title)
    )
    conn.commit()
    conn.close()
    return conv_id

def add_message(conversation_id: str, role: str, content: str):
    """Saves a message to a conversation and updates its updated_at timestamp."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Insert message
    cursor.execute(
        "INSERT INTO messages (conversation_id, role, content) VALUES (?, ?, ?)",
        (conversation_id, role, content)
    )
    
    # Update conversation's updated_at timestamp
    cursor.execute(
        "UPDATE conversations SET updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (conversation_id,)
    )
    
    conn.commit()
    conn.close()

def get_conversations(user_email: str) -> list:
    """Retrieves all conversations for a user, ordered by updated_at DESC."""
    user_id = get_user_id_by_email(user_email)
    if not user_id:
        return []
        
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, title, created_at, updated_at FROM conversations WHERE user_id = ? ORDER BY updated_at DESC",
        (user_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_messages(conversation_id: str) -> list:
    """Retrieves all messages for a conversation, ordered by created_at ASC."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        "SELECT role, content, created_at FROM messages WHERE conversation_id = ? ORDER BY id ASC",
        (conversation_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def delete_conversation(conversation_id: str):
    """Deletes a conversation and cascades to delete all its messages."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Enable foreign keys for cascade delete support
    cursor.execute("PRAGMA foreign_keys = ON")
    cursor.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
    conn.commit()
    conn.close()

def rename_conversation(conversation_id: str, title: str):
    """Renames a conversation."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE conversations SET title = ? WHERE id = ?", (title, conversation_id))
    conn.commit()
    conn.close()

# --- MEMORY CRUD ---

def get_memories(user_email: str) -> list:
    """Retrieves all memories for a user."""
    user_id = get_user_id_by_email(user_email)
    if not user_id:
        return []
        
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT id, fact, created_at FROM memories WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def add_memory(user_email: str, fact: str) -> int:
    """Adds a new fact to the user's memories."""
    user_id = get_user_id_by_email(user_email)
    if not user_id:
        raise ValueError(f"User not found for email: {user_email}")
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO memories (user_id, fact) VALUES (?, ?)", (user_id, fact))
    memory_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return memory_id

def update_memory(user_email: str, memory_id: int, new_fact: str):
    """Updates an existing memory."""
    user_id = get_user_id_by_email(user_email)
    if not user_id:
        return
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE memories SET fact = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ? AND user_id = ?",
        (new_fact, memory_id, user_id)
    )
    conn.commit()
    conn.close()

def delete_memory(user_email: str, memory_id: int):
    """Deletes a memory."""
    user_id = get_user_id_by_email(user_email)
    if not user_id:
        return
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM memories WHERE id = ? AND user_id = ?", (memory_id, user_id))
    conn.commit()
    conn.close()

# --- SEMANTIC SEARCH OF PAST CONVERSATIONS ---

def extract_search_keywords(text: str) -> list:
    """Extracts search keywords from natural language queries, filtering out common stop words."""
    clean_text = "".join(c if c.isalnum() or c.isspace() else " " for c in text.lower())
    words = clean_text.split()
    stop_words = {
        "what", "is", "this", "the", "a", "an", "we", "did", "you", "about", "to", 
        "in", "on", "for", "me", "my", "our", "your", "us", "how", "why", "where",
        "when", "who", "whom", "whose", "which", "that", "these", "those", "then",
        "there", "here", "with", "from", "by", "at", "of", "and", "or", "but", "if",
        "can", "could", "would", "should", "do", "does", "get", "go", "discuss",
        "discussed", "talk", "talked", "tell", "told", "find", "search", "recall"
    }
    keywords = [w for w in words if w not in stop_words and len(w) > 2]
    return keywords

def search_past_conversations(user_email: str, keywords: list, current_conv_id: str = None) -> list:
    """Queries the messages table for historical messages matching key terms."""
    if not keywords:
        return []
    
    user_id = get_user_id_by_email(user_email)
    if not user_id:
        return []
        
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    query = """
        SELECT m.content, m.role, m.created_at, c.title 
        FROM messages m
        JOIN conversations c ON m.conversation_id = c.id
        WHERE c.user_id = ?
    """
    params = [user_id]
    
    if current_conv_id:
        query += " AND c.id != ?"
        params.append(current_conv_id)
        
    # Build OR clauses for each keyword
    keyword_clauses = []
    for kw in keywords:
        keyword_clauses.append("m.content LIKE ?")
        params.append(f"%{kw}%")
        
    if keyword_clauses:
        query += " AND (" + " OR ".join(keyword_clauses) + ")"
        
    query += " ORDER BY m.created_at DESC LIMIT 10"
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(r) for r in rows]
