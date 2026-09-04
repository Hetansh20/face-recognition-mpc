import sys
import os
import unittest
import json
import numpy as np
import cv2
from io import BytesIO

# Add workspace to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app import create_app
from backend.models.database import db_session, UserModel, FacultyModel, StudentModel, TimetableModel, AttendanceSessionModel
from backend.utils.security import generate_access_token

class FullStackE2ETestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    def get_auth_headers(self, email="admin123@gmail.com", role="ADMIN", user_id=1):
        token = generate_access_token(user_id=user_id, role=role, email=email)
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    def test_01_health_check(self):
        res = self.client.get("/api/v1/health")
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data.get("success"))
        self.assertEqual(data["data"]["status"], "healthy")

    def test_02_login_invalid_credentials(self):
        res = self.client.post("/api/v1/auth/login", json={"email": "wrong@test.com", "password": "badpassword"})
        self.assertEqual(res.status_code, 401)
        data = json.loads(res.data)
        self.assertFalse(data.get("success"))

    def test_03_login_valid_admin(self):
        res = self.client.post("/api/v1/auth/login", json={"email": "admin123@gmail.com", "password": "admin123"})
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data.get("success"))
        self.assertIn("access_token", data["data"])

    def test_04_unauthorized_access(self):
        res = self.client.get("/api/v1/admin/semesters")
        self.assertEqual(res.status_code, 401)

    def test_05_role_permission_forbidden(self):
        headers = self.get_auth_headers(email="student@test.com", role="STUDENT", user_id=99)
        res = self.client.get("/api/v1/faculty", headers=headers)
        self.assertEqual(res.status_code, 403)

    def test_06_timetable_and_active_session_resolution(self):
        headers = self.get_auth_headers(email="admin123@gmail.com", role="ADMIN", user_id=1)
        res = self.client.get("/api/v1/timetables", headers=headers)
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data.get("success"))
        self.assertIsInstance(data.get("data"), list)

    def test_07_report_export_csv(self):
        headers = self.get_auth_headers(email="admin123@gmail.com", role="ADMIN", user_id=1)
        res = self.client.get("/api/v1/reports/export/csv", headers=headers)
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.content_type.startswith("text/csv"))

    def test_08_report_export_excel(self):
        headers = self.get_auth_headers(email="admin123@gmail.com", role="ADMIN", user_id=1)
        res = self.client.get("/api/v1/reports/export/excel", headers=headers)
        self.assertEqual(res.status_code, 200)

    def test_09_audit_logs(self):
        headers = self.get_auth_headers(email="admin123@gmail.com", role="ADMIN", user_id=1)
        res = self.client.get("/api/v1/logs/audit", headers=headers)
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data.get("success"))

    def test_10_attendance_session_lifecycle(self):
        tt = db_session.query(TimetableModel).first()
        self.assertIsNotNone(tt, "Need at least one timetable entry in DB for test")
        headers = self.get_auth_headers(email="prof@faceattend.com", role="FACULTY", user_id=2)

        # 1. Start Session
        res = self.client.post("/api/v1/attendance/sessions/start", json={"faculty_id": tt.faculty_id, "timetable_id": tt.id}, headers=headers)
        self.assertIn(res.status_code, [200, 201])
        data = json.loads(res.data)
        sess_data = data.get("data", {})
        session_id = sess_data.get("session_id") or sess_data.get("id")
        self.assertIsNotNone(session_id)

        # 2. Get Session Results
        res_get = self.client.get(f"/api/v1/attendance/sessions/{session_id}", headers=headers)
        self.assertEqual(res_get.status_code, 200)

        # 3. Stop Session
        res_stop = self.client.post(f"/api/v1/attendance/sessions/{session_id}/stop", headers=headers)
        self.assertEqual(res_stop.status_code, 200)
        stop_data = json.loads(res_stop.data).get("data", {})
        self.assertEqual(stop_data.get("status"), "COMPLETED")

    def test_11_update_session_records(self):
        tt = db_session.query(TimetableModel).first()
        headers = self.get_auth_headers(email="admin123@gmail.com", role="ADMIN", user_id=1)
        # Start session
        res = self.client.post("/api/v1/attendance/sessions/start", json={"faculty_id": tt.faculty_id, "timetable_id": tt.id}, headers=headers)
        sess_data = json.loads(res.data).get("data", {})
        session_id = sess_data.get("session_id") or sess_data.get("id")

        # Update records
        res_up = self.client.post(
            f"/api/v1/attendance/sessions/{session_id}/update-records",
            json={"records": [{"student_id": "1", "status": "PRESENT"}]},
            headers=headers
        )
        self.assertEqual(res_up.status_code, 200)

if __name__ == "__main__":
    unittest.main()
