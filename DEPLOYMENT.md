# Deploying FaceAttend to Production

This covers hosting the **backend API** and the **admin web portal** live, plus what your friend needs to change before publishing the **Android app** to the Play Store. All three talk to each other over plain HTTPS — there's no coupling beyond URLs and environment variables.

---

## 0. Before you start — decide your domains

You'll end up with two public URLs. Pick them (or just use the free subdomains the platforms below give you) before configuring anything, since both the admin portal and the Android app need to know the backend's URL:

- Backend API → e.g. `https://faceattend-api.up.railway.app`
- Admin portal → e.g. `https://faceattend-admin.vercel.app`

---

## 1. Backend API (Flask + InsightFace)

**Recommended platform: [Railway](https://railway.app)** — it's what the project's own docs were already written against, supports long-running Python processes (needed for the ML model), and offers a managed Postgres database and persistent volumes, both of which you need.

### 1.1 Why this needs care (read this first)

Two things on a typical "just deploy the container" platform get **wiped on every redeploy** unless you explicitly persist them:

1. **The database** — if you leave `DATABASE_URL` as the SQLite default, every redeploy resets all students, faculty, sessions, and attendance history to empty.
2. **Registered face photos + the trained embedding cache** (`registered_faces/`, `face_database.json`, `face_embeddings_insightface.pkl`) — without persistence, every redeploy means re-uploading every student's photo and retraining from scratch.

The backend now supports both being pointed at persistent storage (see below) — this was fixed as part of this deployment prep.

### 1.2 Steps (Railway)

1. **Create a new Railway project** from this GitHub repo (`face-recognition-mpc`).
2. **Set the Dockerfile path** to `Dockerfile.backend` (Railway → Settings → Build → Dockerfile Path). This is a separate file from the repo's root `Dockerfile`, which builds the old legacy app — don't use that one.
3. **Add a Postgres database** (Railway → New → Database → PostgreSQL). Railway auto-injects a `DATABASE_URL` variable into your service — but it will be a `postgres://` URL; SQLAlchemy needs `postgresql://` or `postgresql+psycopg2://`. If Railway gives you `postgres://...`, change the prefix to `postgresql://...` in the variable, or add a small override.
4. **Add a Volume** (Railway → your service → Volumes → New Volume), mount it at `/app/data`. Then set the environment variable:
   ```
   DATA_DIR=/app/data
   ```
   This is what makes registered face photos and the trained embedding cache survive redeploys.
5. **Set the rest of the environment variables** (Railway → Variables):

   | Variable | Value | Notes |
   |---|---|---|
   | `DATABASE_URL` | `postgresql://...` (from step 3) | Falls back to SQLite under `DATA_DIR` if omitted — fine for a quick test, not for real use |
   | `DATA_DIR` | `/app/data` | Must match the volume mount path from step 4 |
   | `SECRET_KEY` | a long random string | **Change from the dev default** |
   | `JWT_SECRET_KEY` | a different long random string | **Change from the dev default** |
   | `JWT_REFRESH_SECRET_KEY` | another different long random string | **Change from the dev default** |
   | `CORS_ORIGINS` | `https://faceattend-admin.vercel.app` | Your actual admin portal URL from Step 0 — don't leave this as `*` in production |
   | `SENDER_EMAIL` | `anshraythatha123@gmail.com` | For the SMTP fallback path |
   | `SENDER_PASSWORD` | (the Gmail app password) | For the SMTP fallback path |
   | `BREVO_API_KEY` | your `xkeysib-...` key | Once whitelisted in Brevo's IP allowlist for Railway's egress IP(s) |
   | `PORT` | *(leave unset)* | Railway sets this automatically; the Dockerfile already reads it |

   Generate random secrets locally with:
   ```bash
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

6. **Deploy.** Railway will build `Dockerfile.backend` and boot Gunicorn on the assigned port. First boot will be slow (~1–2 min) while InsightFace downloads its model weights into the container — this only happens once per container instance since the volume doesn't cover the model cache (that's fine, it's a few hundred MB, cached in the image layer after first pull if you don't clear it).

7. **Verify**: hit `https://<your-backend>.up.railway.app/api/v1/health` — you should get a JSON success response.

8. **Brevo IP allowlist**: Railway's outbound IP isn't fixed on the free tier, which complicates whitelisting for Brevo's IP-restriction feature. Simplest fix: in Brevo, go to **Settings → Security → Authorised IPs** and either turn the restriction off, or (better, if available on your plan) add a static outbound IP add-on. Otherwise the app will silently fall back to Gmail SMTP, which still works correctly.

### 1.3 First-time data setup on the live backend

Once deployed, the database starts empty. You have two options:
- **Re-run the same migration approach** used locally (pointing at the live Postgres `DATABASE_URL` instead of the local SQLite file) to bring over the real student roster from the web version, or
- **Use the admin portal itself** once it's live to add faculty/students/timetables, and use its face-registration flow to enroll students directly.

---

## 2. Admin Web Portal (React/Vite)

**Recommended platform: [Vercel](https://vercel.com)** or [Netlify](https://netlify.com) — both build and host a Vite static site for free with zero server management.

### 2.1 Steps (Vercel)

1. **Import the repo** into Vercel, set the **Root Directory** to `admin-web/` (Vercel → Project Settings → General → Root Directory).
2. **Build command**: `npm run build` (Vercel usually auto-detects this for Vite).
3. **Output directory**: `dist`.
4. **Set one environment variable** (Vercel → Settings → Environment Variables):
   ```
   VITE_API_BASE_URL=https://<your-backend>.up.railway.app/api/v1
   ```
   This is required — without it, the admin portal defaults to a relative `/api/v1` path, which only works when the frontend and backend share a domain (they won't, here).
5. **Deploy.** Vercel gives you a `https://<project>.vercel.app` URL.
6. **Go back and update `CORS_ORIGINS`** on the backend (Section 1.2, step 5) to this exact URL, then redeploy the backend so it actually accepts requests from the deployed admin portal.

### 2.2 Verify

Open the deployed admin portal URL, log in (`admin123@gmail.com` / `admin123` — **change this**, see Section 4), and confirm the dashboard loads live stats from the Railway backend.

---

## 3. Android App — what your friend needs to change before publishing

The app currently has an in-app "Server Address Settings" field so it can be pointed at any backend during development. That field is now **automatically hidden in release builds** — release builds always use one fixed, baked-in production URL, and there's no way for an end user to redirect the app elsewhere. Two things must happen before your friend builds the release:

1. **Update the production URL** in `android-app/app/build.gradle.kts`:
   ```kotlin
   buildConfigField("String", "PROD_SERVER_URL", "\"https://your-backend-domain.example.com/api/v1/\"")
   ```
   Replace the placeholder with your actual deployed backend URL from Section 1 (must end in `/api/v1/`, including the trailing slash).

2. **Build a release bundle**, not a debug APK — this is what actually applies the change above and what the Play Store requires:
   ```bash
   cd android-app
   ./gradlew bundleRelease
   ```
   This produces `app/build/outputs/bundle/release/app-release.aab`, an Android App Bundle, which is what gets uploaded to the Play Console (not a raw `.apk`).

3. **Your friend needs a signing key** for the release build — if the app isn't signed yet, Play Console requires either:
   - A `signingConfig` wired into `build.gradle.kts` pointing at a keystore file, or
   - Letting Google Play generate and manage the signing key ("Play App Signing"), which is the simpler modern default — your friend can upload an unsigned or debug-signed bundle initially and let Play Console handle final signing, depending on their Play Console setup.

   This part is entirely on your friend's side since it's tied to their Play Console developer account.

4. Do **not** commit the real production URL if it contains anything sensitive — a plain HTTPS hostname is fine to have in source control, there's no secret in it.

### 3.1 Why the in-app server picker had to be hidden

It existed purely so this app could be pointed at a laptop's LAN IP / USB-tunneled localhost during development and testing. Shipping that control to real users would let anyone redirect the app to a different (potentially malicious) backend and have it silently send login credentials and photos there. It's now compiled out of release builds entirely — not hidden by a flag that could be toggled, but a different code path that reads a fixed `BuildConfig` value with the settings UI omitted.

---

## 4. Security checklist before going live

- [ ] Change `SECRET_KEY`, `JWT_SECRET_KEY`, `JWT_REFRESH_SECRET_KEY` from their dev defaults (Section 1.2).
- [ ] Set `CORS_ORIGINS` to the real admin portal domain, not `*`.
- [ ] Change the hardcoded admin login (`admin123@gmail.com` / `admin123`) — this is currently a fallback baked into `backend/services/auth_service.py`; either change the constants there before deploying, or immediately create a real admin user through the same login system and disable the fallback.
- [ ] Confirm `.env` is never committed (`.gitignore` already excludes it — verify with `git status` before your first push after this setup).
- [ ] Rotate the Brevo API key and Gmail app password if either was ever pasted into a chat, ticket, or shared document outside this project.
- [ ] Decide on the Brevo IP-allowlist question (Section 1.2, step 8) rather than leaving it silently falling back to SMTP indefinitely.

---

## 5. Ongoing operations

- **Redeploying the backend**: pushing to the connected branch triggers a Railway rebuild automatically. Data survives because of the volume + Postgres setup in Section 1.
- **Redeploying the admin portal**: same — push to the connected branch, Vercel rebuilds.
- **Updating the Android app**: any change requires your friend to build a new signed release bundle and upload it as a new version in Play Console; there's no over-the-air update path for native app code (only backend/API changes take effect immediately for existing installs).
