import sys
import os
import unittest
import json
import time
import requests
import numpy as np
import cv2

BASE_URL = "http://127.0.0.1:5000/api/v1"

def get_token(email="admin123@gmail.com", password="admin123"):
    res = requests.post(f"{BASE_URL}/auth/login", json={"email": email, "password": password})
    if res.status_code == 200:
        return res.json()["data"]["access_token"]
    raise Exception(f"Login failed ({res.status_code}): {res.text}")

class AndroidAppFullQATestSuite(unittest.TestCase):
    """
    Automated QA Test Execution Suite for FaceAttend Android Application & Backend APIs
    Matches all 7 QA Test Suites in the Validation Plan.
    """

    # --------------------------------------------------------------------------
    # Suite 1: Network Configuration & Server Connection
    # --------------------------------------------------------------------------
    def test_suite_1_01_health_ping(self):
        print("\n[Suite 1] Health Ping Test...")
        res = requests.get(f"{BASE_URL}/health")
        self.assertEqual(res.status_code, 200, f"Expected 200 OK from /health, got {res.status_code}")
        body = res.json()
        self.assertTrue(body.get("success"), "Response success flag should be True")
        self.assertEqual(body["data"]["database"], "healthy", "Database status must be healthy")
        print("  ✓ Server connected and healthy!")

    def test_suite_1_02_invalid_host_simulation(self):
        print("[Suite 1] Invalid Host Connection Test...")
        try:
            res = requests.get("http://10.255.255.1:5000/api/v1/health", timeout=1)
            self.fail("Should have timed out")
        except requests.exceptions.RequestException as e:
            print("  ✓ Network timeout handled gracefully!")

    # --------------------------------------------------------------------------
    # Suite 2: Authentication & Session Token Lifecycle
    # --------------------------------------------------------------------------
    def test_suite_2_01_valid_faculty_login(self):
        print("\n[Suite 2] Valid Faculty Login Test...")
        token = get_token("anshraythatha123@gmail.com", "faculty123")
        self.assertIsNotNone(token, "Login token must not be None")
        print("  ✓ Faculty authentication successful!")

    def test_suite_2_02_invalid_login_credentials(self):
        print("[Suite 2] Invalid Login Credentials Test...")
        payload = {"email": "invalid.user@faceattend.com", "password": "wrongpassword"}
        res = requests.post(f"{BASE_URL}/auth/login", json=payload)
        self.assertEqual(res.status_code, 401, "Expected 401 Unauthorized")
        body = res.json()
        self.assertFalse(body.get("success"))
        print("  ✓ Invalid credentials correctly rejected (401)!")

    # --------------------------------------------------------------------------
    # Suite 3: Active Class Slot & Semester Integration
    # --------------------------------------------------------------------------
    def test_suite_3_01_active_class_slot_resolution(self):
        print("\n[Suite 3] Active Class & Semester Resolution Test...")
        token = get_token("anshraythatha123@gmail.com", "faculty123")
        headers = {"Authorization": f"Bearer {token}"}

        res = requests.get(f"{BASE_URL}/timetables/active?faculty_id=1", headers=headers)
        if res.status_code == 200:
            active_class = res.json().get("data", {})
            print(f"  ✓ Active slot found: {active_class.get('subject_name')} ({active_class.get('class_name')}), Semester: {active_class.get('semester', 'N/A')}")
        else:
            print("  ✓ No active class currently scheduled (404 expected state out of class hours)")

    # --------------------------------------------------------------------------
    # Suite 4: Attendance Taking — Multi-Photo (Up to 3 Photos) & Face Detection
    # --------------------------------------------------------------------------
    def test_suite_4_01_group_detect_photo_recognition(self):
        print("\n[Suite 4] Group Photo Recognition Test...")
        token = get_token("admin123@gmail.com", "admin123")
        headers = {"Authorization": f"Bearer {token}"}

        # Create a synthetic image for testing group detection route
        blank_img = np.zeros((300, 300, 3), dtype=np.uint8)
        _, img_encoded = cv2.imencode('.jpg', blank_img)
        img_bytes = img_encoded.tobytes()

        files = {'image': ('test_group.jpg', img_bytes, 'image/jpeg')}
        res = requests.post(f"{BASE_URL}/attendance/group-detect", headers=headers, files=files)
        self.assertEqual(res.status_code, 200, f"Group detect failed with status {res.status_code}")
        body = res.json().get("data", {})
        self.assertIn("present", body, "Response must include present list")
        self.assertIn("absent", body, "Response must include absent list")
        print(f"  ✓ Group detect processed successfully. Total students in class: {len(body.get('present', [])) + len(body.get('absent', []))}")

    # --------------------------------------------------------------------------
    # Suite 5: Post-Recognition Attendance Checklist & Verification Page
    # --------------------------------------------------------------------------
    def test_suite_5_01_confirm_group_checklist(self):
        print("\n[Suite 5] Post-Recognition Attendance Confirmation Test...")
        token = get_token("admin123@gmail.com", "admin123")
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

        # Submit attendance confirmation for student IDs [1, 2]
        payload = {
            "timetable_id": 2,
            "present_student_ids": [1, 2]
        }
        res = requests.post(f"{BASE_URL}/attendance/confirm-group", headers=headers, json=payload)
        self.assertEqual(res.status_code, 200, f"Confirm group failed: {res.status_code} - {res.text}")
        data = res.json().get("data", {})
        self.assertIn("session_id", data)
        print(f"  ✓ Attendance session #{data.get('session_id')} successfully created with {data.get('marked_count')} present records!")

    # --------------------------------------------------------------------------
    # Suite 6: CSV Export & Roster Data Integrity
    # --------------------------------------------------------------------------
    def test_suite_6_01_csv_export_validation(self):
        print("\n[Suite 6] CSV Attendance Export Test...")
        token = get_token("admin123@gmail.com", "admin123")
        headers = {"Authorization": f"Bearer {token}"}

        res = requests.get(f"{BASE_URL}/reports/export/csv?timetable_id=2", headers=headers)
        self.assertEqual(res.status_code, 200, "CSV Export failed")
        self.assertTrue(res.headers.get("Content-Type", "").startswith("text/csv"))

        csv_content = res.text
        lines = csv_content.strip().split("\n")
        self.assertGreater(len(lines), 0, "CSV content should not be empty")

        headers_line = lines[0]
        self.assertIn("Class Name", headers_line)
        self.assertIn("Student GR Number", headers_line)
        self.assertIn("Status", headers_line)
        print(f"  ✓ CSV Report exported cleanly with {len(lines) - 1} student record lines!")

    # --------------------------------------------------------------------------
    # Suite 7: Edge Cases & System Resilience
    # --------------------------------------------------------------------------
    def test_suite_7_01_unauthorized_token_rejection(self):
        print("\n[Suite 7] Unauthorized Request Rejection Test...")
        bad_headers = {"Authorization": "Bearer invalid_token_xyz"}
        res = requests.get(f"{BASE_URL}/attendance", headers=bad_headers)
        self.assertEqual(res.status_code, 401, "Invalid token must be rejected with 401")
        print("  ✓ Invalid JWT tokens strictly rejected (401)!")

if __name__ == "__main__":
    unittest.main()
