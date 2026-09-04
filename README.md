# FaceAttend: Automatic Attendance & Biometric Management System

An enterprise-grade, contactless attendance management ecosystem powered by deep learning facial recognition (**InsightFace** + **YOLOv8**). Features a RESTful Python Flask backend, a modern glassmorphic React/TypeScript Web Admin Dashboard, and a native Kotlin Android kiosk/mobile application.

---

## 🌟 System Architecture

FaceAttend consists of three core components:

1. **Python Flask Backend (`/` & `/backend`)**:
   - Biometric Face Identification Engine (ArcFace / InsightFace `buffalo_l` 512-D embeddings + YOLOv8 face detection).
   - REST API handling authentication, real-time MJPEG camera streaming, attendance tracking, Analytics & CSV/Excel export generation.
   - Relational Database ORM supporting SQLite (local dev) and PostgreSQL (production deployment).

2. **Admin Web Dashboard (`/admin-web`)**:
   - Modern React 18 + Vite + TypeScript web portal with high-fidelity glassmorphic UI.
   - Live dashboard metrics, student & faculty roster management, timetable scheduling, real-time session tracking, device management, and audit logs.

3. **Android Mobile Application (`/android-app`)**:
   - Native Android application written in Kotlin.
   - Converts Android devices into mobile biometric attendance terminals with automated device registration & REST API sync.

---

## ✨ Key Features

- **High-Accuracy Face Recognition**: 512-dimensional embedding comparison using L2-normalized Euclidean distance via InsightFace (`buffalo_l`).
- **Multi-Face Crowd Detection**: YOLOv8 face detector (`yolov8n-face.pt`) for high-density group photos and fast multi-face bounding box extraction.
- **Real-Time Video Streaming**: Low-latency MJPEG video streaming powered by asynchronous OpenCV frame capturing.
- **Glassmorphic Admin Portal**: Responsive, sleek web dashboard for system configuration, user provisioning, timetable matching, and automated report generation.
- **Android Kiosk App**: Device-linked Android client allowing faculty/kiosk registration and on-the-go biometric check-ins.
- **Automated Reporting & Analytics**: Export present/absent logs instantly in formatted `.csv` and `.xlsx` formats.

---

## 📁 Repository Structure

```
face_recognition-main/
├── admin-web/               # React + TypeScript + Vite Admin Web Application
│   ├── src/                 # UI Components, Pages, Services, API Client
│   ├── package.json         # Node.js dependencies
│   └── vite.config.ts       # Vite Configuration
├── android-app/             # Native Android Kotlin Application
│   ├── app/src/main/        # Kotlin source code, layouts, and manifests
│   ├── build.gradle.kts     # Android Build Configuration
│   └── local.properties     # Android SDK path (Git-ignored)
├── backend/                 # Flask Backend & API Modules
│   ├── api/                 # Endpoint handlers (Auth, Students, Timetables, Reports)
│   ├── face_engine/         # InsightFace & YOLOv8 facial recognition engine
│   ├── middleware/          # JWT / Auth & Security middleware
│   └── services/            # Analytics, CSV/Excel export, Email notifications
├── app.py                   # Main Flask Backend Server Launcher
├── database.py              # Database initialization & models
├── requirements.txt         # Python dependencies
└── .gitignore               # Excludes secrets, builds, venv, DBs, models, & photos
```

---

## ⚙️ Getting Started

### Prerequisites
- **Python**: 3.9 or higher
- **Node.js**: v18 or higher (for `admin-web`)
- **Android Studio**: Jellyfish / Hedgehog or newer with JDK 17+ (for `android-app`)

---

### 1. Backend Setup (Flask & AI Engine)

1. **Clone Repository & Navigate to Directory**:
   ```bash
   git clone <repository-url>
   cd face_recognition-main
   ```

2. **Create & Activate Virtual Environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Initialize Database & Seed Initial Data**:
   ```bash
   python3 seed_db.py
   ```

5. **Start Flask Server**:
   ```bash
   python3 app.py
   ```
   > **Note**: On the first run, InsightFace (`buffalo_l`) and YOLOv8 (`yolov8n-face.pt`) models will automatically download. The backend runs on `http://localhost:5000`.

---

### 2. Admin Web Dashboard Setup (React + Vite)

1. **Navigate to `admin-web` directory**:
   ```bash
   cd admin-web
   ```

2. **Install Node Dependencies**:
   ```bash
   npm install
   ```

3. **Run Web Development Server**:
   ```bash
   npm run dev
   ```
   The dashboard will be available at `http://localhost:5173`.

---

### 3. Android Mobile Application Setup

1. Open the `android-app` directory in **Android Studio**.
2. Sync Gradle dependencies.
3. Configure `ApiClient.kt` base URL to point to your backend IP address (e.g. `http://10.0.2.2:5000` for Android Emulator or your server's LAN IP).
4. Run on an Android device or emulator (Android 8.0+ / API 26+).

---

## 🔐 Environment & Security Notes

This repository includes a strict `.gitignore` to prevent sensitive or bulky files from being committed to GitHub:
- **Secrets & Keys**: `.env`, `local.properties`, keystores, and credentials are git-ignored.
- **AI Models & Datasets**: Heavy `.pt`, `.pkl`, and `.onnx` files are stored locally.
- **User Photographs & Data**: Student face registration photos (`registered_faces/`) and exported reports (`attendance_reports/`) remain local and private.

---

## 🛠️ Tech Stack Summary

- **Backend**: Python, Flask, OpenCV, InsightFace (ArcFace), YOLOv8 (Ultralytics), SQLite / PostgreSQL
- **Frontend**: React 18, TypeScript, Vite, TailwindCSS, Lucide Icons, Axios
- **Mobile**: Android Native (Kotlin), Jetpack components, Retrofit/OkHttp
- **Deployment**: Gunicorn, Nginx, Docker support
