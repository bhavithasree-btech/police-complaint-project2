import firebase_admin
from firebase_admin import credentials, firestore
import datetime
import random
import string
import os

# Global Firestore DB client
db = None

def init_firebase():
    global db
    # Check if firebase is already initialized to prevent errors on reload
    if not firebase_admin._apps:
        try:
            # Look for serviceAccountKey.json in the same directory as this script
            key_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "serviceAccountKey.json")
            cred = credentials.Certificate(key_path)
            firebase_admin.initialize_app(cred)
            print("Firebase Admin SDK initialized successfully.")
        except Exception as e:
            print(f"Warning: Could not initialize Firebase Admin SDK with serviceAccountKey.json: {e}")
            print("Falling back to application default credentials.")
            try:
                firebase_admin.initialize_app()
            except Exception as e2:
                print(f"Error: Could not initialize Firebase at all: {e2}")
    try:
        db = firestore.client()
        print("Firestore client created successfully.")
    except Exception as e:
        print(f"Error: Firebase Firestore Client could not be created. {e}")
        db = None

def _check_db():
    """Raises RuntimeError if the Firestore client is not available."""
    if db is None:
        raise RuntimeError(
            "Firebase Firestore is not connected. "
            "Check your serviceAccountKey.json and Firestore is enabled in the Firebase Console."
        )

def generate_complaint_id():
    date_str = datetime.datetime.now().strftime("%Y%m%d")
    random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"COMP-{date_str}-{random_str}"

# --- USER OPERATIONS ---

def create_user(name, email, mobile, password_hash, role='student'):
    """Creates a new user document in Firestore."""
    _check_db()
    user_ref = db.collection('users').document()
    user_data = {
        'id': user_ref.id,
        'name': name,
        'email': email,
        'mobile': mobile,
        'password_hash': password_hash,
        'role': role,
        'created_at': datetime.datetime.utcnow()
    }
    # Check if email exists
    existing = db.collection('users').where('email', '==', email).get()
    if existing:
        raise ValueError("Email already registered")
        
    user_ref.set(user_data)
    return user_data

def get_user_by_email(email):
    """Finds a user by email."""
    _check_db()
    users = db.collection('users').where('email', '==', email).limit(1).get()
    if users:
        return users[0].to_dict()
    return None

def get_user_by_id(user_id):
    """Finds a user by Firestore document ID."""
    _check_db()
    doc = db.collection('users').document(user_id).get()
    if doc.exists:
        return doc.to_dict()
    return None

def update_user_profile(user_id, name, mobile):
    """Updates user profile data."""
    _check_db()
    db.collection('users').document(user_id).update({
        'name': name,
        'mobile': mobile
    })

# --- COMPLAINT OPERATIONS ---

def create_complaint(title, description, category, anonymous, file_path, user_id=None):
    """Creates a new complaint document in Firestore."""
    _check_db()
    complaint_id = generate_complaint_id()
    complaint_ref = db.collection('complaints').document(complaint_id)
    
    complaint_data = {
        'id': complaint_id,
        'user_id': user_id,  # Will be None if anonymous
        'title': title,
        'description': description,
        'category': category,
        'anonymous': anonymous,
        'file_path': file_path,
        'status': 'Submitted',
        'created_at': datetime.datetime.utcnow(),
        'updated_at': datetime.datetime.utcnow()
    }
    complaint_ref.set(complaint_data)
    return complaint_id

def get_complaint_by_id(complaint_id):
    """Fetches a specific complaint."""
    doc = db.collection('complaints').document(complaint_id).get()
    if doc.exists:
        return doc.to_dict()
    return None

