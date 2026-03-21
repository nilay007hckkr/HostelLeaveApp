from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from datetime import date
import sqlite3

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- DATA MODELS ---
class UserLogin(BaseModel):
    user_id: str
    password: str

class LeaveRequest(BaseModel):
    student_id: str
    destination: str
    reason: str
    leave_date: date
    arrival_date: date
    requires_transport: bool

class ProfileUpdate(BaseModel):
    user_id: str
    course: str
    semester: str
    section: str
    hostel: str
    room_number: str
    mother_phone: str
    father_phone: str

class PushTokenUpdate(BaseModel):
    token: str

university_holidays = [date(2026, 3, 21), date(2026, 3, 22)]

def is_holiday_or_weekend(d: date) -> bool:
    """Returns True if the date is a Saturday, Sunday, or university holiday."""
    return d.weekday() >= 5 or d in university_holidays

# --- DATABASE SETUP ---
def setup_database():
    conn = sqlite3.connect("hostel_records.db")
    cursor = conn.cursor()
    
    # 1. Users Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            role TEXT,
            password TEXT,
            name TEXT,
            course TEXT,
            semester TEXT,
            section TEXT,
            hostel TEXT,
            room_number TEXT,
            mother_phone TEXT,
            father_phone TEXT,
            phone TEXT,
            profile_complete INTEGER DEFAULT 0,
            push_token TEXT
        )
    ''')

    # Add new columns to existing DB if they don't exist (migration safety)
    for col, col_type in [('semester', 'TEXT'), ('phone', 'TEXT'), ('profile_complete', 'INTEGER DEFAULT 0'), ('push_token', 'TEXT')]:
        try:
            cursor.execute(f'ALTER TABLE users ADD COLUMN {col} {col_type}')
        except Exception:
            pass

    # 2. Leave Requests Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS leave_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT,
            destination TEXT,
            reason TEXT,
            leave_date TEXT,
            arrival_date TEXT,
            requires_transport BOOLEAN,
            status TEXT,
            assigned_cc TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Migration safety for arrival_date, reason, and created_at
    for col, col_type in [('arrival_date', 'TEXT'), ('reason', 'TEXT'), ('created_at', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP')]:
        try:
            cursor.execute(f'ALTER TABLE leave_requests ADD COLUMN {col} {col_type}')
        except Exception:
            pass
    
    # Auto-Seeder: If empty, inject official accounts
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        cursor.executemany('''
            INSERT INTO users (user_id, role, password, name, course, semester, section, hostel, room_number, mother_phone, father_phone, phone, profile_complete)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', [
            ('2561143', 'student', 'pass123', 'Nilay Joshi', '', '', '', '', '', '', '', '', 0),
            ('student_1', 'student', 'pass', 'Alice (Pending Profile)', '', '', '', '', '', '', '', '', 0),
            ('student_2', 'student', 'pass', 'Bob (Pending Profile)', '', '', '', '', '', '', '', '', 0),
            ('cc_a', 'cc', 'pass', 'Prof. Alpha (CC Sec A)', 'BTech', '1st', 'A', '', '', '', '', '9870000001', 1),
            ('cc_b', 'cc', 'pass', 'Prof. Beta (CC Sec B)', 'BTech', '1st', 'B', '', '', '', '', '9870000002', 1),
            ('warden_bh1', 'warden', 'pass', 'Warden BH1', '', '', '', 'Boys Hostel 1', '', '', '', '9999999991', 1),
            ('warden_gh1', 'warden', 'pass', 'Warden GH1', '', '', '', 'Girls Hostel 1', '', '', '', '9999999992', 1)
        ])
        
    conn.commit()
    conn.close()

    # Normalize any stale course names left from old data entry so CC matching works
    conn2 = sqlite3.connect("hostel_records.db")
    c2 = conn2.cursor()
    c2.execute("UPDATE users SET course = 'BTech' WHERE LOWER(TRIM(course)) IN ('b tech', 'b.tech', 'b.tech computer science', 'btech')")
    conn2.commit()
    conn2.close()

setup_database()

