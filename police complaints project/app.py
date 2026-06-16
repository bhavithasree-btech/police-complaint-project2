import os
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import db_manager
import database
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize database (SQL or Firebase)
db_manager.init_db()

# Mock data injection for local SQL databases (runs only for sqlite/mysql)
def inject_mock_data():
    if Config.DB_TYPE == 'firebase':
        return
        
    conn = database.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM complaints")
    count = cursor.fetchone()[0]
    
    if count == 0:
        cursor.execute("SELECT id FROM users WHERE role = 'student'")
        student = cursor.fetchone()
        student_id = student[0] if student else None
        
        mock_complaints = [
            ("COMP-20260601-A9F3", student_id, "Cyberbullying on Whatsapp", 
             "A group of students have been sending offensive messages and memes in our class WhatsApp group chat.", 
             "Bullying/Cyberbullying", 0, None, "Under Review"),
            ("COMP-20260602-X2E1", None, "Unsafe Street Lights near College Gate", 
             "The street lights leading from the Metro Station to the main college gate are not working. It is unsafe in the evenings.", 
             "Civic Issues (Roads, Lights, Cleanliness)", 1, None, "In Progress"),
            ("COMP-20260603-K4H9", student_id, "Exam Hall Fee Discrepancy", 
             "The administration office is charging an extra processing fee without providing receipts.", 
             "College/School Related Issues", 0, None, "Submitted"),
            ("COMP-20260604-M8B2", None, "Offline Harassment near Bus Stop", 
             "A group of guys repeatedly loiter around the bus stop at 4 PM and make students feel extremely uncomfortable.", 
             "Harassment (Online/Offline)", 1, None, "Resolved")
        ]
        
        for comp in mock_complaints:
            cursor.execute(
                "INSERT INTO complaints (id, user_id, title, description, category, anonymous, file_path, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                comp
            )
            
            if comp[7] == "Resolved":
                cursor.execute(
                    "INSERT INTO comments (complaint_id, user_id, comment_text) VALUES (?, ?, ?)",
                    (comp[0], 1, "Policed patrolled the area and coordinates have been shared with local control room. Beat policing enhanced at 4 PM.")
                )
            elif comp[7] == "In Progress":
                cursor.execute(
                    "INSERT INTO comments (complaint_id, user_id, comment_text) VALUES (?, ?, ?)",
                    (comp[0], 1, "Shared coordinate details with municipal civic engineering branch. Work order scheduled for next Tuesday.")
                )

        conn.commit()
    conn.close()

inject_mock_data()

# Helper for file extension validation
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Routes
@app.route('/')
def home():
    stats = db_manager.get_stats()
    return render_template('home.html', stats=stats)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        mobile = request.form['mobile']
        password = request.form['password']
        
        hashed_password = generate_password_hash(password)
        
        try:
            db_manager.create_user(name, email, mobile, hashed_password, 'student')
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            flash(f'Registration error: {e}', 'danger')
            
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user = db_manager.get_user_by_email(email)
        
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            session['role'] = user['role']
            flash(f"Welcome back, {user['name']}!", 'success')
            
            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('user_dashboard'))
        else:
            flash('Invalid email or password.', 'danger')
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('home'))

# Submit Complaint Route
@app.route('/submit-complaint', methods=['GET', 'POST'])
def submit_complaint_view():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        category = request.form['category']
        anonymous = 1 if request.form.get('anonymous') == '1' else 0
        
        # Determine associated user ID
        user_id = None
        if not anonymous and session.get('user_id'):
            user_id = session.get('user_id')
            
        # Handle file upload
        file_name = None
        if 'file' in request.files:
            file = request.files['file']
            if file and file.filename != '' and allowed_file(file.filename):
                file_name = secure_filename(file.filename)
                import time
                file_name = f"{int(time.time())}_{file_name}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], file_name))
                
        complaint_id = db_manager.create_complaint(title, description, category, anonymous, file_name, user_id)
        
        flash(f"Complaint successfully submitted! Your Tracking ID is: {complaint_id}", 'success')
        return redirect(url_for('track_view', complaint_id=complaint_id))
        
    return render_template('submit_complaint.html')

