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
import kotlinx.coroutines.launch

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
            }.onFailure {
                _sessionState.value = SessionUiState.Error(it.message ?: "Failed to start session")
            }
        }
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

    fun uploadGroupPhotos(sessionId: String, uris: List<android.net.Uri>, context: android.content.Context) {
        val selected = uris.take(3)
        if (selected.isEmpty()) return

        viewModelScope.launch {
            _isUploadingPhotos.value = true
            try {
                selected.forEachIndexed { index, uri ->
                    _uploadStatusMessage.value = "Processing photo ${index + 1} of ${selected.size}..."
                    val bytes = context.contentResolver.openInputStream(uri)?.use { it.readBytes() }
                    if (bytes != null && bytes.isNotEmpty()) {
                        val res = repository.captureGroupPhoto(sessionId, bytes)
                        res.onSuccess { result ->
                            _lastFrameResult.value = result
                            val current = _sessionState.value
                            if (current is SessionUiState.Active) {
                                _sessionState.value = SessionUiState.Active(
                                    current.session.copy(presentCount = result.totalPresent)
                                )
                            }
                        }
                    }
                }
                _uploadStatusMessage.value = "Successfully processed ${selected.size} photo(s)!"
            } catch (e: Exception) {
                _uploadStatusMessage.value = "Error uploading photos: ${e.message}"
            } finally {
                _isUploadingPhotos.value = false
            }
        }
    }

    fun clearUploadStatus() {
        _uploadStatusMessage.value = null
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

    fun exportAndShareCsv(sessionId: String, context: android.content.Context) {
        viewModelScope.launch {
            val res = repository.downloadCsvReport(sessionId)
            res.onSuccess { csvText ->
                try {
                    val file = java.io.File(context.cacheDir, "attendance_session_$sessionId.csv")
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

    fun stopSession(sessionId: String) {
        viewModelScope.launch {
            val res = repository.stopSession(sessionId)
            res.onSuccess {
                _sessionState.value = SessionUiState.Completed(it)
                loadSessionResults(sessionId)
            }.onFailure {
                _sessionState.value = SessionUiState.Error(it.message ?: "Failed to end session")
            }
        }
    }
}