# --- THE OVERRIDE BUTTON ---
@app.get("/force-seed")
def force_seed_database():
    conn = sqlite3.connect("hostel_records.db")
    cursor = conn.cursor()
    cursor.executemany('''
        INSERT OR REPLACE INTO users (user_id, role, password, name, course, semester, section, hostel, room_number, mother_phone, father_phone, phone, profile_complete)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', [
        ('2561143', 'student', 'pass123', 'Nilay Joshi', '', '', '', '', '', '', '', '', 0),
        ('student_1', 'student', 'pass', 'Alice (Pending Profile)', '', '', '', '', '', '', '', '', 0),
        ('student_2', 'student', 'pass', 'Bob (Pending Profile)', '', '', '', '', '', '', '', '', 0),
        ('cc_a', 'cc', 'pass', 'Prof. Alpha (CC Sec A)', 'BTech', '1st', 'A', '', '', '', '', '9870000001', 1),
        ('cc_b', 'cc', 'pass', 'Prof. Beta (CC Sec B)', 'BTech', '1st', 'B', '', '', '', '', '9870000002', 1),
        ('warden_bh1', 'warden', 'pass', 'Warden BH1', '', '', '', 'Boys Hostel 1', '', '', '', '9999999991', 1),
        ('warden_gh1', 'warden', 'pass', 'Warden GH1', '', '', '', 'Girls Hostel 1', '', '', '', '9999999992', 1)
    ])
    conn.commit()
    conn.close()
    return {"status": "SUCCESS! Student account reset with empty profile for testing."}

# --- UPDATE STUDENT PROFILE ---
@app.put("/student/update-profile")
def update_student_profile(data: ProfileUpdate):
    conn = sqlite3.connect("hostel_records.db")
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE users
        SET course = ?, semester = ?, section = ?, hostel = ?,
            room_number = ?, mother_phone = ?, father_phone = ?, profile_complete = 1
        WHERE user_id = ?
    ''', (data.course, data.semester, data.section, data.hostel,
          data.room_number, data.mother_phone, data.father_phone, data.user_id))
    conn.commit()

    # Return the updated user profile
    conn.row_factory = sqlite3.Row
    cursor2 = conn.cursor()
    cursor2.execute("SELECT * FROM users WHERE user_id = ?", (data.user_id,))
    updated_user = cursor2.fetchone()
    conn.close()

    if updated_user:
        return {"success": True, "user_profile": dict(updated_user)}
    raise HTTPException(status_code=404, detail="User not found")

# --- API ROUTES ---
@app.get("/")
def read_root():
    return {"message": "Welcome to the GEHU Backend!"}

@app.post("/login")
def login_user(credentials: UserLogin):
    conn = sqlite3.connect("hostel_records.db")
    conn.row_factory = sqlite3.Row 
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users WHERE user_id = ? AND password = ?", (credentials.user_id, credentials.password))
    user = cursor.fetchone()
    conn.close()

    if user:
        return {"success": True, "user_profile": dict(user)}
    else:
        raise HTTPException(status_code=401, detail="Invalid ID or Password")

