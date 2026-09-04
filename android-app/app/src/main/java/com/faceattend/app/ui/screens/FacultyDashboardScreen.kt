package com.faceattend.app.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.faceattend.app.data.model.ActiveClassInfo
import com.faceattend.app.ui.viewmodel.*

@Composable
fun FacultyDashboardScreen(
    authViewModel: AuthViewModel,
    attendanceViewModel: AttendanceViewModel,
    onStartCameraSession: (sessionId: String, className: String, subjectName: String) -> Unit,
    onLogout: () -> Unit
) {
    val facultyId = authViewModel.getFacultyId()
    val activeClassState by attendanceViewModel.activeClassState.collectAsState()
    val sessionState by attendanceViewModel.sessionState.collectAsState()

    LaunchedEffect(facultyId) {
        attendanceViewModel.loadActiveClass(facultyId)
    }

    LaunchedEffect(sessionState) {
        if (sessionState is SessionUiState.Active) {
            val active = (sessionState as SessionUiState.Active).session
            onStartCameraSession(active.sessionId, active.className, active.subjectName)
        }
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(Color(0xFF090D16))
            .padding(20.dp)
    ) {
        // Header
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(bottom = 20.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Column {
                Text(
                    text = "Welcome, ${authViewModel.getUserName()}",
                    fontSize = 20.sp,
                    fontWeight = FontWeight.Bold,
                    color = Color.White
                )
                Text(
                    text = "Faculty ID: FAC-$facultyId",
                    fontSize = 12.sp,
                    color = Color(0xFF818CF8)
                )
            }

            TextButton(onClick = {
                authViewModel.logout()
                onLogout()
            }) {
                Text("Logout", color = Color(0xFFFB7185))
            }
        }

        Spacer(modifier = Modifier.height(10.dp))

        // Active Scheduled Class Card
        Text(
            text = "CURRENT SCHEDULED SESSION",
            fontSize = 12.sp,
            fontWeight = FontWeight.Bold,
            color = Color(0xFF94A3B8),
            modifier = Modifier.padding(bottom = 8.dp)
        )

        when (val state = activeClassState) {
            is ActiveClassUiState.Loading -> {
                Box(modifier = Modifier.fillMaxWidth().height(150.dp), contentAlignment = Alignment.Center) {
                    CircularProgressIndicator(color = Color(0xFF6366F1))
                }
            }

            is ActiveClassUiState.Success -> {
                ActiveClassCard(
                    classInfo = state.classInfo,
                    isStarting = sessionState is SessionUiState.Starting,
                    onStartSession = {
                        attendanceViewModel.startAttendanceSession(facultyId, state.classInfo.timetableId)
                    }
                )
            }

            is ActiveClassUiState.NoClass -> {
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(16.dp),
                    colors = CardDefaults.cardColors(containerColor = Color(0xFF0F172A))
                ) {
                    Column(modifier = Modifier.padding(20.dp)) {
                        Text(
                            text = "No Class Currently Active",
                            fontSize = 16.sp,
                            fontWeight = FontWeight.Bold,
                            color = Color(0xFFCBD5E1)
                        )
                        Spacer(modifier = Modifier.height(6.dp))
                        Text(
                            text = state.message,
                            fontSize = 13.sp,
                            color = Color(0xFF64748B)
                        )
                    }
                }
            }

            is ActiveClassUiState.Error -> {
                Text(text = state.message, color = Color.Red)
            }
        }
    }
}

@Composable
fun ActiveClassCard(
    classInfo: ActiveClassInfo,
    isStarting: Boolean,
    onStartSession: () -> Unit
) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(20.dp),
        colors = CardDefaults.cardColors(containerColor = Color(0xFF1E1B4B))
    ) {
        Column(modifier = Modifier.padding(20.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                Text(
                    text = classInfo.subjectName,
                    fontSize = 18.sp,
                    fontWeight = FontWeight.Bold,
                    color = Color.White
                )
                Surface(
                    color = Color(0xFF10B981).copy(alpha = 0.2f),
                    shape = RoundedCornerShape(10.dp)
                ) {
                    Text(
                        text = "LIVE SLOT",
                        color = Color(0xFF34D399),
                        fontSize = 10.sp,
                        fontWeight = FontWeight.Bold,
                        modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp)
                    )
                }
            }

            Spacer(modifier = Modifier.height(8.dp))

            val semText = if (!classInfo.semester.isNullOrEmpty() && classInfo.semester != "N/A") " • ${classInfo.semester}" else ""
            Text(
                text = "${classInfo.className}${semText} • ${classInfo.roomNumber ?: "Main Hall"}",
                fontSize = 14.sp,
                color = Color(0xFFA5B4FC)
            )

            Text(
                text = "${classInfo.startTime} - ${classInfo.endTime} • ${classInfo.totalStudents} Enrolled Students",
                fontSize = 12.sp,
                color = Color(0xFF64748B),
                modifier = Modifier.padding(top = 4.dp)
            )

            Spacer(modifier = Modifier.height(20.dp))

            Button(
                onClick = onStartSession,
                enabled = !isStarting,
                shape = RoundedCornerShape(12.dp),
                colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF10B981)),
                modifier = Modifier
                    .fillMaxWidth()
                    .height(48.dp)
            ) {
                if (isStarting) {
                    CircularProgressIndicator(color = Color.White, modifier = Modifier.size(20.dp))
                } else {
                    Text(
                        text = "Start AI Camera Recognition",
                        fontWeight = FontWeight.Bold,
                        fontSize = 15.sp,
                        color = Color.White
                    )
                }
            }
        }
    }
}
