package com.faceattend.app.data.api

import android.content.Context
import android.content.SharedPreferences
import com.faceattend.app.data.model.*
import okhttp3.Interceptor
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.MultipartBody
import okhttp3.OkHttpClient
import okhttp3.RequestBody.Companion.toRequestBody
import okhttp3.Response
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import retrofit2.http.*
import java.util.UUID
import java.util.concurrent.TimeUnit

// ── Retrofit Interfaces ───────────────────────────────────────────────

interface AuthApiService {
    @POST("auth/login")
    suspend fun login(@Body request: LoginRequest): ApiResponse<LoginResponse>

    @GET("auth/me")
    suspend fun getProfile(): ApiResponse<UserInfo>
}

interface TimetableApiService {
    @GET("timetables/active")
    suspend fun getActiveClass(@Query("faculty_id") facultyId: Int): ApiResponse<ActiveClassInfo>
}

interface AttendanceApiService {
    @POST("attendance/sessions/start")
    suspend fun startSession(@Body request: StartSessionRequest): ApiResponse<AttendanceSessionData>

    @Multipart
    @POST("attendance/sessions/{id}/recognize")
    suspend fun recognizeFrame(
        @Path("id") sessionId: String,
        @Part image: MultipartBody.Part
    ): ApiResponse<FrameRecognitionResult>

    @Multipart
    @POST("attendance/sessions/{id}/capture")
    suspend fun captureGroupPhoto(
        @Path("id") sessionId: String,
        @Part image: MultipartBody.Part
    ): ApiResponse<FrameRecognitionResult>

    @Multipart
    @POST("attendance/sessions/{id}/review")
    suspend fun reviewGroupPhotos(
        @Path("id") sessionId: String,
        @Part images: List<MultipartBody.Part>
    ): ApiResponse<GroupReviewResult>

    @POST("attendance/sessions/{id}/confirm")
    suspend fun confirmAttendance(
        @Path("id") sessionId: String,
        @Body request: ConfirmAttendanceRequest
    ): ApiResponse<ConfirmAttendanceResult>

    @POST("attendance/sessions/{id}/stop")
    suspend fun stopSession(
        @Path("id") sessionId: String,
        @Body request: StopSessionRequest
    ): ApiResponse<SessionSummary>

    @GET("attendance/sessions/{id}/results")
    suspend fun getSessionResults(@Path("id") sessionId: String): ApiResponse<SessionResultsData>

    @POST("attendance/sessions/{id}/update-records")
    suspend fun updateSessionRecords(
        @Path("id") sessionId: String,
        @Body request: UpdateRecordsRequest
    ): ApiResponse<SessionResultsData>

    @GET("reports/export/session-csv")
    suspend fun exportSessionPresentCsv(
        @Query("session_id") sessionId: String
    ): okhttp3.ResponseBody

    @GET("reports/export/session-absent-csv")
    suspend fun exportSessionAbsentCsv(
        @Query("session_id") sessionId: String
    ): okhttp3.ResponseBody
}

// ── OkHttp Auth Interceptor ───────────────────────────────────────────

class AuthInterceptor(private val prefs: SharedPreferences) : Interceptor {
    override fun intercept(chain: Interceptor.Chain): Response {
        val original = chain.request()
        val token = prefs.getString("access_token", null)
        val deviceId = prefs.getString("device_id", UUID.randomUUID().toString()).also {
            prefs.edit().putString("device_id", it).apply()
        }

        val deviceModel = "${android.os.Build.MANUFACTURER.replaceFirstChar { if (it.isLowerCase()) it.titlecase() else it.toString() }} ${android.os.Build.MODEL}"
        val osVersion = "Android ${android.os.Build.VERSION.RELEASE} (API ${android.os.Build.VERSION.SDK_INT})"

        val builder = original.newBuilder()
            .header("X-Request-ID", "android-" + UUID.randomUUID().toString().take(12))
            .header("X-Device-ID", deviceId ?: "android-device")
            .header("X-Device-Model", deviceModel)
            .header("X-OS-Version", osVersion)
            .header("X-App-Version", "v1.0.0")

        if (!token.isNull_or_Empty()) {
            builder.header("Authorization", "Bearer $token")
        }

        return chain.proceed(builder.build())
    }
}

private fun String?.isNull_or_Empty() = this == null || this.isEmpty()

// ── ApiClient Singleton ──────────────────────────────────────────────

object ApiClient {
    private var cachedRetrofit: Retrofit? = null
    private var cachedBaseUrl: String? = null

    fun getBaseUrl(context: Context): String {
        val prefs = context.getSharedPreferences("faceattend_prefs", Context.MODE_PRIVATE)
        return prefs.getString("server_url", "http://10.101.79.81:5000/api/v1/")
            ?: "http://10.101.79.81:5000/api/v1/"
    }

    fun setServerAddress(address: String, context: Context) {
        var clean = address.trim()
        if (clean.isEmpty()) return

        if (!clean.startsWith("http://") && !clean.startsWith("https://")) {
            clean = "http://$clean"
        }
        if (!clean.contains("/api/v1")) {
            clean = if (clean.endsWith("/")) "${clean}api/v1/" else "$clean/api/v1/"
        }
        if (!clean.endsWith("/")) {
            clean = "$clean/"
        }

        val prefs = context.getSharedPreferences("faceattend_prefs", Context.MODE_PRIVATE)
        prefs.edit().putString("server_url", clean).apply()

        cachedBaseUrl = null
        cachedRetrofit = null
    }

    private fun getRetrofit(context: Context): Retrofit {
        val currentBaseUrl = getBaseUrl(context)
        if (cachedRetrofit == null || cachedBaseUrl != currentBaseUrl) {
            cachedBaseUrl = currentBaseUrl
            val prefs = context.getSharedPreferences("faceattend_prefs", Context.MODE_PRIVATE)
            val logging = HttpLoggingInterceptor().apply {
                level = HttpLoggingInterceptor.Level.BODY
            }
            val okHttpClient = OkHttpClient.Builder()
                .addInterceptor(AuthInterceptor(prefs))
                .addInterceptor(logging)
                .connectTimeout(15, TimeUnit.SECONDS)
                .readTimeout(30, TimeUnit.SECONDS)
                .writeTimeout(30, TimeUnit.SECONDS)
                .build()

            cachedRetrofit = Retrofit.Builder()
                .baseUrl(currentBaseUrl)
                .client(okHttpClient)
                .addConverterFactory(GsonConverterFactory.create())
                .build()
        }
        return cachedRetrofit!!
    }

    fun getAuthApi(context: Context): AuthApiService = getRetrofit(context).create(AuthApiService::class.java)
    fun getTimetableApi(context: Context): TimetableApiService = getRetrofit(context).create(TimetableApiService::class.java)
    fun getAttendanceApi(context: Context): AttendanceApiService = getRetrofit(context).create(AttendanceApiService::class.java)
}

