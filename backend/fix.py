import sqlite3
conn = sqlite3.connect('hostel_records.db')
c = conn.cursor()
c.execute("UPDATE users SET course='B.Tech Computer Science' WHERE role='student'")

# Clean up all existing orphaned leaves
c.execute("DELETE FROM leave_requests")

conn.commit()
conn.close()
print("Fixed DB!")
