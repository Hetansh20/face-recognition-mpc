package com.faceattend.app.ui.screens

import android.widget.Toast
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
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
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.faceattend.app.data.model.AttendanceRecordItem
import com.faceattend.app.data.model.RecordStatusUpdate
import com.faceattend.app.ui.viewmodel.AttendanceViewModel
import com.faceattend.app.ui.viewmodel.SessionUiState

@Composable
fun SessionSummaryScreen(
    attendanceViewModel: AttendanceViewModel,
    onDone: () -> Unit
) {
    val context = LocalContext.current
    val sessionState by attendanceViewModel.sessionState.collectAsState()
    val sessionResults by attendanceViewModel.sessionResultsState.collectAsState()
    val isSaving by attendanceViewModel.isSavingRecords.collectAsState()

    val sessionId = remember(sessionState) {
        when (val state = sessionState) {
            is SessionUiState.Completed -> state.summary.sessionId
            is SessionUiState.Active -> state.session.sessionId
            else -> ""
        }
    }

    LaunchedEffect(sessionId) {
        if (sessionId.isNotEmpty()) {
            attendanceViewModel.loadSessionResults(sessionId)
        }
    }

    // Map to keep track of edited student statuses (studentId -> isPresent)
    val editedStatusMap = remember { mutableStateMapOf<String, Boolean>() }

    // Initialize editedStatusMap when sessionResults are loaded
    LaunchedEffect(sessionResults) {
        sessionResults?.records?.forEach { record ->
            if (!editedStatusMap.containsKey(record.studentId)) {
                editedStatusMap[record.studentId] = record.status.equals("PRESENT", ignoreCase = true)
            }
        }
    }

    val presentCount = editedStatusMap.values.count { it }
    val totalStudents = sessionResults?.records?.size ?: editedStatusMap.size
    val absentCount = (totalStudents - presentCount).coerceAtLeast(0)

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(Color(0xFF090D16))
            .padding(16.dp)
    ) {
        // Header Banner
        Card(
            modifier = Modifier
                .fillMaxWidth()
                .padding(bottom = 16.dp),
            shape = RoundedCornerShape(20.dp),
            colors = CardDefaults.cardColors(containerColor = Color(0xFF0F172A))
        ) {
            Column(
                modifier = Modifier.padding(16.dp),
                horizontalAlignment = Alignment.CenterHorizontally
            ) {
                Text(
                    text = "Attendance Summary & Review",
                    fontSize = 18.sp,
                    fontWeight = FontWeight.Bold,
                    color = Color(0xFF34D399)
                )

                Spacer(modifier = Modifier.height(12.dp))

                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceEvenly
                ) {
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        Text(text = "$presentCount", fontSize = 22.sp, fontWeight = FontWeight.Bold, color = Color(0xFF10B981))
                        Text(text = "Present", fontSize = 11.sp, color = Color(0xFF94A3B8))
                    }
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        Text(text = "$absentCount", fontSize = 22.sp, fontWeight = FontWeight.Bold, color = Color(0xFFF43F5E))
                        Text(text = "Absent", fontSize = 11.sp, color = Color(0xFF94A3B8))
                    }
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        Text(text = "$totalStudents", fontSize = 22.sp, fontWeight = FontWeight.Bold, color = Color(0xFF818CF8))
                        Text(text = "Total Enrolled", fontSize = 11.sp, color = Color(0xFF94A3B8))
                    }
                }
            }
        }

        Text(
            text = "EDIT ATTENDANCE (CHECK / UNCHECK)",
            fontSize = 11.sp,
            fontWeight = FontWeight.Bold,
            color = Color(0xFF94A3B8),
            modifier = Modifier.padding(bottom = 8.dp, start = 4.dp)
        )

        // Student Checkbox List
        val records = sessionResults?.records ?: emptyList()
        if (records.isEmpty()) {
            Box(
                modifier = Modifier
                    .weight(1f)
                    .fillMaxWidth(),
                contentAlignment = Alignment.Center
            ) {
                CircularProgressIndicator(color = Color(0xFF6366F1))
            }
        } else {
            LazyColumn(
                modifier = Modifier
                    .weight(1f)
                    .fillMaxWidth(),
                verticalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                items(records, key = { it.studentId }) { record ->
                    val isChecked = editedStatusMap[record.studentId] ?: (record.status == "PRESENT")

                    Card(
                        shape = RoundedCornerShape(12.dp),
                        colors = CardDefaults.cardColors(
                            containerColor = if (isChecked) Color(0xFF064E3B).copy(alpha = 0.4f) else Color(0xFF1E293B)
                        ),
                        modifier = Modifier
                            .fillMaxWidth()
                            .clickable {
                                editedStatusMap[record.studentId] = !isChecked
                            }
                    ) {
                        Row(
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(horizontal = 14.dp, vertical = 10.dp),
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.SpaceBetween
                        ) {
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                Checkbox(
                                    checked = isChecked,
                                    onCheckedChange = { checked ->
                                        editedStatusMap[record.studentId] = checked
                                    },
                                    colors = CheckboxDefaults.colors(
                                        checkedColor = Color(0xFF10B981),
                                        uncheckedColor = Color(0xFF64748B),
                                        checkmarkColor = Color.White
                                    )
                                )

                                Column(modifier = Modifier.padding(start = 8.dp)) {
                                    Text(
                                        text = record.name,
                                        fontWeight = FontWeight.Bold,
                                        color = Color.White,
                                        fontSize = 14.sp
                                    )
                                    Text(
                                        text = "GR: ${record.studentId} • ${record.department ?: "Gen"}",
                                        color = Color(0xFF94A3B8),
                                        fontSize = 11.sp
                                    )
                                }
                            }

                            Surface(
                                color = if (isChecked) Color(0xFF10B981).copy(alpha = 0.2f) else Color(0xFFF43F5E).copy(alpha = 0.2f),
                                shape = RoundedCornerShape(8.dp)
                            ) {
                                Text(
                                    text = if (isChecked) "PRESENT" else "ABSENT",
                                    color = if (isChecked) Color(0xFF34D399) else Color(0xFFFB7185),
                                    fontWeight = FontWeight.Bold,
                                    fontSize = 11.sp,
                                    modifier = Modifier.padding(horizontal = 10.dp, vertical = 4.dp)
                                )
                            }
                        }
                    }
                }
            }
        }

        Spacer(modifier = Modifier.height(12.dp))

        // Action Buttons Row
        Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(10.dp)
            ) {
                // Save Edits Button
                Button(
                    onClick = {
                        val updates = editedStatusMap.map { (stuId, isPresent) ->
                            RecordStatusUpdate(studentId = stuId, status = if (isPresent) "PRESENT" else "ABSENT")
                        }
                        attendanceViewModel.saveAttendanceEdits(sessionId, updates) {
                            Toast.makeText(context, "Attendance updated successfully!", Toast.LENGTH_SHORT).show()
                        }
                    },
                    enabled = !isSaving,
                    shape = RoundedCornerShape(12.dp),
                    colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF10B981)),
                    modifier = Modifier.weight(1f).height(48.dp)
                ) {
                    if (isSaving) {
                        CircularProgressIndicator(color = Color.White, modifier = Modifier.size(18.dp))
                    } else {
                        Text("Save Edits", fontWeight = FontWeight.Bold, fontSize = 14.sp)
                    }
                }

                // Export Present CSV Button
                Button(
                    onClick = {
                        attendanceViewModel.exportAndShareCsv(sessionId, context, absent = false)
                    },
                    shape = RoundedCornerShape(12.dp),
                    colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF6366F1)),
                    modifier = Modifier.weight(1f).height(48.dp)
                ) {
                    Text("Export CSV", fontWeight = FontWeight.Bold, fontSize = 14.sp)
                }
            }

            // Export Absent CSV Button — matches the web app's separate
            // Present/Absent CSV exports emailed after confirming attendance
            OutlinedButton(
                onClick = {
                    attendanceViewModel.exportAndShareCsv(sessionId, context, absent = true)
                },
                shape = RoundedCornerShape(12.dp),
                modifier = Modifier.fillMaxWidth().height(44.dp)
            ) {
                Text("Export Absent List CSV", color = Color.White, fontSize = 13.sp)
            }

            // Return to Dashboard Button
            Button(
                onClick = onDone,
                shape = RoundedCornerShape(12.dp),
                colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF334155)),
                modifier = Modifier.fillMaxWidth().height(44.dp)
            ) {
                Text("Return to Dashboard", color = Color.White, fontSize = 13.sp)
            }
        }
    }
}
