from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
import os
import face_recognition
import numpy as np
from datetime import datetime
from werkzeug.utils import secure_filename
import base64

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Change this to a secure key
app.config['UPLOAD_FOLDER'] = 'static/faces'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def get_db_connection():
    conn = sqlite3.connect('attendance.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('''CREATE TABLE IF NOT EXISTS employees (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        email TEXT UNIQUE,
                        face_encoding TEXT NOT NULL,
                        image_path TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )''')

    conn.execute('''CREATE TABLE IF NOT EXISTS attendance (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        employee_id INTEGER,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        date TEXT,
                        FOREIGN KEY (employee_id) REFERENCES employees (id)
                    )''')

    conn.execute('''CREATE TABLE IF NOT EXISTS admins (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        password TEXT NOT NULL
                    )''')

    # Create default admin if not exists
    admin_exists = conn.execute('SELECT 1 FROM admins WHERE username = ?', ('admin',)).fetchone()
    if not admin_exists:
        conn.execute('INSERT INTO admins (username, password) VALUES (?, ?)',
                    ('admin', 'admin123'))  # Change default password

    conn.commit()
    conn.close()

# Initialize database on startup
init_db()

@app.route('/')
def index():
    if 'admin_id' not in session:
        return redirect(url_for('login'))
    return redirect(url_for('dashboard'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        admin = conn.execute('SELECT * FROM admins WHERE username = ? AND password = ?',
                           (username, password)).fetchone()
        conn.close()

        if admin:
            session['admin_id'] = admin['id']
            session['admin_username'] = admin['username']
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials', 'error')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'admin_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    employees = conn.execute('SELECT * FROM employees ORDER BY created_at DESC').fetchall()

    # Get today's attendance
    today = datetime.now().strftime('%Y-%m-%d')
    attendance_today = conn.execute('''
        SELECT a.*, e.name
        FROM attendance a
        JOIN employees e ON a.employee_id = e.id
        WHERE a.date = ?
        ORDER BY a.timestamp DESC
    ''', (today,)).fetchall()

    conn.close()

    return render_template('dashboard.html', employees=employees, attendance_today=attendance_today)

@app.route('/add_employee', methods=['GET', 'POST'])
def add_employee():
    if 'admin_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        file = request.files['face_image']

        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(request.url)

        if file:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            # Load image and get face encoding
            try:
                image = face_recognition.load_image_file(filepath)
                face_encodings = face_recognition.face_encodings(image)

                if len(face_encodings) == 0:
                    flash('No face detected in the image', 'error')
                    os.remove(filepath)
                    return redirect(request.url)

                face_encoding = face_encodings[0]
                encoding_str = base64.b64encode(face_encoding.tobytes()).decode('utf-8')

                # Save to database (store relative path without 'static/' prefix)
                relative_filepath = filepath.replace('static/', '', 1)
                conn = get_db_connection()
                conn.execute('INSERT INTO employees (name, email, face_encoding, image_path) VALUES (?, ?, ?, ?)',
                           (name, email, encoding_str, relative_filepath))
                conn.commit()
                conn.close()

                flash('Employee added successfully', 'success')
                return redirect(url_for('dashboard'))

            except Exception as e:
                flash(f'Error processing image: {str(e)}', 'error')
                if os.path.exists(filepath):
                    os.remove(filepath)
                return redirect(request.url)

    return render_template('add_employee.html')

@app.route('/edit_employee/<int:employee_id>', methods=['GET', 'POST'])
def edit_employee(employee_id):
    if 'admin_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    employee = conn.execute('SELECT * FROM employees WHERE id = ?', (employee_id,)).fetchone()
    conn.close()

    if not employee:
        flash('Employee not found', 'error')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        file = request.files.get('face_image')

        # Check if email is already used by another employee
        conn = get_db_connection()
        existing = conn.execute('SELECT id FROM employees WHERE email = ? AND id != ?',
                               (email, employee_id)).fetchone()

        if existing:
            conn.close()
            flash('Email address is already used by another employee', 'error')
            return redirect(request.url)

        update_data = {'name': name, 'email': email}
        image_updated = False

        # Handle face image update
        if file and file.filename != '':
            # Delete old image if it exists
            if employee['image_path'] and os.path.exists(employee['image_path']):
                os.remove(employee['image_path'])

            # Save new image
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            try:
                # Generate new face encoding
                image = face_recognition.load_image_file(filepath)
                face_encodings = face_recognition.face_encodings(image)

                if len(face_encodings) == 0:
                    flash('No face detected in the uploaded image', 'error')
                    os.remove(filepath)
                    conn.close()
                    return redirect(request.url)

                face_encoding = face_encodings[0]
                encoding_str = base64.b64encode(face_encoding.tobytes()).decode('utf-8')

                update_data['face_encoding'] = encoding_str
                update_data['image_path'] = filepath.replace('static/', '', 1)  # Store relative path
                image_updated = True

            except Exception as e:
                flash(f'Error processing image: {str(e)}', 'error')
                if os.path.exists(filepath):
                    os.remove(filepath)
                conn.close()
                return redirect(request.url)

        # Update employee in database
        if image_updated:
            conn.execute('''UPDATE employees
                           SET name = ?, email = ?, face_encoding = ?, image_path = ?
                           WHERE id = ?''',
                        (update_data['name'], update_data['email'],
                         update_data['face_encoding'], update_data['image_path'], employee_id))
        else:
            conn.execute('UPDATE employees SET name = ?, email = ? WHERE id = ?',
                        (update_data['name'], update_data['email'], employee_id))

        conn.commit()
        conn.close()

        flash('Employee updated successfully', 'success')
        return redirect(url_for('dashboard'))

    return render_template('edit_employee.html', employee=employee)

@app.route('/attendance')
def attendance():
    if 'admin_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    attendance_records = conn.execute('''
        SELECT a.*, e.name, e.email
        FROM attendance a
        JOIN employees e ON a.employee_id = e.id
        ORDER BY a.timestamp DESC
    ''').fetchall()
    conn.close()

    return render_template('attendance.html', attendance_records=attendance_records)

@app.route('/run_attendance')
def run_attendance():
    if 'admin_id' not in session:
        return redirect(url_for('login'))

    # Import and run the attendance system
    import subprocess
    import sys

    try:
        # Run the attendance system in a subprocess
        result = subprocess.run([sys.executable, 'attendance_system_db.py'],
                              capture_output=True, text=True, timeout=300)

        if result.returncode == 0:
            flash('Attendance system completed successfully', 'success')
        else:
            flash(f'Error running attendance system: {result.stderr}', 'error')

    except subprocess.TimeoutExpired:
        flash('Attendance system timed out after 5 minutes', 'error')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')

    return redirect(url_for('dashboard'))

@app.route('/reset_attendance', methods=['POST'])
def reset_attendance():
    if 'admin_id' not in session:
        return redirect(url_for('login'))

    # Get today's date
    today = datetime.now().strftime('%Y-%m-%d')

    # Delete all attendance records for today
    conn = get_db_connection()
    deleted_count = conn.execute('DELETE FROM attendance WHERE date = ?', (today,)).rowcount
    conn.commit()
    conn.close()

    flash(f'Attendance reset successfully! {deleted_count} records removed for today.', 'success')
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(debug=True)
