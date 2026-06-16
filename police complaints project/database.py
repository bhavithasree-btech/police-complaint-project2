import sqlite3
import os
import random
import string
from werkzeug.security import generate_password_hash
from config import Config

def get_db_connection():
    if Config.DB_TYPE == 'sqlite':
        # If on Vercel, copy the database file from the read-only directory to /tmp
        if Config.IS_VERCEL:
            db_dir = os.path.dirname(Config.SQLITE_DB_PATH)
            os.makedirs(db_dir, exist_ok=True)
            if not os.path.exists(Config.SQLITE_DB_PATH):
                src_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'complaints.db')
                if os.path.exists(src_path):
                    import shutil
                    try:
                        shutil.copy2(src_path, Config.SQLITE_DB_PATH)
                        print("SQLite database copied to /tmp successfully.")
                    except Exception as e:
                        print(f"Warning: Failed to copy SQLite db: {e}")
        
        conn = sqlite3.connect(Config.SQLITE_DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    else:
        # Placeholder/template for MySQL
        try:
            import pymysql
            conn = pymysql.connect(
                host=Config.MYSQL_HOST,
                user=Config.MYSQL_USER,
                password=Config.MYSQL_PASSWORD,
                db=Config.MYSQL_DB,
                cursorclass=pymysql.cursors.DictCursor
            )
            return conn
        except ImportError:
            # Fallback to sqlite if pymysql is missing
            conn = sqlite3.connect(Config.SQLITE_DB_PATH)
            conn.row_factory = sqlite3.Row
            return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        mobile TEXT,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'student',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Create complaints table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS complaints (
        id TEXT PRIMARY KEY,
        user_id INTEGER,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        category TEXT NOT NULL,
        anonymous INTEGER DEFAULT 0,
        file_path TEXT,
        status TEXT NOT NULL DEFAULT 'Submitted',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    ''')

    # Create comments table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        complaint_id TEXT NOT NULL,
        user_id INTEGER NOT NULL,
        comment_text TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (complaint_id) REFERENCES complaints(id),
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    ''')

    # Create notifications table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        complaint_id TEXT NOT NULL,
        message TEXT NOT NULL,
        read_status INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (complaint_id) REFERENCES complaints(id)
    )
    ''')

    # Insert default admin if not exists
    cursor.execute("SELECT * FROM users WHERE role = 'admin'")
    if not cursor.fetchone():
        admin_pass = generate_password_hash('admin123')
        cursor.execute(
            "INSERT INTO users (name, email, mobile, password_hash, role) VALUES (?, ?, ?, ?, ?)",
            ('System Administrator', 'admin@complaints.org', '9999999999', admin_pass, 'admin')
        )

    # Insert a couple of default demo student accounts for easier testing
    cursor.execute("SELECT * FROM users WHERE email = 'student@test.com'")
    if not cursor.fetchone():
        student_pass = generate_password_hash('student123')
        cursor.execute(
            "INSERT INTO users (name, email, mobile, password_hash, role) VALUES (?, ?, ?, ?, ?)",
            ('John Doe', 'student@test.com', '9876543210', student_pass, 'student')
        )

    conn.commit()
    conn.close()

def generate_complaint_id():
    # Format: COMP-YYYYMMDD-XXXX where XXXX is random letters/digits
    import datetime
    date_str = datetime.datetime.now().strftime("%Y%m%d")
    random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"COMP-{date_str}-{random_str}"
