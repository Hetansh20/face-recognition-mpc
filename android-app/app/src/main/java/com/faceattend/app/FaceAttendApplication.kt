package com.faceattend.app

import android.app.Application

class FaceAttendApplication : Application() {
    override fun onCreate() {
        super.onCreate()
        instance = this
    }

    companion object {
        lateinit var instance: FaceAttendApplication
            private set
    }
}
