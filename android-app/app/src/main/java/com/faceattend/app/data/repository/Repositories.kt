package com.faceattend.app.data.repository

import android.content.Context
import com.faceattend.app.data.api.ApiClient
import com.faceattend.app.data.model.*
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.MultipartBody
import okhttp3.RequestBody.Companion.toRequestBody

class AuthRepository(private val context: Context) {
    private val authApi get() = ApiClient.getAuthApi(context)
    private val prefs = context.getSharedPreferences("faceattend_prefs", Context.MODE_PRIVATE)


    suspend fun login(email: String, passcode: String): Result<LoginResponse> {
        return try {
            val res = authApi.login(LoginRequest(email, passcode))
            if (res.success && res.data != null) {
                val resolvedFacultyId = res.data.user.facultyId ?: (if (res.data.user.role == "FACULTY") (if (res.data.user.id > 0) res.data.user.id else 1) else 0)
                prefs.edit().apply {
                    putString("access_token", res.data.accessToken)
                    putString("refresh_token", res.data.refreshToken)
                    putInt("faculty_id", resolvedFacultyId)
                    putString("user_name", res.data.user.fullName)
                    putString("user_email", res.data.user.email)
                    putString("user_role", res.data.user.role)
                    apply()
                }
                Result.success(res.data)
            } else {
                Result.failure(Exception(res.error?.message ?: "Login failed"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    fun isLoggedIn(): Boolean {
        return !prefs.getString("access_token", null).isNullOrEmpty()
    }

    fun logout() {
        // Clear only session/identity keys — NOT the whole prefs blob, which
        // would also wipe the user-configured server_url and device_id
        // (previously caused the app to silently revert to the hardcoded
        // default server address on every logout).
        prefs.edit()
            .remove("access_token")
            .remove("refresh_token")
            .remove("faculty_id")
            .remove("user_name")
            .remove("user_email")
            .remove("user_role")
            .apply()
    }

    fun getFacultyId(): Int = prefs.getInt("faculty_id", 0)
    fun getUserName(): String = prefs.getString("user_name", "Faculty") ?: "Faculty"
    fun getUserEmail(): String = prefs.getString("user_email", "") ?: ""
    fun getUserRole(): String = prefs.getString("user_role", "FACULTY") ?: "FACULTY"
}

class AttendanceRepository(private val context: Context) {
    private val timetableApi get() = ApiClient.getTimetableApi(context)
    private val attendanceApi get() = ApiClient.getAttendanceApi(context)

    suspend fun getActiveClass(facultyId: Int): Result<ActiveClassInfo> {
        return try {
            val res = timetableApi.getActiveClass(facultyId)
            if (res.success && res.data != null) {
                Result.success(res.data)
            } else {
                Result.failure(Exception(res.error?.message ?: "No active class found"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    suspend fun startSession(facultyId: Int, timetableId: Int): Result<AttendanceSessionData> {
        return try {
            val res = attendanceApi.startSession(StartSessionRequest(facultyId, timetableId))
            if (res.success && res.data != null) {
                Result.success(res.data)
            } else {
                Result.failure(Exception(res.error?.message ?: "Could not start session"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    suspend fun recognizeFrame(sessionId: String, jpegBytes: ByteArray): Result<FrameRecognitionResult> {
        return try {
            val reqBody = jpegBytes.toRequestBody("image/jpeg".toMediaTypeOrNull())
            val part = MultipartBody.Part.createFormData("image", "frame.jpg", reqBody)
            val res = attendanceApi.recognizeFrame(sessionId, part)
            if (res.success && res.data != null) {
                Result.success(res.data)
            } else {
                Result.failure(Exception(res.error?.message ?: "Frame processing error"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    suspend fun captureGroupPhoto(sessionId: String, jpegBytes: ByteArray): Result<FrameRecognitionResult> {
        return try {
            val reqBody = jpegBytes.toRequestBody("image/jpeg".toMediaTypeOrNull())
            val part = MultipartBody.Part.createFormData("image", "group_photo.jpg", reqBody)
            val res = attendanceApi.captureGroupPhoto(sessionId, part)
            if (res.success && res.data != null) {
                Result.success(res.data)
            } else {
                recognizeFrame(sessionId, jpegBytes)
            }
        } catch (e: Exception) {
            recognizeFrame(sessionId, jpegBytes)
        }
    }

    /** Upload -> Review step: runs recognition on up to 3 photos WITHOUT
     * marking attendance yet, mirroring the web app's multi_photo_attend. */
    suspend fun reviewGroupPhotos(sessionId: String, photos: List<ByteArray>): Result<GroupReviewResult> {
        return try {
            val parts = photos.mapIndexed { index, bytes ->
                val reqBody = bytes.toRequestBody("image/jpeg".toMediaTypeOrNull())
                MultipartBody.Part.createFormData("image_$index", "photo_$index.jpg", reqBody)
            }
            val res = attendanceApi.reviewGroupPhotos(sessionId, parts)
            if (res.success && res.data != null) {
                Result.success(res.data)
            } else {
                Result.failure(Exception(res.error?.message ?: "Could not process photos"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    /** Review -> Confirm step: commits the faculty-edited present list and
     * emails present/absent CSVs to the faculty, mirroring the web app's
     * confirm_attendance. */
    suspend fun confirmAttendance(
        sessionId: String,
        present: List<PresentEntryRequest>,
        facultyEmail: String?,
        facultyName: String?
    ): Result<ConfirmAttendanceResult> {
        return try {
            val res = attendanceApi.confirmAttendance(
                sessionId,
                ConfirmAttendanceRequest(present, facultyEmail, facultyName)
            )
            if (res.success && res.data != null) {
                Result.success(res.data)
            } else {
                Result.failure(Exception(res.error?.message ?: "Could not confirm attendance"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    suspend fun stopSession(sessionId: String, passcode: String? = null): Result<SessionSummary> {
        return try {
            val res = attendanceApi.stopSession(sessionId, StopSessionRequest(passcode))
            if (res.success && res.data != null) {
                Result.success(res.data)
            } else {
                Result.failure(Exception(res.error?.message ?: "Could not stop session"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    suspend fun getSessionResults(sessionId: String): Result<SessionResultsData> {
        return try {
            val res = attendanceApi.getSessionResults(sessionId)
            if (res.success && res.data != null) {
                Result.success(res.data)
            } else {
                Result.failure(Exception(res.error?.message ?: "Could not load session results"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    suspend fun updateSessionRecords(sessionId: String, updates: List<RecordStatusUpdate>): Result<SessionResultsData> {
        return try {
            val res = attendanceApi.updateSessionRecords(sessionId, UpdateRecordsRequest(updates))
            if (res.success && res.data != null) {
                Result.success(res.data)
            } else {
                Result.failure(Exception(res.error?.message ?: "Could not update attendance records"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    suspend fun downloadPresentCsvReport(sessionId: String): Result<String> {
        return try {
            Result.success(attendanceApi.exportSessionPresentCsv(sessionId).string())
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    suspend fun downloadAbsentCsvReport(sessionId: String): Result<String> {
        return try {
            Result.success(attendanceApi.exportSessionAbsentCsv(sessionId).string())
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
}
