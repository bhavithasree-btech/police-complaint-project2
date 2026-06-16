import database
import firebase_db
from config import Config
from werkzeug.security import generate_password_hash
import datetime

# Determine which database engine to use
def is_firebase():
    return Config.DB_TYPE == 'firebase'

def init_db():
    if is_firebase():
        firebase_db.init_firebase()
    else:
        database.init_db()

# --- STATISTICS ---

def get_stats():
    if is_firebase():
        complaints = firebase_db.db.collection('complaints').get()
        stats = {'total': len(complaints), 'submitted': 0, 'review': 0, 'progress': 0, 'resolved': 0}
        for doc in complaints:
            c = doc.to_dict()
            status = c.get('status', 'Submitted')
            if status == 'Submitted': stats['submitted'] += 1
            elif status == 'Under Review': stats['review'] += 1
            elif status == 'In Progress': stats['progress'] += 1
            elif status == 'Resolved': stats['resolved'] += 1
        return stats
    else:
        conn = database.get_db_connection()
        cursor = conn.cursor()
        stats = {}
        cursor.execute("SELECT COUNT(*) FROM complaints")
        stats['total'] = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM complaints WHERE status = 'Submitted'")
        stats['submitted'] = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM complaints WHERE status = 'Under Review'")
        stats['review'] = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM complaints WHERE status = 'In Progress'")
        stats['progress'] = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM complaints WHERE status = 'Resolved'")
        stats['resolved'] = cursor.fetchone()[0]
        conn.close()
        return stats

# --- USER OPERATIONS ---

def create_user(name, email, mobile, password_hash, role='student'):
    if is_firebase():
        return firebase_db.create_user(name, email, mobile, password_hash, role)
    else:
        conn = database.get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (name, email, mobile, password_hash, role) VALUES (?, ?, ?, ?, ?)",
            (name, email, mobile, password_hash, role)
        )
        conn.commit()
        conn.close()
        return True

def get_user_by_email(email):
    if is_firebase():
        return firebase_db.get_user_by_email(email)
    else:
        conn = database.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        conn.close()
        if user:
            return dict(user)
        return None

def get_user_by_id(user_id):
    if is_firebase():
        return firebase_db.get_user_by_id(user_id)
    else:
        conn = database.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        conn.close()
        if user:
            return dict(user)
        return None

def update_user_profile(user_id, name, mobile):
    if is_firebase():
        firebase_db.update_user_profile(user_id, name, mobile)
    else:
        conn = database.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET name = ?, mobile = ? WHERE id = ?", (name, mobile, user_id))
        conn.commit()
        conn.close()

# --- COMPLAINT OPERATIONS ---

def create_complaint(title, description, category, anonymous, file_path, user_id=None):
    if is_firebase():
        return firebase_db.create_complaint(title, description, category, anonymous, file_path, user_id)
    else:
        complaint_id = database.generate_complaint_id()
        conn = database.get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO complaints (id, user_id, title, description, category, anonymous, file_path) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (complaint_id, user_id, title, description, category, anonymous, file_path)
        )
        conn.commit()
        conn.close()
        return complaint_id

def get_complaint_by_id(complaint_id):
    if is_firebase():
        return firebase_db.get_complaint_by_id(complaint_id)
    else:
        conn = database.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM complaints WHERE id = ?", (complaint_id,))
        complaint = cursor.fetchone()
        conn.close()
        if complaint:
            return dict(complaint)
        return None

def get_all_complaints():
    if is_firebase():
        return firebase_db.get_all_complaints()
    else:
        conn = database.get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT complaints.*, users.name as user_name 
            FROM complaints 
            LEFT JOIN users ON complaints.user_id = users.id 
            ORDER BY complaints.created_at DESC
        ''')
        complaints = [dict(c) for c in cursor.fetchall()]
        conn.close()
        return complaints

def get_complaints_by_user(user_id):
    if is_firebase():
        return firebase_db.get_complaints_by_user(user_id)
    else:
        conn = database.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM complaints WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
        complaints = [dict(c) for c in cursor.fetchall()]
        conn.close()
        return complaints

def admin_update_complaint(complaint_id, status, comment_text, admin_user_id):
    if is_firebase():
        firebase_db.update_complaint_status(complaint_id, status)
        if comment_text and comment_text.strip():
            firebase_db.add_comment(complaint_id, admin_user_id, comment_text)
        
        # Check and send notification
        complaint = firebase_db.get_complaint_by_id(complaint_id)
        if complaint and complaint.get('user_id'):
            notify_msg = f"Your complaint '{complaint['title']}' has been updated to '{status}'."
            firebase_db.add_notification(complaint['user_id'], complaint_id, notify_msg)
    else:
        conn = database.get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE complaints SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (status, complaint_id)
        )
        if comment_text and comment_text.strip():
            cursor.execute(
                "INSERT INTO comments (complaint_id, user_id, comment_text) VALUES (?, ?, ?)",
                (complaint_id, admin_user_id, comment_text)
            )
        # Notify user if the complaint is not anonymous
        cursor.execute("SELECT user_id, title FROM complaints WHERE id = ?", (complaint_id,))
        row = cursor.fetchone()
        if row and row['user_id']:
            notify_msg = f"Your complaint '{row['title']}' has been updated to '{status}'."
            cursor.execute(
                "INSERT INTO notifications (user_id, complaint_id, message) VALUES (?, ?, ?)",
                (row['user_id'], complaint_id, notify_msg)
            )
        conn.commit()
        conn.close()

# --- COMMENT OPERATIONS ---

def get_comments_by_complaint(complaint_id):
    if is_firebase():
        return firebase_db.get_comments_by_complaint(complaint_id)
    else:
        conn = database.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM comments WHERE complaint_id = ? ORDER BY created_at DESC", (complaint_id,))
        comments = [dict(c) for c in cursor.fetchall()]
        conn.close()
        return comments

# --- NOTIFICATION OPERATIONS ---

def get_notifications_by_user(user_id):
    if is_firebase():
        return firebase_db.get_notifications_by_user(user_id)
    else:
        conn = database.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM notifications WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
        notifs = [dict(n) for n in cursor.fetchall()]
        conn.close()
        return notifs

def get_unread_notifications_count(user_id):
    if is_firebase():
        return firebase_db.get_unread_notifications_count(user_id)
    else:
        conn = database.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM notifications WHERE user_id = ? AND read_status = 0", (user_id,))
        count = cursor.fetchone()[0]
        conn.close()
        return count

def mark_notification_read(notification_id, user_id):
    if is_firebase():
        firebase_db.mark_notification_read(notification_id, user_id)
    else:
        conn = database.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE notifications SET read_status = 1 WHERE id = ? AND user_id = ?", (notification_id, user_id))
        conn.commit()
        conn.close()
