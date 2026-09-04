import os
import cv2
import json
import numpy as np
import base64
from backend.config import Config
from backend.face_engine.embedding_service import embedding_service, l2_normalize

def process_group_photo(image_bytes: bytes, target_pids: set = None, threshold: float = 0.75) -> dict:
    """
    Runs InsightFace on full group photo in ONE PASS.
    Optionally runs YOLOv8 sweep for background faces.
    """
    from backend.face_engine.face_engine import face_service
    face_service.initialize()

    np_arr = np.frombuffer(image_bytes, np.uint8)
    frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    if frame is None:
        return {"error": "Could not decode image."}

    h, w = frame.shape[:2]
    if max(h, w) > 1920:
        scale = 1920 / max(h, w)
        frame = cv2.resize(frame, (int(w * scale), int(h * scale)))

    annotated = frame.copy()
    yolo_used = False

    detected = face_service.detect_faces(frame)
    matched_centers = set()
    recognized = []

    for face in detected:
        box = face.bbox.astype(int)
        bbox = [int(box[0]), int(box[1]), int(box[2]), int(box[3])]
        cx = (bbox[0] + bbox[2]) // 2
        cy = (bbox[1] + bbox[3]) // 2
        matched_centers.add((cx // 20, cy // 20))

        live_vec = face.embedding.astype(np.float32)
        pid, dist, info = embedding_service.find_best_match(live_vec, target_pids=target_pids, threshold=threshold)

        if pid and info:
            confidence = round((1.0 - dist) * 100, 1)
            recognized.append({
                "person_id": pid,
                "student_id": info.get("gr_number", pid),
                "name": info.get("name", pid),
                "confidence": confidence,
                "bbox": bbox
            })
            _draw_box(annotated, bbox, info.get("name", pid), confidence)
        else:
            _draw_box(annotated, bbox, None, None)

    unrecognized = len(detected) - len(recognized)

    # Optional YOLO sweep for background faces
    if os.path.exists(Config.YOLO_MODEL_PATH) and len(detected) > 0:
        try:
            from ultralytics import YOLO
            yolo = YOLO(Config.YOLO_MODEL_PATH)
            results = yolo(frame, verbose=False, conf=0.4)[0]
            extra = 0
            for box in results.boxes.xyxy.cpu().numpy():
                x1, y1, x2, y2 = map(int, box[:4])
                cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
                cell = (cx // 20, cy // 20)
                if cell in matched_centers:
                    continue

                pad = 40
                crop = frame[max(0, y1 - pad):min(h, y2 + pad), max(0, x1 - pad):min(w, x2 + pad)]
                faces_in_crop = face_service.detect_faces(crop)
                if faces_in_crop:
                    best_crop = max(faces_in_crop, key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]))
                    lv = best_crop.embedding.astype(np.float32)
                    pid2, dist2, info2 = embedding_service.find_best_match(lv, target_pids=target_pids, threshold=threshold)
                    bbox2 = [x1, y1, x2, y2]
                    matched_centers.add(cell)
                    if pid2 and info2:
                        confidence = round((1.0 - dist2) * 100, 1)
                        recognized.append({
                            "person_id": pid2,
                            "student_id": info2.get("gr_number", pid2),
                            "name": info2.get("name", pid2),
                            "confidence": confidence,
                            "bbox": bbox2
                        })
                        _draw_box(annotated, bbox2, info2.get("name", pid2), confidence)
                        extra += 1
                    else:
                        unrecognized += 1
                        _draw_box(annotated, bbox2, None, None)
            yolo_used = extra > 0
        except Exception as e:
            print(f"[GroupRecog] YOLO sweep skipped: {e}")

    _, buf = cv2.imencode(".jpg", annotated, [cv2.IMWRITE_JPEG_QUALITY, 88])
    annotated_b64 = "data:image/jpeg;base64," + base64.b64encode(buf).decode()

    return {
        "recognized": recognized,
        "unrecognized_count": max(0, unrecognized),
        "total_faces": len(detected),
        "annotated_image": annotated_b64,
        "yolo_used": yolo_used
    }

def _draw_box(frame, bbox, name, confidence):
    x1, y1, x2, y2 = bbox
    color = (46, 160, 67) if name else (218, 54, 51)
    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
    label = f"{name} {confidence}%" if name else "Unknown"
    (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 1)
    cv2.rectangle(frame, (x1, y1 - th - 10), (x1 + tw + 8, y1), color, -1)
    cv2.putText(frame, label, (x1 + 4, y1 - 4), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)
