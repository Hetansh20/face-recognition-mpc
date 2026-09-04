import os
import cv2
import numpy as np
from insightface.app import FaceAnalysis
from backend.config import Config
from backend.face_engine.embedding_service import embedding_service, l2_normalize

class FaceRecognitionService:
    """Core Face Recognition Engine using InsightFace and OpenCV."""

    def __init__(self):
        self.app = None
        self.is_initialized = False

    def initialize(self):
        """Lazy loads the InsightFace model once at startup."""
        if self.is_initialized and self.app is not None:
            return

        try:
            print("[FaceEngine] Loading InsightFace (buffalo_sc CPU model)...")
            self.app = FaceAnalysis(name="buffalo_sc")
            self.app.prepare(ctx_id=-1, det_thresh=0.45, det_size=(320, 320))
            self.is_initialized = True
            print("[FaceEngine] InsightFace engine ready.")
        except Exception as e:
            print(f"[FaceEngine] Failed to initialize InsightFace: {e}")

    def detect_faces(self, frame: np.ndarray):
        """Detect faces in an OpenCV frame."""
        self.initialize()
        if self.app is None:
            return []
        try:
            return self.app.get(frame)
        except Exception as e:
            print(f"[FaceEngine] detect_faces error: {e}")
            return []

    def process_frame(self, image_bytes: bytes, target_pids: set = None, threshold: float = 0.55):
        """
        Accepts frame bytes (JPEG/PNG) from Android app or web client,
        detects faces, extracts 512-d embeddings, matches against database,
        and returns structured recognition results.
        """
        self.initialize()
        np_arr = np.frombuffer(image_bytes, np.uint8)
        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        if frame is None:
            return {"error": "Invalid image payload", "faces_detected": 0, "recognized": 0, "students": []}

        h, w = frame.shape[:2]
        # Optimize frame width for fast CPU inference if > 640px
        scale = 1.0
        infer_frame = frame
        if w > 640:
            scale = 640.0 / float(w)
            infer_h = max(1, int(h * scale))
            infer_frame = cv2.resize(frame, (640, infer_h), interpolation=cv2.INTER_LINEAR)

        faces = self.detect_faces(infer_frame)
        if not faces:
            return {
                "faces_detected": 0,
                "recognized": 0,
                "unknown": 0,
                "students": []
            }

        students_matched = []
        recognized_count = 0
        unknown_count = 0

        for face in faces:
            box = face.bbox.astype(np.float32)
            if scale != 1.0:
                box[0] /= scale
                box[2] /= scale
                box[1] /= scale
                box[3] /= scale
            bbox = [int(box[0]), int(box[1]), int(box[2]), int(box[3])]

            live_vec = face.embedding.astype(np.float32)
            best_pid, best_dist, info = embedding_service.find_best_match(
                live_vec, target_pids=target_pids, threshold=threshold
            )

            confidence = round(max(0.0, (1.0 - best_dist) * 100), 1)

            if best_pid and info:
                recognized_count += 1
                students_matched.append({
                    "person_id": best_pid,
                    "student_id": info.get("gr_number", best_pid),
                    "name": info.get("name", best_pid),
                    "confidence": confidence / 100.0,
                    "confidence_pct": confidence,
                    "status": "PRESENT",
                    "bbox": bbox
                })
            else:
                unknown_count += 1
                students_matched.append({
                    "person_id": "UNKNOWN",
                    "student_id": "UNKNOWN",
                    "name": "Unknown Person",
                    "confidence": confidence / 100.0,
                    "confidence_pct": confidence,
                    "status": "UNKNOWN",
                    "bbox": bbox
                })

        return {
            "faces_detected": len(faces),
            "recognized": recognized_count,
            "unknown": unknown_count,
            "students": students_matched
        }

face_service = FaceRecognitionService()