@app.post("/request-leave")
def submit_leave_request(request: LeaveRequest):
    conn = sqlite3.connect("hostel_records.db")
    cursor = conn.cursor()

    cursor.execute("SELECT course, semester, section FROM users WHERE user_id = ?", (request.student_id,))
    student_data = cursor.fetchone()
    if student_data and student_data[0]:
        course, semester, section = student_data
        
        # Match CC with case and whitespace insensitivity
        cursor.execute("SELECT user_id, name FROM users WHERE role = 'cc' AND LOWER(TRIM(course)) = LOWER(TRIM(?)) AND LOWER(TRIM(semester)) = LOWER(TRIM(?)) AND LOWER(TRIM(section)) = LOWER(TRIM(?))", 
                       (course, semester, section))
        cc_match = cursor.fetchone()
        
        if cc_match:
            assigned_cc = cc_match[0] # user_id of the CC
            current_status = f"Pending {cc_match[1]} Approval"
        else:
            assigned_cc = "Unknown CC"
            current_status = f"Pending Class Coordinator Approval"
    else:
        assigned_cc = "Unknown CC"
        current_status = f"Pending Class Coordinator Approval"

    if is_holiday_or_weekend(request.leave_date):
        current_status = "Pending Warden Approval"
        day_type = "weekend" if request.leave_date.weekday() >= 5 else "university holiday"
        routing_message = f"Leave date falls on a {day_type}. Bypassing CC — sent directly to Warden."

        # Notify Warden directly
        cursor.execute("SELECT push_token FROM users WHERE role='warden' AND hostel=(SELECT hostel FROM users WHERE user_id=?)", (request.student_id,))
        for w in cursor.fetchall():
            send_push_notification(w[0], "🛡️ New Leave Request", f"A student requested leave on a {day_type}. No CC required.")

    else:
        routing_message = "Working day. Sent to Class Coordinator for approval."

        # Notify CC (only if one was matched)
        if assigned_cc != "Unknown CC":
            cursor.execute("SELECT push_token FROM users WHERE user_id=?", (assigned_cc,))
            cc_row = cursor.fetchone()
            if cc_row and cc_row[0]:
                send_push_notification(cc_row[0], "🔔 New Leave Request", "A student from your section has requested leave.")

    cursor.execute('''
        INSERT INTO leave_requests (student_id, destination, reason, leave_date, arrival_date, requires_transport, status, assigned_cc)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (request.student_id, request.destination, request.reason, str(request.leave_date), str(request.arrival_date), request.requires_transport, current_status, assigned_cc))
    conn.commit()
    conn.close()

    return {"success": True, "status": current_status, "system_note": routing_message}

@app.get("/student/{student_id}/status")
def get_student_status(student_id: str):
    conn = sqlite3.connect("hostel_records.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Auto-expire pending requests older than 24 hours
    cursor.execute("UPDATE leave_requests SET status = 'Expired (24h Timeout)' WHERE status LIKE 'Pending%' AND created_at <= datetime('now', '-24 hours')")
    conn.commit()

    cursor.execute('SELECT * FROM leave_requests WHERE student_id = ? ORDER BY id DESC LIMIT 1', (student_id,))
    record = cursor.fetchone()
    conn.close()
    
    if record:
        return {"success": True, "data": dict(record)}
    else:
        return {"success": False, "message": "No leave requests found for this ID."}

@app.get("/student/{student_id}/cc-info")
def get_student_cc_info(student_id: str):
    conn = sqlite3.connect("hostel_records.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get student course/sem/sec
    cursor.execute("SELECT course, semester, section FROM users WHERE user_id = ?", (student_id,))
    student = cursor.fetchone()
    if not student:
        conn.close()
        return {"success": False, "message": "Student not found"}
        
    # Find CC matching course/sem/sec (case and whitespace insensitive)
    cursor.execute("SELECT name, phone FROM users WHERE role = 'cc' AND LOWER(TRIM(course)) = LOWER(TRIM(?)) AND LOWER(TRIM(semester)) = LOWER(TRIM(?)) AND LOWER(TRIM(section)) = LOWER(TRIM(?))", 
                   (student["course"], student["semester"], student["section"]))
    cc = cursor.fetchone()
    conn.close()
    
    if cc:
        return {"success": True, "name": cc["name"], "phone": cc["phone"]}
    return {"success": False, "message": "No CC mapped yet"}

@app.put("/admin/update-status/{request_id}")
def update_leave_status(request_id: int, new_status: str):
    conn = sqlite3.connect("hostel_records.db")
    cursor = conn.cursor()
    
    # 1. Update the request
    cursor.execute('UPDATE leave_requests SET status = ? WHERE id = ?', (new_status, request_id))
    
    # 2. Fire Push Notifications
    cursor.execute('SELECT student_id, (SELECT hostel FROM users WHERE user_id=leave_requests.student_id) as hostel FROM leave_requests WHERE id = ?', (request_id,))
    req = cursor.fetchone()
    
    if req:
        student_id, hostel = req
        if "Pending Warden" in new_status:
            # CC Approved → Notify the student's hostel Warden
            cursor.execute("SELECT push_token FROM users WHERE role='warden' AND hostel=?", (hostel,))
            for w in cursor.fetchall():
                send_push_notification(w[0], "🛡️ CC Approved Leave", "A request has been approved by CC and is ready for your final decision.")
        elif "APPROVED" in new_status:
            # Warden fully approved → Notify student
            cursor.execute("SELECT push_token FROM users WHERE user_id=?", (student_id,))
            student = cursor.fetchone()
            if student and student[0]:
                send_push_notification(student[0], "✅ Leave Approved!", "Your leave request has been fully approved by the Warden.")
        elif "REJECTED" in new_status:
            # CC or Warden rejected → Notify student
            rejected_by = "Warden" if "Warden" in new_status else "Class Coordinator"
            cursor.execute("SELECT push_token FROM users WHERE user_id=?", (student_id,))
            student = cursor.fetchone()
            if student and student[0]:
                send_push_notification(student[0], "❌ Leave Rejected", f"Your leave request was rejected by the {rejected_by}.")

    conn.commit()
    conn.close()
    return {"success": True, "message": f"Leave Request #{request_id} updated to {new_status}"}

@app.get("/admin/leaves")
def view_all_leaves():
    conn = sqlite3.connect("hostel_records.db")
    conn.row_factory = sqlite3.Row 
    cursor = conn.cursor()
    
    # 1. Auto-expire requests with a past leave date that are still pending
    cursor.execute("UPDATE leave_requests SET status = 'Expired (Past Date)' WHERE status LIKE 'Pending%' AND leave_date < date('now', 'localtime')")
    
    # 2. Auto-expire pending requests older than 24 hours
    cursor.execute("UPDATE leave_requests SET status = 'Expired (24h Timeout)' WHERE status LIKE 'Pending%' AND created_at <= datetime('now', '-24 hours')")
    
    conn.commit()
    
    # JOIN the tables so the Warden sees the Student's actual name!
    cursor.execute('''
        SELECT leave_requests.*, users.name as student_name, users.course, users.semester, users.section, users.hostel, users.room_number, users.mother_phone, users.father_phone
        FROM leave_requests 
        LEFT JOIN users ON leave_requests.student_id = users.user_id
    ''')
    all_records = cursor.fetchall()
    conn.close()
    
    return {"total_requests": len(all_records), "data": [dict(row) for row in all_records]}

@app.put("/user/{user_id}/push-token")
def update_push_token(user_id: str, payload: PushTokenUpdate):
    conn = sqlite3.connect("hostel_records.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET push_token = ? WHERE user_id = ?", (payload.token, user_id))
    conn.commit()
    conn.close()
    return {"success": True}

import urllib.request
import json

def send_push_notification(token: str, title: str, body: str):
    if not token: return
    try:
        req = urllib.request.Request(
            "https://exp.host/--/api/v2/push/send",
            data=json.dumps({"to": token, "title": title, "body": body}).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        urllib.request.urlopen(req, timeout=3)
    except Exception as e:
        print(f"Push Notification Error: {e}")

# --- WARDEN DASHBOARD ---
@app.get("/warden", response_class=HTMLResponse)
def warden_web_interface():
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Hostel Leave Management</title>
        <style>
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; padding: 20px; background-color: #f0f2f5; }
            h1 { color: #1a1a1a; text-align: center; margin-bottom: 30px;}
            table { width: 100%; border-collapse: collapse; background: white; box-shadow: 0 1px 3px rgba(0,0,0,0.2); font-size: 14px; }
            th, td { padding: 12px; border-bottom: 1px solid #ddd; text-align: left; }
            th { background-color: #2c3e50; color: white; }
            tr:hover { background-color: #f5f5f5; }
            .btn { padding: 8px 12px; border: none; border-radius: 4px; cursor: pointer; font-weight: bold; margin-right: 5px; font-size: 12px;}
            .approve-btn { background-color: #27ae60; color: white; }
            .reject-btn { background-color: #c0392b; color: white; }
            .status-text { font-weight: bold; color: #2980b9; }
            .student-details { font-size: 12px; color: #7f8c8d; }
        </style>
    </head>
    <body>
        <h1>🛡️ Warden Control Panel</h1>
        
        <table id="requestsTable">
            <tr>
                <th>Req ID</th>
                <th>Student Info</th>
                <th>Hostel & Room</th>
                <th>Destination</th>
                <th>Date</th>
                <th>Transport</th>
                <th>Current Status</th>
                <th>Actions</th>
            </tr>
        </table>

        <script>
            async function loadRequests() {
                const response = await fetch('/admin/leaves');
                const result = await response.json();
                const table = document.getElementById('requestsTable');
                
                while(table.rows.length > 1) { table.deleteRow(1); }

                result.data.forEach(req => {
                    const row = table.insertRow();
                    const transport = req.requires_transport ? "Yes 🚌" : "No";
                    
                    let actionButtons = "";
                    if (req.status.includes("APPROVED") || req.status.includes("REJECTED")) {
                        actionButtons = ""; 
                    } else {
                        actionButtons = `
                            <button class="btn approve-btn" onclick="updateStatus(${req.id}, 'APPROVED')">Approve ✅</button>
                            <button class="btn reject-btn" onclick="updateStatus(${req.id}, 'REJECTED')">Reject ❌</button>
                        `;
                    }
                    
                    row.innerHTML = `
                        <td>#${req.id}</td>
                        <td>
                            <strong>${req.student_name || 'Unknown'}</strong><br>
                            <span class="student-details">ID: ${req.student_id} | ${req.course || 'N/A'}</span>
                        </td>
                        <td><strong>${req.hostel || 'N/A'}</strong><br><span class="student-details">Room: ${req.room_number || 'N/A'}</span></td>
                        <td>${req.destination}</td>
                        <td>${req.leave_date}</td>
                        <td>${transport}</td>
                        <td class="status-text">${req.status}</td>
                        <td>${actionButtons}</td>
                    `;
                });
            }

            async function updateStatus(id, newStatus) {
                await fetch(`/admin/update-status/${id}?new_status=${newStatus}`, { method: 'PUT' });
                loadRequests(); 
            }

            loadRequests();
        </script>
    </body>
    </html>
    """
    return html_content