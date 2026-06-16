import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'student_complaint_app_secure_secret_key_129837192')
    
    # Detect Vercel environment
    IS_VERCEL = os.environ.get('VERCEL') == '1' or os.environ.get('VERCEL_ENV') is not None
    
    if IS_VERCEL:
        UPLOAD_FOLDER = '/tmp/uploads'
        SQLITE_DB_PATH = '/tmp/complaints.db'
    else:
        UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static', 'uploads')
        SQLITE_DB_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'complaints.db')
        
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx', 'txt'}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB limit

    DB_TYPE = 'sqlite'  # 'sqlite', 'mysql', or 'firebase'
    
    # MySQL (Optional - configuration template)
    MYSQL_HOST = 'localhost'
    MYSQL_USER = 'root'
    MYSQL_PASSWORD = ''
    MYSQL_DB = 'student_complaints'
