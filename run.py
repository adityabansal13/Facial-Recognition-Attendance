#!/usr/bin/env python3
"""
Simple script to run the Facial Recognition Attendance System
"""

import os
import sys

def main():
    print("Starting Facial Recognition Attendance System...")
    print("Make sure you have installed the requirements: pip install -r requirements.txt")
    print("")

    # Check if requirements are installed
    try:
        import flask
        import face_recognition
        import cv2
        print("✓ All dependencies are installed")
    except ImportError as e:
        print(f"✗ Missing dependency: {e}")
        print("Please run: pip install -r requirements.txt")
        return

    # Check if database exists, if not, it will be created when app starts
    if os.path.exists('attendance.db'):
        print("✓ Database found")
    else:
        print("⚠ Database not found - will be created on first run")

    # Check if static directories exist
    if os.path.exists('static/faces'):
        print("✓ Static directories exist")
    else:
        print("⚠ Creating static directories...")
        os.makedirs('static/faces', exist_ok=True)

    print("")
    print("Starting Flask application...")
    print("Access the web interface at: http://127.0.0.1:5000")
    print("Default login: admin / admin123")
    print("Press Ctrl+C to stop the server")
    print("")

    # Run the Flask app
    os.system('python app.py')

if __name__ == "__main__":
    main()
