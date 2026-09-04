import os
import json
import pickle
import numpy as np
from backend.config import Config

def l2_normalize(x: np.ndarray) -> np.ndarray:
    return x / (np.linalg.norm(x) + 1e-10)

class EmbeddingService:
    """Service for managing, caching, and matching facial embeddings."""

    def __init__(self):
        self.embeddings = {}
        self.face_db = {}
        self.load_cache()

    def load_cache(self):
        """Loads cached embeddings from PKL and metadata from JSON."""
        if os.path.exists(Config.EMB_CACHE_PKL):
            try:
                with open(Config.EMB_CACHE_PKL, "rb") as f:
                    self.embeddings = pickle.load(f)
            except Exception as e:
                print(f"[EmbeddingService] Failed to load PKL cache: {e}")

        if os.path.exists(Config.FACE_DB_JSON):
            try:
                with open(Config.FACE_DB_JSON, "r") as f:
                    self.face_db = json.load(f)
            except Exception as e:
                print(f"[EmbeddingService] Failed to load JSON DB: {e}")

    def save_cache(self):
        """Persists current in-memory embeddings and metadata."""
        os.makedirs(os.path.dirname(Config.EMB_CACHE_PKL), exist_ok=True)
        with open(Config.EMB_CACHE_PKL, "wb") as f:
            pickle.dump(self.embeddings, f)

        with open(Config.FACE_DB_JSON, "w") as f:
            json.dump(self.face_db, f, indent=4)

    def register_embedding(self, person_id: str, name: str, gr_number: str, vectors: list, image_paths: list = None):
        """Registers face vectors for a student."""
        normalized_vectors = [l2_normalize(np.array(v, dtype=np.float32)) for v in vectors]
        
        self.embeddings[person_id] = {
            "all": normalized_vectors,
            "mean": l2_normalize(np.mean(normalized_vectors, axis=0))
        }

        self.face_db[person_id] = {
            "name": name,
            "gr_number": gr_number,
            "image_paths": image_paths or [],
            "registered": str(np.datetime64('now'))
        }
        self.save_cache()

    def find_best_match(self, live_vec: np.ndarray, target_pids: set = None, threshold: float = 0.55):
        """Find best cosine match for a live face vector."""
        if not self.embeddings:
            return None, 1.0, None

        live_norm = l2_normalize(live_vec.astype(np.float32))
        dists = []

        for pid, data in self.embeddings.items():
            if target_pids and pid not in target_pids:
                continue

            if isinstance(data, dict) and "all" in data:
                min_d = min(1.0 - float(np.dot(live_norm, sv)) for sv in data["all"])
                dists.append((pid, min_d))
            elif isinstance(data, dict) and "mean" in data:
                d = 1.0 - float(np.dot(live_norm, data["mean"]))
                dists.append((pid, d))

        if not dists:
            return None, 1.0, None

        dists.sort(key=lambda x: x[1])
        best_pid, best_dist = dists[0]
        second_dist = dists[1][1] if len(dists) > 1 else 1.0

        if best_dist < threshold:
            info = self.face_db.get(best_pid, {})
            return best_pid, best_dist, info
        return None, best_dist, None

embedding_service = EmbeddingService()
