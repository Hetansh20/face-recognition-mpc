package com.faceattend.app

import android.Manifest
import android.content.pm.PackageManager
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.activity.viewModels
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.core.content.ContextCompat
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import com.faceattend.app.ui.screens.*
import com.faceattend.app.ui.viewmodel.AttendanceViewModel
import com.faceattend.app.ui.viewmodel.AuthViewModel

class MainActivity : ComponentActivity() {

    private val authViewModel: AuthViewModel by viewModels()
    private val attendanceViewModel: AttendanceViewModel by viewModels()

    private val requestCameraPermissionLauncher =
        registerForActivityResult(ActivityResultContracts.RequestPermission()) { isGranted ->
            if (!isGranted) {
                // Permission handled inside camera view gracefully
            }
        }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        if (ContextCompat.checkSelfPermission(this, Manifest.permission.CAMERA) != PackageManager.PERMISSION_GRANTED) {
            requestCameraPermissionLauncher.launch(Manifest.permission.CAMERA)
        }

        setContent {
            MaterialTheme {
                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = Color(0xFF090D16)
                ) {
                    val navController = rememberNavController()

                    NavHost(
                        navController = navController,
                        startDestination = if (authViewModel.getFacultyId() > 0) "dashboard" else "login"
                    ) {
                        composable("login") {
                            LoginScreen(
                                authViewModel = authViewModel,
                                onLoginSuccess = {
                                    navController.navigate("dashboard") {
                                        popUpTo("login") { inclusive = true }
                                    }
                                }
                            )
                        }

                        composable("dashboard") {
                            FacultyDashboardScreen(
                                authViewModel = authViewModel,
                                attendanceViewModel = attendanceViewModel,
                                onStartCameraSession = { sessionId, className, subjectName ->
                                    navController.navigate("camera/$sessionId/$className/$subjectName")
                                },
                                onLogout = {
                                    navController.navigate("login") {
                                        popUpTo("dashboard") { inclusive = true }
                                    }
                                }
                            )
                        }

                        composable("camera/{sessionId}/{className}/{subjectName}") { backStackEntry ->
                            val sessionId = backStackEntry.arguments?.getString("sessionId") ?: ""
                            val className = backStackEntry.arguments?.getString("className") ?: ""
                            val subjectName = backStackEntry.arguments?.getString("subjectName") ?: ""

                            CameraAttendanceScreen(
                                sessionId = sessionId,
                                className = className,
                                subjectName = subjectName,
                                attendanceViewModel = attendanceViewModel,
                                onReviewPhotos = {
                                    navController.navigate("review/$sessionId/$className")
                                },
                                onFinishSession = {
                                    navController.navigate("summary") {
                                        popUpTo("dashboard") { inclusive = false }
                                    }
                                }
                            )
                        }

                        composable("review/{sessionId}/{className}") { backStackEntry ->
                            val sessionId = backStackEntry.arguments?.getString("sessionId") ?: ""
                            val className = backStackEntry.arguments?.getString("className") ?: ""

                            GroupReviewScreen(
                                sessionId = sessionId,
                                className = className,
                                facultyEmail = authViewModel.getUserEmail(),
                                facultyName = authViewModel.getUserName(),
                                attendanceViewModel = attendanceViewModel,
                                onConfirmed = {
                                    attendanceViewModel.clearReview()
                                    navController.popBackStack("camera/{sessionId}/{className}/{subjectName}", inclusive = false)
                                },
                                onBack = {
                                    attendanceViewModel.clearReview()
                                    navController.popBackStack()
                                }
                            )
                        }

                        composable("summary") {
                            SessionSummaryScreen(
                                attendanceViewModel = attendanceViewModel,
                                onDone = {
                                    navController.navigate("dashboard") {
                                        popUpTo("dashboard") { inclusive = true }
                                    }
                                }
                            )
                        }
                    }
                }
            }
        }
    }
}
