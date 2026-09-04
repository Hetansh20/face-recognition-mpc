package com.faceattend.app.ui.viewmodel

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.faceattend.app.data.model.*
import com.faceattend.app.data.repository.AttendanceRepository
import com.faceattend.app.data.repository.AuthRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch
import kotlinx.coroutines.delay
import kotlinx.coroutines.Job

// ── Auth ViewModel ───────────────────────────────────────────────────

sealed class AuthUiState {
    object Idle : AuthUiState()
    object Loading : AuthUiState()
    data class Success(val user: UserInfo) : AuthUiState()
    data class Error(val message: String) : AuthUiState()
}

class AuthViewModel(application: Application) : AndroidViewModel(application) {
    private val repository = AuthRepository(application)

    private val _uiState = MutableStateFlow<AuthUiState>(
        if (repository.isLoggedIn()) AuthUiState.Success(
            UserInfo(0, repository.getFacultyId(), null, "", repository.getUserName(), repository.getUserRole(), null)
        ) else AuthUiState.Idle
    )
    val uiState: StateFlow<AuthUiState> = _uiState.asStateFlow()

    fun login(email: String, passcode: String) {
        viewModelScope.launch {
            _uiState.value = AuthUiState.Loading
            val result = repository.login(email, passcode)
            result.onSuccess {
                _uiState.value = AuthUiState.Success(it.user)
            }.onFailure {
                _uiState.value = AuthUiState.Error(it.message ?: "Authentication failed")
            }
        }
    }

    fun logout() {
        repository.logout()
        _uiState.value = AuthUiState.Idle
    }

    fun getFacultyId(): Int = repository.getFacultyId()
    fun getUserName(): String = repository.getUserName()
    fun getUserEmail(): String = repository.getUserEmail()
}

// ── Attendance ViewModel ─────────────────────────────────────────────

sealed class ActiveClassUiState {
    object Loading : ActiveClassUiState()
    data class Success(val classInfo: ActiveClassInfo) : ActiveClassUiState()
    data class NoClass(val message: String) : ActiveClassUiState()
    data class Error(val message: String) : ActiveClassUiState()
}

sealed class SessionUiState {
    object Inactive : SessionUiState()
    object Starting : SessionUiState()
    data class Active(val session: AttendanceSessionData) : SessionUiState()
    data class Completed(val summary: SessionSummary) : SessionUiState()
    data class Error(val message: String) : SessionUiState()
}

class AttendanceViewModel(application: Application) : AndroidViewModel(application) {
    private val repository = AttendanceRepository(application)

    private val _activeClassState = MutableStateFlow<ActiveClassUiState>(ActiveClassUiState.Loading)
    val activeClassState: StateFlow<ActiveClassUiState> = _activeClassState.asStateFlow()

    private val _sessionState = MutableStateFlow<SessionUiState>(SessionUiState.Inactive)
    val sessionState: StateFlow<SessionUiState> = _sessionState.asStateFlow()

    private val _lastFrameResult = MutableStateFlow<FrameRecognitionResult?>(null)
    val lastFrameResult: StateFlow<FrameRecognitionResult?> = _lastFrameResult.asStateFlow()

    private val _isRecognizing = MutableStateFlow(false)
    val isRecognizing: StateFlow<Boolean> = _isRecognizing.asStateFlow()

    fun loadActiveClass(facultyId: Int) {
        viewModelScope.launch {
            _activeClassState.value = ActiveClassUiState.Loading
            val res = repository.getActiveClass(facultyId)
            res.onSuccess {
                _activeClassState.value = ActiveClassUiState.Success(it)
            }.onFailure {
                _activeClassState.value = ActiveClassUiState.NoClass("No active scheduled class for this time slot.")
            }
        }
    }

    fun startAttendanceSession(facultyId: Int, timetableId: Int) {
        viewModelScope.launch {
            _sessionState.value = SessionUiState.Starting
            val res = repository.startSession(facultyId, timetableId)
            res.onSuccess {
                _sessionState.value = SessionUiState.Active(it)
                startPresentCountPolling(it.sessionId)
            }.onFailure {
                _sessionState.value = SessionUiState.Error(it.message ?: "Failed to start session")
            }
        }
    }

