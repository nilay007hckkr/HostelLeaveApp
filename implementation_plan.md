# Dashboard Screens for HostelLeaveApp

After login, users should be routed to role-specific dashboards. The login screen has a TODO where this routing needs to be wired up. This plan builds all 3 role dashboards using Expo Router's file-based routing.

## Proposed Changes

### Routing Architecture

The app currently uses [(tabs)](file:///c:/Users/nilay/OneDrive/Desktop/HostelLeaveApp/frontend/app/%28tabs%29/index.tsx#45-46) for both Login and Explore. We'll restructure it:
- **[index.tsx](file:///c:/Users/nilay/OneDrive/Desktop/HostelLeaveApp/frontend/app/%28tabs%29/index.tsx)** → Login screen (stays as-is, adds routing after login)
- **[explore.tsx](file:///c:/Users/nilay/OneDrive/Desktop/HostelLeaveApp/frontend/app/%28tabs%29/explore.tsx)** → Will be repurposed/hidden (not needed)
- New **Stack screens** for each dashboard role added to root [_layout.tsx](file:///c:/Users/nilay/OneDrive/Desktop/HostelLeaveApp/frontend/app/_layout.tsx)

New files under `app/`:
- `app/student-dashboard.tsx` — Student's leave request + status screen
- `app/cc-dashboard.tsx` — Class Coordinator's pending approvals screen
- `app/warden-dashboard.tsx` — Warden's full leave management screen

---

### Frontend — New Screens

#### [MODIFY] [index.tsx](file:///c:/Users/nilay/OneDrive/Desktop/HostelLeaveApp/frontend/app/(tabs)/index.tsx)
- After successful login, read `role` from `data.user_profile`
- Use `router.push('/student-dashboard', { ... })` with user profile as params
- Route [student](file:///c:/Users/nilay/OneDrive/Desktop/HostelLeaveApp/backend/main.py#145-158) → `/student-dashboard`, `cc` → `/cc-dashboard`, [warden](file:///c:/Users/nilay/OneDrive/Desktop/HostelLeaveApp/backend/main.py#189-275) → `/warden-dashboard`
- Pass `user_profile` data via `router.push` params

#### [MODIFY] [_layout.tsx](file:///c:/Users/nilay/OneDrive/Desktop/HostelLeaveApp/frontend/app/_layout.tsx)
- Register the 3 new Stack screens so Expo Router knows about them
  - `student-dashboard`, `cc-dashboard`, `warden-dashboard`

#### [NEW] [student-dashboard.tsx](file:///c:/Users/nilay/OneDrive/Desktop/HostelLeaveApp/frontend/app/student-dashboard.tsx)
- Shows student name, hostel, room number, course info from profile
- **Leave Request Form**: destination input, date picker, transport toggle
- **Submit** calls `POST /request-leave`
- **Status Card**: calls `GET /student/{id}/status` to show latest leave status
- **Logout** button returns to login

#### [NEW] [cc-dashboard.tsx](file:///c:/Users/nilay/OneDrive/Desktop/HostelLeaveApp/frontend/app/cc-dashboard.tsx)
- Shows all pending leaves from `GET /admin/leaves`
- Filters to only show requests with status containing `"CC_Section_"`
- Approve / Reject buttons call `PUT /admin/update-status/{id}?new_status=...`
  - Approval sets status to `"Pending Warden Approval"`
  - Rejection sets status to `"REJECTED by CC"`
- Logout button

#### [NEW] [warden-dashboard.tsx](file:///c:/Users/nilay/OneDrive/Desktop/HostelLeaveApp/frontend/app/warden-dashboard.tsx)
- Shows all leave requests from `GET /admin/leaves`
- Final Approve → sets status `"APPROVED"`
- Final Reject → sets status `"REJECTED by Warden"`
- Shows student name, hostel, room, destination, date, transport
- Logout button

---

### Backend — Minor Enhancement

#### [MODIFY] [main.py](file:///c:/Users/nilay/OneDrive/Desktop/HostelLeaveApp/backend/main.py)
- Add `return_date` field support is **not needed** (keep it simple)
- The `/admin/update-status` route currently takes `new_status` as a **query param** — this works fine with the existing frontend. No changes needed.

---

## Verification Plan

### Manual Verification (no automated test suite exists)

**Setup**: Make sure the backend is running at `http://10.30.48.195:8000` (or localhost) and Expo app is running.

1. **Student Flow**:
   - Login with `2561143` / `pass123`
   - Should be routed to Student Dashboard showing name "Nilay Joshi", hostel info
   - Submit a leave request for tomorrow's date → should show success + status updates
   - "Check Status" should show latest request status

2. **CC Flow**:
   - Login with `cc_admin` / `cc123`
   - Should see CC Dashboard with pending requests assigned to their section
   - Approve one → status changes to "Pending Warden Approval"
   - Reject one → status changes to "REJECTED by CC"

3. **Warden Flow**:
   - Login with `warden_admin` / `warden123`
   - Should see all leave requests including ones awaiting warden approval
   - Final approve/reject works correctly

4. **Logout**: All dashboards should have a logout button returning to the Login screen
