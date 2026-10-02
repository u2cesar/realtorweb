import os
import sqlite3
from werkzeug.security import check_password_hash, generate_password_hash

DB_PATH = os.environ.get("DATABASE_PATH", "app.db")


def get_db(db_path=None):
    if db_path is None:
        db_path = DB_PATH
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path=None):
    conn = get_db(db_path)
    with conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
    conn.close()


def create_user(username, password, db_path=None):
    username = username.strip()
    if not username or not password:
        raise ValueError("El usuario y la contraseña no pueden estar vacíos.")

    password_hash = generate_password_hash(password)
    conn = get_db(db_path)
    try:
        with conn:
            cursor = conn.execute(
                "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                (username, password_hash),
            )
            user_id = cursor.lastrowid
            return user_id
    except sqlite3.IntegrityError:
        raise ValueError("El nombre de usuario ya está registrado.")
    finally:
        conn.close()


def get_user_by_username(username, db_path=None):
    conn = get_db(db_path)
    cursor = conn.execute(
        "SELECT * FROM users WHERE LOWER(username) = LOWER(?)", (username.strip(),)
    )
    user = cursor.fetchone()
    conn.close()
    return user


def get_user_by_id(user_id, db_path=None):
    conn = get_db(db_path)
    cursor = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user


def verify_user(username, password, db_path=None):
    user = get_user_by_username(username, db_path)
    if user and check_password_hash(user["password_hash"], password):
        return user
    return None
