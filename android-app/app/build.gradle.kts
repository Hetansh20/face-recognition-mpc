plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

val uploadStoreFile = providers.gradleProperty("FACEATTEND_UPLOAD_STORE_FILE").orNull
    ?: error("FACEATTEND_UPLOAD_STORE_FILE is not configured")
val uploadKeyAlias = providers.gradleProperty("FACEATTEND_UPLOAD_KEY_ALIAS").orNull
    ?: error("FACEATTEND_UPLOAD_KEY_ALIAS is not configured")
val uploadStorePassword = providers.gradleProperty("FACEATTEND_UPLOAD_STORE_PASSWORD").orNull
    ?: error("FACEATTEND_UPLOAD_STORE_PASSWORD is not configured")
val uploadKeyPassword = providers.gradleProperty("FACEATTEND_UPLOAD_KEY_PASSWORD").orNull
    ?: error("FACEATTEND_UPLOAD_KEY_PASSWORD is not configured")

android {
    namespace = "com.faceattend.app"
    compileSdk = 36

    defaultConfig {
        applicationId = "com.faceattend.app"
        minSdk = 26
        targetSdk = 36
        versionCode = 1
        versionName = "1.0.0"

        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
        vectorDrawables {
            useSupportLibrary = true
        }

        buildConfigField("String", "PROD_SERVER_URL", "\"https://face-recognition-mpc-production.up.railway.app/api/v1/\"")
    }

    signingConfigs {
        create("release") {
            storeFile = file(uploadStoreFile)
            storePassword = uploadStorePassword
            keyAlias = uploadKeyAlias
            keyPassword = uploadKeyPassword
        }
    }

    buildTypes {
        release {
            isMinifyEnabled = false
            signingConfig = signingConfigs.getByName("release")
            proguardFiles(getDefaultProguardFile("proguard-android-optimize.txt"), "proguard-rules.pro")
        }
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    kotlinOptions {
        jvmTarget = "17"
    }
    buildFeatures {
        compose = true
        buildConfig = true
    }
    composeOptions {
        kotlinCompilerExtensionVersion = "1.5.8"
    }
    packaging {
        resources {
            excludes += "/META-INF/{AL2.0,LGPL2.1}"
        }
    }
}

dependencies {
    // AndroidX Core & Compose
    implementation("androidx.core:core-ktx:1.12.0")
    implementation("androidx.lifecycle:lifecycle-runtime-ktx:2.7.0")
    implementation("androidx.activity:activity-compose:1.8.2")
    implementation(platform("androidx.compose:compose-bom:2024.02.00"))
    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.ui:ui-graphics")
    implementation("androidx.compose.ui:ui-tooling-preview")
    implementation("androidx.compose.material3:material3")
    implementation("androidx.navigation:navigation-compose:2.7.7")

    // CameraX
    val cameraVersion = "1.3.1"
    implementation("androidx.camera:camera-core:$cameraVersion")
    implementation("androidx.camera:camera-camera2:$cameraVersion")
    implementation("androidx.camera:camera-lifecycle:$cameraVersion")
    implementation("androidx.camera:camera-view:$cameraVersion")

    // Networking (Retrofit, OkHttp, Gson)
    implementation("com.squareup.retrofit2:retrofit:2.9.0")
    implementation("com.squareup.retrofit2:converter-gson:2.9.0")
    implementation("com.squareup.okhttp3:okhttp:4.12.0")
    implementation("com.squareup.okhttp3:logging-interceptor:4.12.0")

    // Coroutines
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:1.7.3")
}
