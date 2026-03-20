from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import date
import sqlite3 # NEW: The built-in database tool!

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class LeaveRequest(BaseModel):
    student_id: str
    destination: str
    leave_date: date
    requires_transport: bool

university_holidays = [date(2026, 3, 21), date(2026, 3, 22)]

# --- NEW: DATABASE SETUP ---
def setup_database():
    # This creates a file called 'hostel_records.db' on your laptop
    conn = sqlite3.connect("hostel_records.db")
    cursor = conn.cursor()
    # Create the digital ledger (a table) if it doesn't exist yet
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS leave_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT,
            destination TEXT,
            leave_date TEXT,
            requires_transport BOOLEAN,
            status TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Run the setup the moment the server turns on
setup_database()
# ---------------------------

@app.get("/")
def read_root():
    return {"message": "Welcome to the Hostel Leave App Backend, Nilay!"}

@app.get("/status")
def check_status():
    return {"status": "Server is running perfectly."}

@app.post("/request-leave")
def submit_leave_request(request: LeaveRequest):
    
    # 1. The Logic Check
    if request.leave_date in university_holidays:
        current_status = "Pending Warden Approval"
        routing_message = "Holiday detected. Bypassing CC, sent directly to Warden."
    else:
        current_status = "Pending CC Approval"
        routing_message = "Working day detected. Sent to Class Coordinator first."

    # 2. NEW: Save it to the Database permanently!
    conn = sqlite3.connect("hostel_records.db")
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO leave_requests (student_id, destination, leave_date, requires_transport, status)
        VALUES (?, ?, ?, ?, ?)
    ''', (request.student_id, request.destination, str(request.leave_date), request.requires_transport, current_status))
    conn.commit()
    conn.close()

    # 3. Reply to the Phone
    return {
        "success": True,
        "student": request.student_id,
        "status": current_status,
        "system_note": routing_message
    }
# --- NEW: THE ADMIN DASHBOARD ---
@app.get("/admin/leaves")
def view_all_leaves():
    # 1. Open the vault
    conn = sqlite3.connect("hostel_records.db")
    
    # This magic line formats the database output so it looks pretty in the browser
    conn.row_factory = sqlite3.Row 
    cursor = conn.cursor()
    
    # 2. Read the ledger
    cursor.execute("SELECT * FROM leave_requests")
    all_records = cursor.fetchall()
    conn.close()
    
    # 3. Send it to the screen
    return {
        "total_requests": len(all_records),
        "data": [dict(row) for row in all_records]
    }