    private var pollingJob: Job? = null

    /** Polls session results every 3s while active, mirroring the web
     * dashboard's setInterval on /api/faculty/session_status — keeps the
     * present count fresh even if attendance is marked by another route. */
    private fun startPresentCountPolling(sessionId: String) {
        pollingJob?.cancel()
        pollingJob = viewModelScope.launch {
            while (isActive) {
                delay(3000)
                val current = _sessionState.value
                if (current !is SessionUiState.Active) break
                repository.getSessionResults(sessionId).onSuccess { results ->
                    _sessionState.value = SessionUiState.Active(results.session)
                }
            }
        }
    }

    private fun stopPresentCountPolling() {
        pollingJob?.cancel()
        pollingJob = null
    }

    fun processFrame(sessionId: String, jpegBytes: ByteArray) {
        if (_isRecognizing.value) return
        _isRecognizing.value = true

        viewModelScope.launch {
            try {
                val res = repository.recognizeFrame(sessionId, jpegBytes)
                res.onSuccess {
                    _lastFrameResult.value = it
                    // Update present count in state if active
                    val current = _sessionState.value
                    if (current is SessionUiState.Active) {
                        _sessionState.value = SessionUiState.Active(
                            current.session.copy(presentCount = it.totalPresent)
                        )
                    }
                }
            } finally {
                _isRecognizing.value = false
            }
        }
    }

    private val _isUploadingPhotos = MutableStateFlow(false)
    val isUploadingPhotos: StateFlow<Boolean> = _isUploadingPhotos.asStateFlow()

    private val _uploadStatusMessage = MutableStateFlow<String?>(null)
    val uploadStatusMessage: StateFlow<String?> = _uploadStatusMessage.asStateFlow()

    // ── Upload -> Review -> Confirm (group photo attendance) ────────────
    // Mirrors the web app's 3-step flow: upload up to 3 photos, review the
    // recognized present/absent lists (with annotated bounding-box images),
    // let the faculty edit them, then confirm to commit + email CSVs.

    private val _reviewState = MutableStateFlow<GroupReviewResult?>(null)
    val reviewState: StateFlow<GroupReviewResult?> = _reviewState.asStateFlow()

    private val _isConfirming = MutableStateFlow(false)
    val isConfirming: StateFlow<Boolean> = _isConfirming.asStateFlow()

    private val _confirmResult = MutableStateFlow<ConfirmAttendanceResult?>(null)
    val confirmResult: StateFlow<ConfirmAttendanceResult?> = _confirmResult.asStateFlow()

    fun uploadAndReviewPhotos(sessionId: String, uris: List<android.net.Uri>, context: android.content.Context) {
        val selected = uris.take(3)
        if (selected.isEmpty()) return

        viewModelScope.launch {
            _isUploadingPhotos.value = true
            _uploadStatusMessage.value = "Analyzing ${selected.size} photo(s)..."
            try {
                val photoBytes = selected.mapNotNull { uri ->
                    context.contentResolver.openInputStream(uri)?.use { it.readBytes() }
                }
                if (photoBytes.isEmpty()) {
                    _uploadStatusMessage.value = "Could not read selected photos."
                    return@launch
                }
                val res = repository.reviewGroupPhotos(sessionId, photoBytes)
                res.onSuccess { review ->
                    _reviewState.value = review
                    _uploadStatusMessage.value = null
                }.onFailure { err ->
                    _uploadStatusMessage.value = "Error analyzing photos: ${err.message}"
                }
            } finally {
                _isUploadingPhotos.value = false
            }
        }
    }

    fun clearReview() {
        _reviewState.value = null
        _confirmResult.value = null
    }

    fun clearUploadStatus() {
        _uploadStatusMessage.value = null
    }

