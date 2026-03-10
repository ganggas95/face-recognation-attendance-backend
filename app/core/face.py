import os
from functools import lru_cache

from app.core.exceptions import AppException


@lru_cache(maxsize=1)
def get_face_analyzer():
    try:
        from insightface.app import FaceAnalysis
    except Exception as exc:
        raise AppException(
            status_code=500,
            message="insightface is not available",
            meta={"error": str(exc)},
        ) from exc

    model_name = os.getenv("INSIGHTFACE_MODEL_NAME", "buffalo_l")
    ctx_id = int(os.getenv("INSIGHTFACE_CTX_ID", "-1"))
    det_size = int(os.getenv("INSIGHTFACE_DET_SIZE", "640"))
    app = FaceAnalysis(name=model_name)
    app.prepare(ctx_id=ctx_id, det_size=(det_size, det_size))
    return app


def _decode_image(image_bytes: bytes):
    try:
        import cv2  # type: ignore
        import numpy as np  # type: ignore
    except Exception as exc:
        raise AppException(
            status_code=500,
            message="opencv/numpy is not available",
            meta={"error": str(exc)},
        ) from exc

    buffer = np.frombuffer(image_bytes, dtype=np.uint8)
    img = cv2.imdecode(buffer, cv2.IMREAD_COLOR)
    if img is None:
        raise AppException(
            status_code=422,
            message="invalid image",
            meta={},
        )
    return img


def extract_single_face_embedding(
    image_bytes: bytes,
    *,
    min_bbox_size: int | None = None,
    min_det_score: float | None = None,
) -> list[float]:
    try:
        import numpy as np  # type: ignore
    except Exception as exc:
        raise AppException(
            status_code=500,
            message="numpy is not available",
            meta={"error": str(exc)},
        ) from exc

    min_bbox_size = min_bbox_size or int(os.getenv("FACE_MIN_BBOX", "80"))
    min_det_score = min_det_score or float(
        os.getenv("FACE_MIN_DET_SCORE", "0.5")
    )

    img = _decode_image(image_bytes)
    analyzer = get_face_analyzer()
    faces = analyzer.get(img)
    if len(faces) != 1:
        raise AppException(
            status_code=422,
            message=f"exactly one face is required (detected={len(faces)})",
            meta={"faces_detected": len(faces)},
        )

    face = faces[0]
    bbox = getattr(face, "bbox", None)
    if bbox is None or len(bbox) != 4:
        raise AppException(
            status_code=500,
            message="face bbox not available",
            meta={},
        )

    x1, y1, x2, y2 = [float(v) for v in bbox]
    w = max(0.0, x2 - x1)
    h = max(0.0, y2 - y1)
    if min(w, h) < float(min_bbox_size):
        raise AppException(
            status_code=422,
            message="face too small",
            meta={"bbox_w": w, "bbox_h": h, "min_bbox": min_bbox_size},
        )

    det_score = float(getattr(face, "det_score", 0.0) or 0.0)
    if det_score < min_det_score:
        raise AppException(
            status_code=422,
            message="face detection confidence too low",
            meta={"det_score": det_score, "min_det_score": min_det_score},
        )

    embedding = getattr(face, "embedding", None)
    if embedding is None:
        raise AppException(
            status_code=500,
            message="face embedding not available",
            meta={},
        )

    arr = np.asarray(embedding, dtype=np.float32).reshape(-1)
    if arr.size != 512:
        raise AppException(
            status_code=500,
            message="invalid embedding size",
            meta={"embedding_size": int(arr.size)},
        )
    return arr.astype(float).tolist()