def get_all_complaints():
    """Fetches all complaints (with user details joined if not anonymous)."""
    _check_db()
    # Note: avoid compound where+order_by to prevent needing composite indexes
    complaints_docs = db.collection('complaints').get()
    complaints = []
    for doc in complaints_docs:
        c = doc.to_dict()
        # Safely convert Firestore Timestamp / datetime to string for templates
        for field in ('created_at', 'updated_at'):
            if field in c and c[field] and not isinstance(c[field], str):
                try:
                    c[field] = c[field].strftime("%Y-%m-%d %H:%M:%S")
                except Exception:
                    c[field] = str(c[field])
        # Fetch username if user_id exists and not anonymous
        c['user_name'] = 'Anonymous'
        if not c.get('anonymous') and c.get('user_id'):
            user = get_user_by_id(c['user_id'])
            if user:
                c['user_name'] = user['name']
        complaints.append(c)
    # Sort in Python to avoid requiring a composite Firestore index
    complaints.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    return complaints

def get_complaints_by_user(user_id):
    """Fetches complaints submitted by a specific logged-in student."""
    _check_db()
    # Filter by user_id only (no compound index needed), then sort in Python
    docs = db.collection('complaints').where('user_id', '==', user_id).get()
    complaints = []
    for doc in docs:
        c = doc.to_dict()
        for field in ('created_at', 'updated_at'):
            if field in c and c[field] and not isinstance(c[field], str):
                try:
                    c[field] = c[field].strftime("%Y-%m-%d %H:%M:%S")
                except Exception:
                    c[field] = str(c[field])
        complaints.append(c)
    complaints.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    return complaints

def update_complaint_status(complaint_id, status):
    """Updates status of a complaint."""
    db.collection('complaints').document(complaint_id).update({
        'status': status,
        'updated_at': datetime.datetime.utcnow()
    })

# --- COMMENT OPERATIONS ---

def add_comment(complaint_id, user_id, comment_text):
    """Adds an admin feedback comment."""
    comment_ref = db.collection('comments').document()
    comment_ref.set({
        'id': comment_ref.id,
        'complaint_id': complaint_id,
        'user_id': user_id,
        'comment_text': comment_text,
        'created_at': datetime.datetime.utcnow()
    })

def get_comments_by_complaint(complaint_id):
    """Gets all updates for a complaint."""
    _check_db()
    # Filter by complaint_id only (no compound index), sort in Python
    docs = db.collection('comments').where('complaint_id', '==', complaint_id).get()
    comments = []
    for doc in docs:
        c = doc.to_dict()
        # Safely convert timestamp to string for display template
        if 'created_at' in c and c['created_at'] and not isinstance(c['created_at'], str):
            try:
                c['created_at'] = c['created_at'].strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                c['created_at'] = str(c['created_at'])
        comments.append(c)
    comments.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    return comments

# --- NOTIFICATION OPERATIONS ---

def add_notification(user_id, complaint_id, message):
    """Creates a user notification."""
    notif_ref = db.collection('notifications').document()
    notif_ref.set({
        'id': notif_ref.id,
        'user_id': user_id,
        'complaint_id': complaint_id,
        'message': message,
        'read_status': 0,
        'created_at': datetime.datetime.utcnow()
    })

def get_notifications_by_user(user_id):
    """Gets all user alerts."""
    _check_db()
    # Filter by user_id only, sort in Python to avoid composite index requirement
    docs = db.collection('notifications').where('user_id', '==', user_id).get()
    notifs = []
    for doc in docs:
        n = doc.to_dict()
        if 'created_at' in n and n['created_at'] and not isinstance(n['created_at'], str):
            try:
                n['created_at'] = n['created_at'].strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                n['created_at'] = str(n['created_at'])
        notifs.append(n)
    notifs.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    return notifs

def mark_notification_read(notification_id, user_id):
    """Marks a notification as read."""
    db.collection('notifications').document(notification_id).update({
        'read_status': 1
    })

def get_unread_notifications_count(user_id):
    """Counts unread alerts."""
    _check_db()
    # Two filters on different fields may need a composite index.
    # To avoid that, filter by user_id only and count unread in Python.
    docs = db.collection('notifications').where('user_id', '==', user_id).get()
    return sum(1 for doc in docs if doc.to_dict().get('read_status', 0) == 0)
