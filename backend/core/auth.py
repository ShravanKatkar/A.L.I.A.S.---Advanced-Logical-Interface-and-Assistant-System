import sqlite3
import hashlib
import os
import secrets
from pathlib import Path

# Use a local database file in the backend root
DB_PATH = Path(__file__).parent.parent / "users.db"

def init_db():
    """Initializes the SQLite database and creates the users table if it doesn't exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()
    
    # Initialize history and memory tables
    from core.history_memory import init_db_tables
    init_db_tables()

def hash_password(password: str, salt: str) -> str:
    """Hashes a password with the given salt using SHA-256."""
    return hashlib.sha256((password + salt).encode('utf-8')).hexdigest()

def register_user(name: str, email: str, password: str):
    """Registers a new user in the database."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if email exists
        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        if cursor.fetchone():
            return {"status": "error", "message": "Email already exists."}
        
        # Generate salt and hash
        salt = secrets.token_hex(16)
        password_hash = hash_password(password, salt)
        
        cursor.execute(
            "INSERT INTO users (name, email, password_hash, salt) VALUES (?, ?, ?, ?)",
            (name, email, password_hash, salt)
        )
        user_id = cursor.lastrowid
        conn.commit()
        
        return {"status": "success", "message": "User registered successfully.", "id": user_id, "name": name, "email": email}
    except Exception as e:
        return {"status": "error", "message": f"Registration failed: {str(e)}"}
    finally:
        conn.close()

def authenticate_user(email: str, password: str):
    """Authenticates a user and returns their details if successful."""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, name, email, password_hash, salt FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        
        if user:
            # Verify password
            provided_hash = hash_password(password, user['salt'])
            if provided_hash == user['password_hash']:
                return {
                    "status": "success",
                    "id": user['id'],
                    "name": user['name'],
                    "email": user['email']
                }
        
        return {"status": "error", "message": "Invalid email or password."}
    except Exception as e:
        return {"status": "error", "message": f"Authentication failed: {str(e)}"}
    finally:
        conn.close()

# Initialize DB when module loads
init_db()
