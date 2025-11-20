# Facial Recognition Attendance System

A complete facial recognition attendance system with a web-based admin interface built with Flask and SQLite.

## Features

- **Web-based Admin Interface**: Add employees, view attendance records, and manage the system through a modern web UI
- **Real-time Facial Recognition**: Uses OpenCV and face_recognition library for accurate face detection
- **Database Integration**: SQLite database stores employee information and attendance records
- **Face Encoding Storage**: Securely stores facial encodings in the database
- **Attendance Tracking**: Automatic attendance marking with duplicate prevention
- **Responsive Design**: Modern, mobile-friendly web interface

## Installation

1. **Clone or download the project files**

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the Flask application**:
   ```bash
   python app.py
   ```

4. **Access the web interface**:
   Open your browser and go to `http://127.0.0.1:5000`

## Usage

### Admin Login
- **Default credentials**:
  - Username: `admin`
  - Password: `admin123`
- **Important**: Change the default password in the code for security!

### Adding Employees

1. Log in to the admin dashboard
2. Click "Add New Employee"
3. Fill in the employee's name and email
4. Upload a clear face image (JPG, PNG format)
5. Click "Add Employee"

**Image Requirements**:
- Clear, well-lit photo
- Face should be clearly visible
- Supported formats: JPG, PNG
- Maximum size: 16MB

### Editing Employees

1. On the dashboard, find the employee card you want to edit
2. Click the "Edit" button on the employee card
3. Update the name, email, or upload a new face image
4. Click "Update Employee"

**Notes:**
- You can update name and email without changing the image
- Uploading a new image will replace the current face photo
- Email addresses must be unique across all employees

### Running Attendance System

1. From the dashboard, click "Run Attendance System"
2. The system will open a camera window
3. Employees will be automatically recognized and attendance marked
4. Press 'q' to stop the attendance system

### Resetting Daily Attendance

1. Click the red "Reset Today's Attendance" button on the dashboard
2. Confirm the action (double confirmation required)
3. All attendance records for the current day will be permanently deleted

**⚠️ Warning:** This action cannot be undone. Use with caution!

### Viewing Attendance Records

1. Click "View All Attendance" from the dashboard
2. Filter records by date or name
3. Export attendance data to CSV

## Database Schema

The system uses SQLite with the following tables:

- **employees**: Stores employee information and face encodings
- **attendance**: Stores attendance records with timestamps
- **admins**: Stores admin user credentials

## File Structure

```
facial_recognition_attendance/
├── app.py                      # Main Flask web application
├── attendance_system_db.py     # Facial recognition attendance system
├── attendance.db              # SQLite database (created automatically)
├── requirements.txt           # Python dependencies
├── run.py                     # Easy startup script
├── README.md                  # This file
├── templates/                 # HTML templates
│   ├── login.html
│   ├── dashboard.html
│   ├── add_employee.html
│   └── attendance.html
└── static/                    # Static files (CSS, JS, images)
    └── faces/                 # Uploaded face images
```

## Security Notes

- Change the default admin password before deployment
- The application runs on localhost by default
- For production deployment, consider:
  - Using environment variables for secrets
  - Adding HTTPS
  - Implementing proper user authentication
  - Database connection pooling

## Troubleshooting

### Camera Issues
- Ensure camera permissions are granted
- Check if camera is being used by another application
- Try restarting the application

### Face Recognition Issues
- Ensure good lighting when taking photos
- Make sure faces are clearly visible in uploaded images
- The system works best with front-facing, well-lit photos

### Database Issues
- The database is created automatically on first run
- If issues occur, delete `attendance.db` and restart the application

## Dependencies

- Flask: Web framework
- face_recognition: Facial recognition library
- OpenCV: Computer vision library
- NumPy: Numerical computing
- Pillow: Image processing
- Werkzeug: WSGI utility library

## License

This project is for educational purposes. Modify and distribute as needed.
