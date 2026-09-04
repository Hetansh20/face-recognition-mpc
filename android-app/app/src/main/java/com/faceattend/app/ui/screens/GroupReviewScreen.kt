package com.faceattend.app.ui.screens

import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.util.Base64
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.draw.clip
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.faceattend.app.data.model.RosterEntry
import com.faceattend.app.ui.viewmodel.AttendanceViewModel

/**
 * Upload -> Review -> Confirm group photo attendance, mirroring the web
 * app's faculty_active_session.html 3-step flow: a stats bar (Faces
 * Detected / Recognized / Unknown / Absent), an annotated bounding-box
 * image carousel, and clickable Present/Absent columns the faculty can
 * edit before confirming (which commits attendance and emails CSVs).
 */
@Composable
fun GroupReviewScreen(
    sessionId: String,
    className: String,
    facultyEmail: String,
    facultyName: String,
    attendanceViewModel: AttendanceViewModel,
    onConfirmed: () -> Unit,
    onBack: () -> Unit
) {
    val review by attendanceViewModel.reviewState.collectAsState()
    val isConfirming by attendanceViewModel.isConfirming.collectAsState()
    val confirmResult by attendanceViewModel.confirmResult.collectAsState()

    var presentList by remember { mutableStateOf<List<RosterEntry>>(emptyList()) }
    var absentList by remember { mutableStateOf<List<RosterEntry>>(emptyList()) }

    LaunchedEffect(review) {
        review?.let {
            presentList = it.present
            absentList = it.absent
        }
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(Color(0xFF090D16))
            .padding(16.dp)
    ) {
        val currentReview = review
        val result = confirmResult

        when {
            currentReview == null -> {
                Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                    CircularProgressIndicator(color = Color(0xFF6366F1))
                }
            }

            result != null -> {
                ConfirmDonePane(result = result, onContinue = onConfirmed)
            }

            else -> {
                Text(
                    text = "Review Attendance — $className",
                    fontSize = 18.sp,
                    fontWeight = FontWeight.Bold,
                    color = Color.White,
                    modifier = Modifier.padding(bottom = 12.dp)
                )

                StatsBar(
                    totalFaces = currentReview.totalFaces,
                    recognized = presentList.size,
                    unrecognized = currentReview.unrecognizedCount,
                    absent = absentList.size
                )

                Spacer(modifier = Modifier.height(12.dp))

                if (currentReview.annotatedImages.isNotEmpty()) {
                    AnnotatedImageCarousel(currentReview.annotatedImages)
                    Spacer(modifier = Modifier.height(12.dp))
                }

                Text(
                    text = "TAP A NAME TO TOGGLE PRESENT / ABSENT",
                    fontSize = 11.sp,
                    fontWeight = FontWeight.Bold,
                    color = Color(0xFF94A3B8),
                    modifier = Modifier.padding(bottom = 8.dp)
                )

                Row(modifier = Modifier.weight(1f).fillMaxWidth()) {
                    RosterColumn(
                        title = "PRESENT",
                        entries = presentList,
                        accentColor = Color(0xFF10B981),
                        modifier = Modifier.weight(1f).fillMaxHeight(),
                        onEntryClick = { entry ->
                            presentList = presentList.filterNot { it === entry }
                            absentList = absentList + entry
                        }
                    )
                    Spacer(modifier = Modifier.width(10.dp))
                    RosterColumn(
                        title = "ABSENT",
                        entries = absentList,
                        accentColor = Color(0xFFF43F5E),
                        modifier = Modifier.weight(1f).fillMaxHeight(),
                        onEntryClick = { entry ->
                            absentList = absentList.filterNot { it === entry }
                            presentList = presentList + entry
                        }
                    )
                }

                Spacer(modifier = Modifier.height(12.dp))

                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(10.dp)
                ) {
                    OutlinedButton(
                        onClick = onBack,
                        enabled = !isConfirming,
                        modifier = Modifier.weight(1f).height(50.dp),
                        shape = RoundedCornerShape(14.dp)
                    ) {
                        Text("Back", color = Color.White)
                    }
                    Button(
                        onClick = {
                            attendanceViewModel.confirmAttendance(
                                sessionId = sessionId,
                                present = presentList,
                                facultyEmail = facultyEmail,
                                facultyName = facultyName
                            )
                        },
                        enabled = !isConfirming,
                        shape = RoundedCornerShape(14.dp),
                        colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF10B981)),
                        modifier = Modifier.weight(2f).height(50.dp)
                    ) {
                        if (isConfirming) {
                            CircularProgressIndicator(color = Color.White, modifier = Modifier.size(20.dp))
                        } else {
                            Text("Confirm Attendance (${presentList.size} Present)", fontWeight = FontWeight.Bold, color = Color.White)
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun StatsBar(totalFaces: Int, recognized: Int, unrecognized: Int, absent: Int) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.spacedBy(8.dp)
    ) {
        StatTile("Faces Detected", totalFaces, Color(0xFF818CF8), Modifier.weight(1f))
        StatTile("Recognized", recognized, Color(0xFF10B981), Modifier.weight(1f))
        StatTile("Unknown", unrecognized, Color(0xFFF59E0B), Modifier.weight(1f))
        StatTile("Marked Absent", absent, Color(0xFFF43F5E), Modifier.weight(1f))
    }
}

@Composable
private fun StatTile(label: String, value: Int, color: Color, modifier: Modifier = Modifier) {
    Card(
        modifier = modifier,
        shape = RoundedCornerShape(12.dp),
        colors = CardDefaults.cardColors(containerColor = Color(0xFF0F172A))
    ) {
        Column(
            modifier = Modifier.padding(vertical = 12.dp, horizontal = 6.dp).fillMaxWidth(),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Text(text = "$value", fontSize = 20.sp, fontWeight = FontWeight.Bold, color = color)
            Text(text = label, fontSize = 10.sp, color = Color(0xFF94A3B8), textAlign = androidx.compose.ui.text.style.TextAlign.Center)
        }
    }
}

@Composable
private fun AnnotatedImageCarousel(images: List<String>) {
    LazyRow(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
        items(images) { dataUri ->
            val bitmap = remember(dataUri) { decodeBase64Image(dataUri) }
            if (bitmap != null) {
                Image(
                    bitmap = bitmap.asImageBitmap(),
                    contentDescription = "Annotated group photo",
                    contentScale = ContentScale.Crop,
                    modifier = Modifier
                        .height(180.dp)
                        .width(260.dp)
                        .clip(RoundedCornerShape(14.dp))
                )
            }
        }
    }
}

@Composable
private fun RosterColumn(
    title: String,
    entries: List<RosterEntry>,
    accentColor: Color,
    modifier: Modifier = Modifier,
    onEntryClick: (RosterEntry) -> Unit
) {
    Column(modifier = modifier) {
        Text(
            text = "$title (${entries.size})",
            fontSize = 12.sp,
            fontWeight = FontWeight.Bold,
            color = accentColor,
            modifier = Modifier.padding(bottom = 6.dp)
        )
        LazyColumn(verticalArrangement = Arrangement.spacedBy(6.dp)) {
            items(entries) { entry ->
                Card(
                    shape = RoundedCornerShape(10.dp),
                    colors = CardDefaults.cardColors(containerColor = Color(0xFF1E293B)),
                    modifier = Modifier
                        .fillMaxWidth()
                        .clickable { onEntryClick(entry) }
                ) {
                    Column(modifier = Modifier.padding(horizontal = 10.dp, vertical = 8.dp)) {
                        Text(
                            text = entry.name ?: entry.grNumber ?: "Unknown",
                            color = Color.White,
                            fontWeight = FontWeight.Bold,
                            fontSize = 12.sp
                        )
                        val subtitle = buildString {
                            entry.grNumber?.let { append("GR: $it") }
                            entry.confidence?.let {
                                if (isNotEmpty()) append(" • ")
                                append("${it.toInt()}%")
                            }
                            if (entry.unregistered) {
                                if (isNotEmpty()) append(" • ")
                                append("New")
                            }
                        }
                        if (subtitle.isNotEmpty()) {
                            Text(text = subtitle, color = Color(0xFF94A3B8), fontSize = 10.sp)
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun ConfirmDonePane(result: com.faceattend.app.data.model.ConfirmAttendanceResult, onContinue: () -> Unit) {
    Column(
        modifier = Modifier.fillMaxSize(),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        Text(
            text = "Attendance Confirmed",
            fontSize = 20.sp,
            fontWeight = FontWeight.Bold,
            color = Color(0xFF34D399)
        )
        Spacer(modifier = Modifier.height(8.dp))
        Text(
            text = "${result.marked.size} student(s) marked present",
            color = Color.White,
            fontSize = 14.sp
        )

        Spacer(modifier = Modifier.height(16.dp))

        Card(
            shape = RoundedCornerShape(14.dp),
            colors = CardDefaults.cardColors(containerColor = Color(0xFF0F172A)),
            modifier = Modifier.fillMaxWidth()
        ) {
            Column(modifier = Modifier.padding(16.dp)) {
                Text("Email Status", color = Color(0xFF94A3B8), fontSize = 12.sp, fontWeight = FontWeight.Bold)
                Spacer(modifier = Modifier.height(6.dp))
                EmailStatusRow("Present list", result.emailStatus.presentSent)
                EmailStatusRow("Absent list", result.emailStatus.absentSent)
                result.emailStatus.message?.let {
                    Spacer(modifier = Modifier.height(6.dp))
                    Text(it, color = Color(0xFF64748B), fontSize = 11.sp)
                }
            }
        }

        if (result.skipped.isNotEmpty()) {
            Spacer(modifier = Modifier.height(12.dp))
            Text("${result.skipped.size} skipped (could not register)", color = Color(0xFFF59E0B), fontSize = 12.sp)
        }

        Spacer(modifier = Modifier.height(24.dp))

        Button(
            onClick = onContinue,
            shape = RoundedCornerShape(14.dp),
            colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF6366F1)),
            modifier = Modifier.fillMaxWidth(0.8f).height(50.dp)
        ) {
            Text("Continue", fontWeight = FontWeight.Bold, color = Color.White)
        }
    }
}

@Composable
private fun EmailStatusRow(label: String, sent: Boolean) {
    Row(
        modifier = Modifier.fillMaxWidth().padding(vertical = 2.dp),
        horizontalArrangement = Arrangement.SpaceBetween
    ) {
        Text(label, color = Color.White, fontSize = 13.sp)
        Text(
            text = if (sent) "Sent" else "Not sent",
            color = if (sent) Color(0xFF34D399) else Color(0xFFFB7185),
            fontWeight = FontWeight.Bold,
            fontSize = 12.sp
        )
    }
}

private fun decodeBase64Image(dataUri: String): Bitmap? {
    return try {
        val base64 = dataUri.substringAfter(",", dataUri)
        val bytes = Base64.decode(base64, Base64.DEFAULT)
        BitmapFactory.decodeByteArray(bytes, 0, bytes.size)
    } catch (e: Exception) {
        null
    }
}
