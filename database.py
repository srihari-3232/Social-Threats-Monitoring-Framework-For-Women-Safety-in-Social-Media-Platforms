import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

DB_NAME = "users.db"


def init_db():
    """Create the database and users table if not exists."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


def create_user(name, email, password):
    """Insert a new user into DB. Returns True if success, False if email exists."""

    hashed_pw = generate_password_hash(password)

    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
                       (name, email, hashed_pw))
        conn.commit()
        conn.close()

        return True  # successfully inserted

    except sqlite3.IntegrityError:
        return False  # email already exists


def validate_user(email, password):
    """Check user login credentials.
       Returns (True, name, user_id) if valid else (False, None, None)."""

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT id, name, password FROM users WHERE email=?", (email,))
    user = cursor.fetchone()

    conn.close()

    if user and check_password_hash(user[2], password):
        return True, user[1], user[0]  # valid login

    return False, None, None


def get_user_by_id(user_id):
    """Fetch a user using their ID."""

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT id, name, email FROM users WHERE id=?", (user_id,))
    user = cursor.fetchone()

    conn.close()

    return user


# Run when this file executes directly
if __name__ == "__main__":
    init_db()
    print("🔧 Database initialized successfully.")
