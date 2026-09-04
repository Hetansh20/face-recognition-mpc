package com.faceattend.app.ui.screens

import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.ImageFormat
import android.graphics.YuvImage
import android.net.Uri
import android.widget.Toast
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.camera.core.*
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.camera.view.PreviewView
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalLifecycleOwner
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.core.content.ContextCompat
import com.faceattend.app.data.model.MatchedStudent
import com.faceattend.app.ui.viewmodel.AttendanceViewModel
import com.faceattend.app.ui.viewmodel.SessionUiState
import java.io.ByteArrayOutputStream

@Composable
fun CameraAttendanceScreen(
    sessionId: String,
    className: String,
    subjectName: String,
    attendanceViewModel: AttendanceViewModel,
    onReviewPhotos: () -> Unit,
    onFinishSession: () -> Unit
) {
    val context = LocalContext.current
    val lifecycleOwner = LocalLifecycleOwner.current

    val lastResult by attendanceViewModel.lastFrameResult.collectAsState()
    val sessionState by attendanceViewModel.sessionState.collectAsState()
    val isRecognizing by attendanceViewModel.isRecognizing.collectAsState()
    val isUploadingPhotos by attendanceViewModel.isUploadingPhotos.collectAsState()
    val uploadStatusMessage by attendanceViewModel.uploadStatusMessage.collectAsState()
    val reviewState by attendanceViewModel.reviewState.collectAsState()
    val stopSessionError by attendanceViewModel.stopSessionError.collectAsState()

    var newlyMarkedList by remember { mutableStateOf<List<MatchedStudent>>(emptyList()) }
    var showStopDialog by remember { mutableStateOf(false) }
    var passcodeInput by remember { mutableStateOf("") }

    // Present count reflects the live-polled session state (matches the web
    // dashboard's 3s polling), falling back to the last live-frame result.
    val presentCount = (sessionState as? SessionUiState.Active)?.session?.presentCount
        ?: lastResult?.totalPresent ?: 0

    // Launcher for selecting up to 3 photos
    val photoPickerLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.GetMultipleContents()
    ) { uris: List<Uri> ->
        if (uris.isNotEmpty()) {
            val selected = uris.take(3)
            Toast.makeText(context, "Analyzing ${selected.size} photo(s)...", Toast.LENGTH_SHORT).show()
            attendanceViewModel.uploadAndReviewPhotos(sessionId, selected, context)
        }
    }

    LaunchedEffect(lastResult) {
        lastResult?.let { res ->
            if (res.newlyMarked.isNotEmpty()) {
                newlyMarkedList = (res.newlyMarked + newlyMarkedList).distinctBy { it.studentId }
            }
        }
    }

    // Navigate to the review screen once photos have been analyzed
    LaunchedEffect(reviewState) {
        if (reviewState != null) {
            onReviewPhotos()
        }
    }

    LaunchedEffect(stopSessionError) {
        stopSessionError?.let {
            Toast.makeText(context, it, Toast.LENGTH_LONG).show()
            attendanceViewModel.clearStopSessionError()
        }
    }

    // Only navigate away once the session has actually stopped (correct passcode)
    LaunchedEffect(sessionState) {
        if (sessionState is SessionUiState.Completed) {
            onFinishSession()
        }
    }

    Box(modifier = Modifier.fillMaxSize().background(Color(0xFF090D16))) {
        // CameraX Preview View
        AndroidView(
            factory = { ctx ->
                val previewView = PreviewView(ctx)
                val cameraProviderFuture = ProcessCameraProvider.getInstance(ctx)

                cameraProviderFuture.addListener({
                    val cameraProvider = cameraProviderFuture.get()
                    val preview = Preview.Builder().build().also {
                        it.setSurfaceProvider(previewView.surfaceProvider)
                    }

                    val imageAnalysis = ImageAnalysis.Builder()
                        .setBackpressureStrategy(ImageAnalysis.STRATEGY_KEEP_ONLY_LATEST)
                        .build()

                    imageAnalysis.setAnalyzer(ContextCompat.getMainExecutor(ctx)) { imageProxy ->
                        val jpegBytes = imageProxy.toJpegByteArray()
                        if (jpegBytes != null && !isRecognizing && !isUploadingPhotos) {
                            attendanceViewModel.processFrame(sessionId, jpegBytes)
                        }
                        imageProxy.close()
                    }

                    try {
                        cameraProvider.unbindAll()
                        cameraProvider.bindToLifecycle(
                            lifecycleOwner,
                            CameraSelector.DEFAULT_BACK_CAMERA,
                            preview,
                            imageAnalysis
                        )
                    } catch (e: Exception) {
                        e.printStackTrace()
                    }
                }, ContextCompat.getMainExecutor(ctx))

                previewView
            },
            modifier = Modifier.fillMaxSize()
        )

        // Overlay Session Banner
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(16.dp),
            verticalArrangement = Arrangement.SpaceBetween
        ) {
            // Top Bar Stats
            Card(
                shape = RoundedCornerShape(16.dp),
                colors = CardDefaults.cardColors(containerColor = Color(0xFF0F172A).copy(alpha = 0.90f)),
                modifier = Modifier.fillMaxWidth()
            ) {
                Row(
                    modifier = Modifier.padding(16.dp).fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Column {
                        Text(
                            text = subjectName,
                            fontSize = 16.sp,
                            fontWeight = FontWeight.Bold,
                            color = Color.White
                        )
                        Text(
                            text = className,
                            fontSize = 12.sp,
                            color = Color(0xFFA5B4FC)
                        )
                    }

                    Surface(
                        color = Color(0xFF10B981).copy(alpha = 0.2f),
                        shape = RoundedCornerShape(12.dp)
                    ) {
                        Text(
                            text = "PRESENT: $presentCount",
                            color = Color(0xFF34D399),
                            fontWeight = FontWeight.Bold,
                            fontSize = 14.sp,
                            modifier = Modifier.padding(horizontal = 12.dp, vertical = 6.dp)
                        )
                    }
                }
            }

            // Bottom Feed & Action Buttons
            Column(modifier = Modifier.fillMaxWidth()) {
                // Status banner if photos are uploading
                if (!uploadStatusMessage.isNullOrEmpty()) {
                    Card(
                        shape = RoundedCornerShape(10.dp),
                        colors = CardDefaults.cardColors(containerColor = Color(0xFF312E81)),
                        modifier = Modifier.fillMaxWidth().padding(bottom = 8.dp)
                    ) {
                        Row(
                            modifier = Modifier.padding(12.dp),
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            if (isUploadingPhotos) {
                                CircularProgressIndicator(color = Color.White, modifier = Modifier.size(16.dp))
                                Spacer(modifier = Modifier.width(8.dp))
                            }
                            Text(
                                text = uploadStatusMessage!!,
                                color = Color.White,
                                fontSize = 13.sp,
                                fontWeight = FontWeight.Medium
                            )
                        }
                    }
                }

                if (newlyMarkedList.isNotEmpty()) {
                    Text(
                        text = "RECENT RECOGNITIONS",
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Bold,
                        color = Color(0xFF94A3B8),
                        modifier = Modifier.padding(bottom = 6.dp)
                    )
                    LazyColumn(
                        modifier = Modifier
                            .fillMaxWidth()
                            .heightIn(max = 130.dp)
                            .padding(bottom = 12.dp)
                    ) {
                        items(newlyMarkedList.take(3)) { student ->
                            Card(
                                shape = RoundedCornerShape(10.dp),
                                colors = CardDefaults.cardColors(containerColor = Color(0xFF1E293B).copy(alpha = 0.85f)),
                                modifier = Modifier.fillMaxWidth().padding(vertical = 3.dp)
                            ) {
                                Row(
                                    modifier = Modifier.padding(horizontal = 12.dp, vertical = 8.dp),
                                    horizontalArrangement = Arrangement.SpaceBetween
                                ) {
                                    Text(text = student.name, fontWeight = FontWeight.Bold, color = Color.White, fontSize = 13.sp)
                                    Text(text = "${student.confidencePct.toInt()}% match", color = Color(0xFF818CF8), fontSize = 12.sp)
                                }
                            }
                        }
                    }
                }

                // Action Buttons Row
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(10.dp)
                ) {
                    Button(
                        onClick = { photoPickerLauncher.launch("image/*") },
                        enabled = !isUploadingPhotos,
                        shape = RoundedCornerShape(14.dp),
                        colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF6366F1)),
                        modifier = Modifier.weight(1f).height(52.dp)
                    ) {
                        Text(
                            text = if (isUploadingPhotos) "Uploading..." else "Upload Photos (Max 3)",
                            fontWeight = FontWeight.Bold,
                            fontSize = 13.sp,
                            color = Color.White
                        )
                    }

                    Button(
                        onClick = { showStopDialog = true },
                        shape = RoundedCornerShape(14.dp),
                        colors = ButtonDefaults.buttonColors(containerColor = Color(0xFFF43F5E)),
                        modifier = Modifier.weight(1f).height(52.dp)
                    ) {
                        Text("End Session", fontWeight = FontWeight.Bold, fontSize = 14.sp, color = Color.White)
                    }
                }
            }
        }

        // Re-auth gate before stopping the session, mirroring the web
        // app's passcode confirmation on /api/faculty/stop_session
        if (showStopDialog) {
            AlertDialog(
                onDismissRequest = { showStopDialog = false; passcodeInput = "" },
                title = { Text("Confirm End Session") },
                text = {
                    Column {
                        Text("Re-enter your passcode to end this class and export attendance.")
                        Spacer(modifier = Modifier.height(12.dp))
                        OutlinedTextField(
                            value = passcodeInput,
                            onValueChange = { passcodeInput = it },
                            label = { Text("Passcode") },
                            visualTransformation = androidx.compose.ui.text.input.PasswordVisualTransformation(),
                            singleLine = true,
                            modifier = Modifier.fillMaxWidth()
                        )
                    }
                },
                confirmButton = {
                    TextButton(onClick = {
                        showStopDialog = false
                        attendanceViewModel.stopSession(sessionId, passcodeInput)
                        passcodeInput = ""
                    }) { Text("End Session") }
                },
                dismissButton = {
                    TextButton(onClick = { showStopDialog = false; passcodeInput = "" }) { Text("Cancel") }
                }
            )
        }
    }
}

// Convert CameraX ImageProxy to Jpeg ByteArray
private fun ImageProxy.toJpegByteArray(): ByteArray? {
    return try {
        val yBuffer = planes[0].buffer
        val uBuffer = planes[1].buffer
        val vBuffer = planes[2].buffer

        val ySize = yBuffer.remaining()
        val uSize = uBuffer.remaining()
        val vSize = vBuffer.remaining()

        val nv21 = ByteArray(ySize + uSize + vSize)

        yBuffer.get(nv21, 0, ySize)
        vBuffer.get(nv21, ySize, vSize)
        uBuffer.get(nv21, ySize + vSize, uSize)

        val yuvImage = YuvImage(nv21, ImageFormat.NV21, this.width, this.height, null)
        val out = ByteArrayOutputStream()
        yuvImage.compressToJpeg(android.graphics.Rect(0, 0, yuvImage.width, yuvImage.height), 85, out)
        out.toByteArray()
    } catch (e: Exception) {
        null
    }
}
