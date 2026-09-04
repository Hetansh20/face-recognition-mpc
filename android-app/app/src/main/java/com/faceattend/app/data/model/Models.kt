package com.faceattend.app.data.model

import com.google.gson.annotations.SerializedName

// ── Generic API Response ──────────────────────────────────────────────

data class ApiResponse<T>(
    @SerializedName("success") val success: Boolean,
    @SerializedName("data") val data: T?,
    @SerializedName("message") val message: String?,
    @SerializedName("request_id") val requestId: String?,
    @SerializedName("error") val error: ApiError?
)

data class ApiError(
    @SerializedName("code") val code: String,
    @SerializedName("message") val message: String
)

// ── Auth Models ───────────────────────────────────────────────────────

data class LoginRequest(
    @SerializedName("email") val email: String,
    @SerializedName("password") val passcode: String
)

data class LoginResponse(
    @SerializedName("access_token") val accessToken: String,
    @SerializedName("refresh_token") val refreshToken: String,
    @SerializedName("token_type") val tokenType: String,
    @SerializedName("expires_in") val expiresIn: Int,
    @SerializedName("user") val user: UserInfo
)

data class UserInfo(
    @SerializedName("id") val id: Int,
    @SerializedName("faculty_id") val facultyId: Int?,
    @SerializedName("student_db_id") val studentDbId: Int?,
    @SerializedName("email") val email: String,
    @SerializedName("full_name") val fullName: String,
    @SerializedName("role") val role: String,
    @SerializedName("department") val department: String?
)

// ── Attendance Session Models ──────────────────────────────────────────

data class ActiveClassInfo(
    @SerializedName("timetable_id") val timetableId: Int,
    @SerializedName("faculty_id") val facultyId: Int,
    @SerializedName("faculty_name") val facultyName: String,
    @SerializedName("class_name") val className: String,
    @SerializedName("semester") val semester: String? = null,
    @SerializedName("subject_name") val subjectName: String,
    @SerializedName("day") val day: String,
    @SerializedName("start_time") val startTime: String,
    @SerializedName("end_time") val endTime: String,
    @SerializedName("room_number") val roomNumber: String?,
    @SerializedName("total_students") val totalStudents: Int
)

data class StartSessionRequest(
    @SerializedName("faculty_id") val facultyId: Int,
    @SerializedName("timetable_id") val timetableId: Int? = null
)

data class StopSessionRequest(
    @SerializedName("passcode") val passcode: String? = null
)

data class AttendanceSessionData(
    @SerializedName("id") val id: Int,
    @SerializedName("session_id") val sessionId: String,
    @SerializedName("faculty_id") val facultyId: Int,
    @SerializedName("timetable_id") val timetableId: Int,
    @SerializedName("class_name") val className: String,
    @SerializedName("subject_name") val subjectName: String,
    @SerializedName("total_students") val totalStudents: Int,
    @SerializedName("present_count") val presentCount: Int,
    @SerializedName("status") val status: String
)

data class FrameRecognitionResult(
    @SerializedName("session_id") val sessionId: String,
    @SerializedName("faces_detected") val facesDetected: Int,
    @SerializedName("recognized") val recognized: Int,
    @SerializedName("unknown") val unknown: Int,
    @SerializedName("total_present_in_session") val totalPresent: Int,
    @SerializedName("newly_marked") val newlyMarked: List<MatchedStudent>,
    @SerializedName("students") val students: List<MatchedStudent>
)

data class MatchedStudent(
    @SerializedName("person_id") val personId: String,
    @SerializedName("student_id") val studentId: String,
    @SerializedName("name") val name: String,
    @SerializedName("confidence") val confidence: Float,
    @SerializedName("confidence_pct") val confidencePct: Float,
    @SerializedName("status") val status: String
)

data class SessionSummary(
    @SerializedName("session_id") val sessionId: String,
    @SerializedName("status") val status: String,
    @SerializedName("total_students") val totalStudents: Int,
    @SerializedName("present_count") val presentCount: Int,
    @SerializedName("absent_count") val absentCount: Int,
    @SerializedName("attendance_percentage") val attendancePercentage: Float,
    @SerializedName("session_start") val sessionStart: String?,
    @SerializedName("session_end") val sessionEnd: String?
)

data class SessionResultsData(
    @SerializedName("session") val session: AttendanceSessionData,
    @SerializedName("records") val records: List<AttendanceRecordItem>
)

data class AttendanceRecordItem(
    @SerializedName("id") val id: Int?,
    @SerializedName("student_id") val studentId: String,
    @SerializedName("name") val name: String,
    @SerializedName("department") val department: String?,
    @SerializedName("status") val status: String,
    @SerializedName("confidence") val confidence: Float?,
    @SerializedName("timestamp") val timestamp: String?
)

data class UpdateRecordsRequest(
    @SerializedName("records") val records: List<RecordStatusUpdate>
)

data class RecordStatusUpdate(
    @SerializedName("student_id") val studentId: String,
    @SerializedName("status") val status: String
)

// ── Group Photo Review / Confirm (Upload -> Review -> Confirm) ─────────
// Mirrors the web app's multi_photo_attend (review, no commit) and
// confirm_attendance (commit + auto-register + email) two-step flow.

data class RosterEntry(
    @SerializedName("gr_number") val grNumber: String?,
    @SerializedName("name") val name: String?,
    @SerializedName("email") val email: String?,
    @SerializedName("department") val department: String?,
    @SerializedName("confidence") val confidence: Float?,
    @SerializedName("person_id") val personId: String? = null,
    @SerializedName("unregistered") val unregistered: Boolean = false
)

data class GroupReviewResult(
    @SerializedName("session_id") val sessionId: String,
    @SerializedName("total_faces") val totalFaces: Int,
    @SerializedName("recognized_count") val recognizedCount: Int,
    @SerializedName("unrecognized_count") val unrecognizedCount: Int,
    @SerializedName("present") val present: List<RosterEntry>,
    @SerializedName("absent") val absent: List<RosterEntry>,
    @SerializedName("annotated_images") val annotatedImages: List<String>
)

data class PresentEntryRequest(
    @SerializedName("gr_number") val grNumber: String?,
    @SerializedName("name") val name: String?,
    @SerializedName("confidence") val confidence: Float?,
    @SerializedName("person_id") val personId: String? = null
)

data class ConfirmAttendanceRequest(
    @SerializedName("present") val present: List<PresentEntryRequest>,
    @SerializedName("faculty_email") val facultyEmail: String?,
    @SerializedName("faculty_name") val facultyName: String?
)

data class MarkedEntry(
    @SerializedName("gr_number") val grNumber: String?,
    @SerializedName("name") val name: String?
)

data class EmailStatus(
    @SerializedName("present_sent") val presentSent: Boolean,
    @SerializedName("absent_sent") val absentSent: Boolean,
    @SerializedName("message") val message: String?
)

data class ConfirmAttendanceResult(
    @SerializedName("session_id") val sessionId: String,
    @SerializedName("marked") val marked: List<MarkedEntry>,
    @SerializedName("skipped") val skipped: List<MarkedEntry>,
    @SerializedName("present_count") val presentCount: Int,
    @SerializedName("email_status") val emailStatus: EmailStatus
)