    fun confirmAttendance(
        sessionId: String,
        present: List<RosterEntry>,
        facultyEmail: String?,
        facultyName: String?,
        onComplete: (() -> Unit)? = null
    ) {
        viewModelScope.launch {
            _isConfirming.value = true
            try {
                val entries = present.map { PresentEntryRequest(it.grNumber, it.name, it.confidence, it.personId) }
                val res = repository.confirmAttendance(sessionId, entries, facultyEmail, facultyName)
                res.onSuccess { result ->
                    _confirmResult.value = result
                    val current = _sessionState.value
                    if (current is SessionUiState.Active) {
                        _sessionState.value = SessionUiState.Active(
                            current.session.copy(presentCount = result.presentCount)
                        )
                    }
                    onComplete?.invoke()
                }.onFailure { err ->
                    _uploadStatusMessage.value = "Error confirming attendance: ${err.message}"
                }
            } finally {
                _isConfirming.value = false
            }
        }
    }

    private val _sessionResultsState = MutableStateFlow<SessionResultsData?>(null)
    val sessionResultsState: StateFlow<SessionResultsData?> = _sessionResultsState.asStateFlow()

    private val _isSavingRecords = MutableStateFlow(false)
    val isSavingRecords: StateFlow<Boolean> = _isSavingRecords.asStateFlow()

    fun loadSessionResults(sessionId: String) {
        viewModelScope.launch {
            val res = repository.getSessionResults(sessionId)
            res.onSuccess {
                _sessionResultsState.value = it
            }
        }
    }

    fun saveAttendanceEdits(sessionId: String, updates: List<RecordStatusUpdate>, onComplete: (() -> Unit)? = null) {
        viewModelScope.launch {
            _isSavingRecords.value = true
            try {
                val res = repository.updateSessionRecords(sessionId, updates)
                res.onSuccess { updated ->
                    _sessionResultsState.value = updated
                    onComplete?.invoke()
                }
            } finally {
                _isSavingRecords.value = false
            }
        }
    }

    fun exportAndShareCsv(sessionId: String, context: android.content.Context, absent: Boolean = false) {
        viewModelScope.launch {
            val res = if (absent) repository.downloadAbsentCsvReport(sessionId) else repository.downloadPresentCsvReport(sessionId)
            res.onSuccess { csvText ->
                try {
                    val suffix = if (absent) "absent" else "present"
                    val file = java.io.File(context.cacheDir, "attendance_${suffix}_$sessionId.csv")
                    file.writeText(csvText)
                    val uri = androidx.core.content.FileProvider.getUriForFile(
                        context,
                        "${context.packageName}.fileprovider",
                        file
                    )
                    val intent = android.content.Intent(android.content.Intent.ACTION_SEND).apply {
                        type = "text/csv"
                        putExtra(android.content.Intent.EXTRA_STREAM, uri)
                        addFlags(android.content.Intent.FLAG_GRANT_READ_URI_PERMISSION)
                    }
                    val chooser = android.content.Intent.createChooser(intent, "Export Attendance CSV")
                    chooser.addFlags(android.content.Intent.FLAG_ACTIVITY_NEW_TASK)
                    context.startActivity(chooser)
                } catch (e: Exception) {
                    android.widget.Toast.makeText(context, "Error sharing CSV: ${e.message}", android.widget.Toast.LENGTH_LONG).show()
                }
            }.onFailure { err ->
                android.widget.Toast.makeText(context, "Failed to download CSV: ${err.message}", android.widget.Toast.LENGTH_LONG).show()
            }
        }
    }

    private val _stopSessionError = MutableStateFlow<String?>(null)
    val stopSessionError: StateFlow<String?> = _stopSessionError.asStateFlow()

    fun clearStopSessionError() {
        _stopSessionError.value = null
    }

    /** Requires the faculty to re-enter their passcode before ending a
     * session, mirroring the web app's /api/faculty/stop_session re-auth gate. */
    fun stopSession(sessionId: String, passcode: String) {
        viewModelScope.launch {
            val res = repository.stopSession(sessionId, passcode)
            res.onSuccess {
                stopPresentCountPolling()
                _sessionState.value = SessionUiState.Completed(it)
                loadSessionResults(sessionId)
            }.onFailure {
                _stopSessionError.value = it.message ?: "Failed to end session"
            }
        }
    }
}
