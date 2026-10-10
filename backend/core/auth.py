import sqlite3
import hashlib
import os
import secrets
import json
import urllib.request
import urllib.error
from pathlib import Path
from dotenv import load_dotenv

# Ensure environment variables are loaded
load_dotenv(Path(__file__).parent.parent / '.env')

# Use a local database file in the backend root
DB_PATH = Path(__file__).parent.parent / "users.db"

def init_db():
    """Initializes the SQLite database, creates tables if needed, and applies migrations."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            provider TEXT DEFAULT 'email',
            picture TEXT DEFAULT ''
        )
    ''')
    
    # Safe migration for existing databases missing new columns
    cursor.execute("PRAGMA table_info(users)")
    columns = [col[1] for col in cursor.fetchall()]
    if "provider" not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN provider TEXT DEFAULT 'email'")
    if "picture" not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN picture TEXT DEFAULT ''")

    conn.commit()
    conn.close()
    
    # Initialize history and memory tables
    from core.history_memory import init_db_tables
    init_db_tables()

def hash_password(password: str, salt: str) -> str:
    """Hashes a password with the given salt using SHA-256."""
    return hashlib.sha256((password + salt).encode('utf-8')).hexdigest()

def register_user(name: str, email: str, password: str):
    """Registers a new user in the database using email and password."""
    name = (name or "").strip()
    email = (email or "").strip().lower()
    
    if not name or not email or not password:
        return {"status": "error", "message": "All fields (name, email, password) are required."}
    if "@" not in email or "." not in email:
        return {"status": "error", "message": "Please enter a valid email address."}
    if len(password) < 6:
        return {"status": "error", "message": "Password must be at least 6 characters long."}

    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Check if email exists
        cursor.execute("SELECT id, provider FROM users WHERE email = ?", (email,))
        existing = cursor.fetchone()
        if existing:
            if existing["provider"] == "google":
                return {
                    "status": "error",
                    "message": "This email is registered with Google. Please sign in with Google."
                }
            return {"status": "error", "message": "Email already exists. Please sign in instead."}
        
        # Generate salt and hash
        salt = secrets.token_hex(16)
        password_hash = hash_password(password, salt)
        
        cursor.execute(
            "INSERT INTO users (name, email, password_hash, salt, provider, picture) VALUES (?, ?, ?, ?, ?, ?)",
            (name, email, password_hash, salt, "email", "")
        )
        user_id = cursor.lastrowid
        conn.commit()
        
        return {
            "status": "success",
            "message": "User registered successfully.",
            "id": user_id,
            "name": name,
            "email": email,
            "picture": "",
            "provider": "email"
        }
    except Exception as e:
        return {"status": "error", "message": f"Registration failed: {str(e)}"}
    finally:
        conn.close()

def authenticate_user(email: str, password: str):
    """Authenticates a user via email and password."""
    email = (email or "").strip().lower()
    if not email or not password:
        return {"status": "error", "message": "Email and password are required."}

    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, name, email, password_hash, salt, provider, picture FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        
        if user:
            # Verify password
            provided_hash = hash_password(password, user['salt'])
            if provided_hash == user['password_hash']:
                return {
                    "status": "success",
                    "id": user['id'],
                    "name": user['name'],
                    "email": user['email'],
                    "picture": user['picture'] if 'picture' in user.keys() else '',
                    "provider": user['provider'] if 'provider' in user.keys() else 'email'
                }
            elif 'provider' in user.keys() and user['provider'] == 'google':
                return {
                    "status": "error",
                    "message": "This account was created with Google Sign-In. Please sign in with Google."
                }
        
        return {"status": "error", "message": "Invalid email or password."}
    except Exception as e:
        return {"status": "error", "message": f"Authentication failed: {str(e)}"}
    finally:
        conn.close()

def verify_google_credential(credential: str):
    """
    Verifies a Google ID token credential.
    Uses google-auth if available, falling back to Google's tokeninfo API.
    """
    expected_client_id = os.getenv("GOOGLE_CLIENT_ID", "").strip() or None

    # First attempt: official google-auth library if available
    try:
        from google.oauth2 import id_token
        from google.auth.transport import requests as google_requests
        idinfo = id_token.verify_oauth2_token(
            credential,
            google_requests.Request(),
            audience=expected_client_id
        )
        return {"status": "success", "payload": idinfo}
    except Exception as ga_err:
        pass

    # Second attempt: Google TokenInfo REST API endpoint
    try:
        url = f"https://oauth2.googleapis.com/tokeninfo?id_token={credential}"
        req = urllib.request.Request(url, headers={"User-Agent": "ALIAS-Assistant/2.0"})
        with urllib.request.urlopen(req, timeout=10) as response:
            payload = json.loads(response.read().decode('utf-8'))
        
        # Verify audience if client ID is set
        if expected_client_id and payload.get("aud") != expected_client_id:
            return {
                "status": "error",
                "message": f"Google token audience mismatch. Expected: {expected_client_id}, got: {payload.get('aud')}"
            }
            
        return {"status": "success", "payload": payload}
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode('utf-8', errors='ignore')
        return {"status": "error", "message": f"Google token validation failed: {err_msg}"}
    except Exception as e:
        return {"status": "error", "message": f"Failed to verify Google token: {str(e)}"}

def authenticate_google_user(credential: str):
    """
    Authenticates or registers a user via a Google ID token.
    Automatically links or creates the local user profile.
    """
    if not credential:
        return {"status": "error", "message": "Google credential token is missing."}

    verify_res = verify_google_credential(credential)
    if verify_res.get("status") != "success":
        return verify_res

    payload = verify_res.get("payload", {})
    email = payload.get("email", "").strip().lower()
    name = payload.get("name") or (email.split("@")[0] if email else "Google User")
    picture = payload.get("picture", "")
    google_id = payload.get("sub", "")
    email_verified = payload.get("email_verified")

    if not email:
        return {"status": "error", "message": "No email address found in Google account."}

    # Verify that the email is verified by Google
    if email_verified not in [True, "true", "True", 1, "1"]:
        return {"status": "error", "message": "Google email address is not verified."}

    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT id, name, email, provider, picture FROM users WHERE email = ?", (email,))
        existing_user = cursor.fetchone()

        if existing_user:
            user_id = existing_user["id"]
            user_name = existing_user["name"] or name
            user_picture = existing_user["picture"] if existing_user["picture"] else picture
            
            # Update user info if name or picture is updated
            updates = []
            params = []
            if picture and not existing_user["picture"]:
                updates.append("picture = ?")
                params.append(picture)
            if not existing_user["name"] and name:
                updates.append("name = ?")
                params.append(name)
            if updates:
                params.append(user_id)
                cursor.execute(f"UPDATE users SET {', '.join(updates)} WHERE id = ?", tuple(params))
                conn.commit()

            return {
                "status": "success",
                "message": "Signed in with Google successfully.",
                "id": user_id,
                "name": user_name,
                "email": existing_user["email"],
                "picture": user_picture,
                "provider": existing_user["provider"] or "google"
            }
        else:
            # Register new user created via Google
            salt = secrets.token_hex(16)
            dummy_hash = hash_password(f"GOOGLE_AUTH_{google_id}_{secrets.token_hex(16)}", salt)
            cursor.execute(
                "INSERT INTO users (name, email, password_hash, salt, provider, picture) VALUES (?, ?, ?, ?, ?, ?)",
                (name, email, dummy_hash, salt, "google", picture)
            )
            user_id = cursor.lastrowid
            conn.commit()

            return {
                "status": "success",
                "message": "Google account registered and logged in successfully.",
                "id": user_id,
                "name": name,
                "email": email,
                "picture": picture,
                "provider": "google"
            }
    except Exception as e:
        return {"status": "error", "message": f"Database error during Google login: {str(e)}"}
    finally:
        conn.close()

def authenticate_firebase_user(email: str, name: str = None, picture: str = '', uid: str = '', provider: str = 'firebase', id_token: str = None):
    """
    Authenticates or registers a user verified through Firebase Auth.
    Syncs the user with the local SQLite database so conversations, histories, and memories work seamlessly.
    """
    email = (email or "").strip().lower()
    if not email:
        return {"status": "error", "message": "Email is required for Firebase authentication."}

    name = (name or "").strip() or (email.split("@")[0] if email else "User")
    picture = picture or ""
    provider_name = provider or "firebase"

    # Verify ID token if provided and possible
    if id_token:
        try:
            verify_res = verify_google_credential(id_token)
            if verify_res.get("status") == "success":
                token_email = verify_res.get("payload", {}).get("email", "").strip().lower()
                if token_email and token_email != email:
                    return {"status": "error", "message": "Firebase token email mismatch."}
        except Exception:
            pass

    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT id, name, email, provider, picture FROM users WHERE email = ?", (email,))
        existing_user = cursor.fetchone()

        if existing_user:
            user_id = existing_user["id"]
            user_name = existing_user["name"] or name
            user_picture = existing_user["picture"] if existing_user["picture"] else picture

            updates = []
            params = []
            if picture and not existing_user["picture"]:
                updates.append("picture = ?")
                params.append(picture)
            if not existing_user["name"] and name:
                updates.append("name = ?")
                params.append(name)
            if updates:
                params.append(user_id)
                cursor.execute(f"UPDATE users SET {', '.join(updates)} WHERE id = ?", tuple(params))
                conn.commit()

            return {
                "status": "success",
                "message": "Signed in with Firebase successfully.",
                "id": user_id,
                "name": user_name,
                "email": existing_user["email"],
                "picture": user_picture,
                "provider": existing_user["provider"] or provider_name
            }
        else:
            # Create user linked to Firebase
            salt = secrets.token_hex(16)
            dummy_hash = hash_password(f"FIREBASE_{uid or secrets.token_hex(16)}", salt)
            cursor.execute(
                "INSERT INTO users (name, email, password_hash, salt, provider, picture) VALUES (?, ?, ?, ?, ?, ?)",
                (name, email, dummy_hash, salt, provider_name, picture)
            )
            user_id = cursor.lastrowid
            conn.commit()

            return {
                "status": "success",
                "message": "Firebase account synced and registered successfully.",
                "id": user_id,
                "name": name,
                "email": email,
                "picture": picture,
                "provider": provider_name
            }
    except Exception as e:
        return {"status": "error", "message": f"Database error during Firebase login: {str(e)}"}
    finally:
        conn.close()

def get_user_by_email(email: str):
    """Fetches user record by email."""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, email, provider, picture FROM users WHERE email = ?", ((email or "").strip().lower(),))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None
    except Exception:
        return None
    finally:
        conn.close()

# Initialize DB when module loads
init_db()
