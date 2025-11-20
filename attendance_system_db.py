import face_recognition
import cv2
import numpy as np
import sqlite3
from datetime import datetime
import base64

def get_db_connection():
    conn = sqlite3.connect('attendance.db')
    conn.row_factory = sqlite3.Row
    return conn

def load_known_faces():
    """Load known faces and encodings from database"""
    conn = get_db_connection()
    employees = conn.execute('SELECT * FROM employees').fetchall()
    conn.close()

    known_face_encodings = []
    known_face_names = []
    employee_ids = []

    for employee in employees:
        try:
            # Decode the face encoding from base64
            encoding_bytes = base64.b64decode(employee['face_encoding'])
            face_encoding = np.frombuffer(encoding_bytes, dtype=np.float64)

            known_face_encodings.append(face_encoding)
            known_face_names.append(employee['name'])
            employee_ids.append(employee['id'])
        except Exception as e:
            print(f"Error loading face encoding for {employee['name']}: {e}")
            continue

    return known_face_encodings, known_face_names, employee_ids

def mark_attendance(employee_id, employee_name):
    """Mark attendance for an employee"""
    conn = get_db_connection()

    # Check if already marked today
    today = datetime.now().strftime('%Y-%m-%d')
    existing = conn.execute('SELECT 1 FROM attendance WHERE employee_id = ? AND date = ?',
                          (employee_id, today)).fetchone()

    if not existing:
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        conn.execute('INSERT INTO attendance (employee_id, timestamp, date) VALUES (?, ?, ?)',
                   (employee_id, current_time, today))
        conn.commit()
        print(f"Attendance marked for {employee_name} at {current_time}")

    conn.close()

def main():
    # Initialize the video capture object for the default camera
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Error: Could not open camera. Please check camera permissions.")
        return

    # Load known faces from database
    print("Loading known faces from database...")
    known_face_encodings, known_face_names, employee_ids = load_known_faces()

    if not known_face_encodings:
        print("No faces found in database. Please add employees first.")
        cap.release()
        return

    print(f"Loaded {len(known_face_encodings)} faces from database")

    # Track employees who haven't been marked yet today
    today = datetime.now().strftime('%Y-%m-%d')
    conn = get_db_connection()
    already_present_today = conn.execute('''
        SELECT DISTINCT employee_id
        FROM attendance
        WHERE date = ?
    ''', (today,)).fetchall()
    conn.close()

    present_employee_ids = {record['employee_id'] for record in already_present_today}
    expected_employees = [name for name, emp_id in zip(known_face_names, employee_ids) if emp_id not in present_employee_ids]

    print(f"Expected employees today: {len(expected_employees)}")
    print(f"Already present today: {len(present_employee_ids)}")

    # Get the current time
    now = datetime.now()

    # Start the main video capture loop
    print("Starting attendance system... Press 'q' to quit.")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Could not read frame from camera.")
            break

        # Resize frame for faster processing
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

        # Recognize faces in the frame
        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        for face_encoding in face_encodings:
            # Compare face with known faces
            matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
            face_distance = face_recognition.face_distance(known_face_encodings, face_encoding)
            best_match_index = np.argmin(face_distance)

            if matches[best_match_index] and face_distance[best_match_index] < 0.6:  # Threshold for match
                name = known_face_names[best_match_index]
                employee_id = employee_ids[best_match_index]

                # Mark attendance if not already done today
                if employee_id not in present_employee_ids:
                    mark_attendance(employee_id, name)
                    present_employee_ids.add(employee_id)
                    expected_employees = [n for n in expected_employees if n != name]

                    # Display success message
                    font = cv2.FONT_HERSHEY_SIMPLEX
                    bottom_left_corner_of_text = (50, 100)
                    font_scale = 1.5
                    font_color = (0, 255, 0)  # Green for success
                    thickness = 3
                    line_type = 2
                    cv2.putText(frame, f"{name} - ATTENDANCE MARKED",
                              bottom_left_corner_of_text, font, font_scale, font_color, thickness, line_type)
                else:
                    # Already marked today - show different message
                    font = cv2.FONT_HERSHEY_SIMPLEX
                    bottom_left_corner_of_text = (50, 100)
                    font_scale = 1.2
                    font_color = (255, 165, 0)  # Orange for already present
                    thickness = 2
                    line_type = 2
                    cv2.putText(frame, f"{name} - ALREADY PRESENT TODAY",
                              bottom_left_corner_of_text, font, font_scale, font_color, thickness, line_type)

        # Display status information
        status_text = f"Expected: {len(expected_employees)} | Present Today: {len(present_employee_ids)}"
        cv2.putText(frame, status_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        cv2.imshow("Attendance System", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    # Release the video capture object and close windows
    cap.release()
    cv2.destroyAllWindows()

    print("Attendance system stopped.")
    print(f"Total employees present today: {len(present_employee_ids)}")
    print(f"Remaining expected employees: {len(expected_employees)}")
    if expected_employees:
        print("Still expected:", ", ".join(expected_employees))

if __name__ == "__main__":
    main()