# Track Complaint Route
@app.route('/track')
def track_view():
    complaint_id = request.args.get('complaint_id')
    complaint = None
    comments = []
    search_made = False
    
    if complaint_id:
        search_made = True
        complaint = db_manager.get_complaint_by_id(complaint_id)
        if complaint:
            comments = db_manager.get_comments_by_complaint(complaint_id)
        
    return render_template('track.html', complaint=complaint, comments=comments, complaint_id=complaint_id, search_made=search_made)

# User Dashboard Route
@app.route('/dashboard')
def user_dashboard():
    if not session.get('user_id') or session.get('role') != 'student':
        flash('Please login to view dashboard.', 'warning')
        return redirect(url_for('login'))
        
    user_id = session.get('user_id')
    
    user = db_manager.get_user_by_id(user_id)
    complaints = db_manager.get_complaints_by_user(user_id)
    notifications = db_manager.get_notifications_by_user(user_id)
    notifications_count = db_manager.get_unread_notifications_count(user_id)
    
    return render_template('user_dashboard.html', user=user, complaints=complaints, notifications=notifications, notifications_count=notifications_count)

# Update profile
@app.route('/dashboard/profile', methods=['POST'])
def update_profile():
    if not session.get('user_id'):
        return redirect(url_for('login'))
        
    name = request.form['name']
    mobile = request.form['mobile']
    user_id = session.get('user_id')
    
    db_manager.update_user_profile(user_id, name, mobile)
    session['user_name'] = name
    flash('Profile updated successfully!', 'success')
    return redirect(url_for('user_dashboard') + '#profile')

# Mark notifications read
@app.route('/dashboard/notification/<notification_id>', methods=['POST'])
def mark_notification(notification_id):
    if not session.get('user_id'):
        return redirect(url_for('login'))
        
    db_manager.mark_notification_read(notification_id, session.get('user_id'))
    return redirect(url_for('user_dashboard') + '#notifications')

# Admin Dashboard Route
@app.route('/admin')
def admin_dashboard():
    if not session.get('user_id') or session.get('role') != 'admin':
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('login'))
        
    complaints = db_manager.get_all_complaints()
    
    # Calculate stats
    stats = {'total': len(complaints), 'submitted': 0, 'review': 0, 'progress': 0, 'resolved': 0}
    chart_categories = {
        'Harassment (Online/Offline)': 0,
        'Bullying/Cyberbullying': 0,
        'Safety Issues': 0,
        'College/School Related Issues': 0,
        'Civic Issues (Roads, Lights, Cleanliness)': 0
    }
    chart_status = {'Submitted': 0, 'Under Review': 0, 'In Progress': 0, 'Resolved': 0}
    
    for c in complaints:
        cat = c['category']
        matched_key = None
        for key in chart_categories.keys():
            if key[:10] in cat:
                matched_key = key
                break
        if matched_key:
            chart_categories[matched_key] += 1
        
        status = c['status']
        if status in chart_status:
            chart_status[status] += 1
            
        if status == 'Submitted': stats['submitted'] += 1
        elif status == 'Under Review': stats['review'] += 1
        elif status == 'In Progress': stats['progress'] += 1
        elif status == 'Resolved': stats['resolved'] += 1
        
    return render_template(
        'admin_dashboard.html', 
        complaints=complaints, 
        stats=stats, 
        chart_categories=chart_categories, 
        chart_status=chart_status
    )

# Admin Update Route
@app.route('/admin/update-complaint', methods=['POST'])
def admin_update_complaint():
    if not session.get('user_id') or session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
        
    complaint_id = request.form['complaint_id']
    new_status = request.form['status']
    comment_text = request.form.get('comment')
    
    db_manager.admin_update_complaint(complaint_id, new_status, comment_text, session.get('user_id'))
    
    flash(f"Complaint {complaint_id} updated successfully.", 'success')
    return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
    app.run(debug=True)
