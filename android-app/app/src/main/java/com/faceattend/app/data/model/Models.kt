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
