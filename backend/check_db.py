import sqlite3

conn = sqlite3.connect('hostel_records.db')
c = conn.cursor()

print("--- STUDENTS ---")
for row in c.execute("SELECT user_id, course, semester, section FROM users WHERE role='student'").fetchall():
    print(row)

print("\n--- CCs ---")
for row in c.execute("SELECT user_id, course, semester, section FROM users WHERE role='cc'").fetchall():
    print(row)

print("\n--- LEAVE REQUESTS ---")
for row in c.execute("SELECT id, student_id, status, assigned_cc FROM leave_requests").fetchall():
    print(row)

conn.close()
