"""Worker de IA: lee una cámara (RTSP o archivo), detecta objetos y avisa a Nx.

Cuando detecta algo, llama al backend (/api/events/generic), que crea un
Generic Event en Nx. En Nx puedes crear una regla que reaccione a ese evento
(grabar, notificar, marcar en la línea de tiempo…).
"""

from __future__ import annotations

import logging
import os
import time
from collections import Counter

import cv2
import httpx

from detector import Detection, MotionDetector, YoloDetector

log = logging.getLogger("ai-worker")


class AlertThrottle:
    """Evita inundar Nx de eventos: como mucho uno por etiqueta cada `cooldown_s`."""

    def __init__(self, cooldown_s: float):
        self.cooldown_s = cooldown_s
        self._last: dict[str, float] = {}

    def should_alert(self, label: str, now: float) -> bool:
        if now - self._last.get(label, float("-inf")) < self.cooldown_s:
            return False
        self._last[label] = now
        return True


def summarize(detections: list[Detection], watch: set[str], min_count: int) -> dict[str, int]:
    counts = Counter(d.label for d in detections if not watch or d.label in watch)
    return {label: n for label, n in counts.items() if n >= min_count}


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    source = os.environ.get("VIDEO_SOURCE", "rtsp://localhost:8554/cam1")
    backend = os.environ.get("BACKEND_URL", "http://localhost:8000").rstrip("/")
    camera_id = os.environ.get("NX_CAMERA_ID", "")
    model_path = os.environ.get("MODEL_PATH", "")
    fps = float(os.environ.get("ANALYSIS_FPS", "2"))
    watch = {s.strip() for s in os.environ.get("WATCH_LABELS", "persona,coche").split(",") if s.strip()}
    min_count = int(os.environ.get("MIN_COUNT", "1"))
    throttle = AlertThrottle(float(os.environ.get("ALERT_COOLDOWN_S", "30")))

    if model_path and os.path.exists(model_path):
        detector = YoloDetector(model_path, float(os.environ.get("CONF_THRESHOLD", "0.5")))
        log.info("Usando modelo YOLO: %s", model_path)
    else:
        detector = MotionDetector()
        watch = {"movimiento"}
        log.info("Sin MODEL_PATH: usando detección de movimiento")

    http = httpx.Client(timeout=10)
    interval = 1.0 / fps
    while True:
        cap = cv2.VideoCapture(source)
        if not cap.isOpened():
            log.warning("No se pudo abrir %s; reintento en 5 s", source)
            time.sleep(5)
            continue
        log.info("Analizando %s a %.1f FPS", source, fps)
        # Un archivo local se leería entero en un instante: lo reproducimos a su velocidad real.
        is_file = "://" not in source
        frame_delay = 1.0 / (cap.get(cv2.CAP_PROP_FPS) or 25.0) if is_file else 0.0
        last = 0.0
        while True:
            ok, frame = cap.read()
            if not ok:
                log.warning("Se perdió el video; reconectando")
                break
            if frame_delay:
                time.sleep(frame_delay)
            now = time.monotonic()
            if now - last < interval:
                continue
            last = now
            for label, n in summarize(detector.detect(frame), watch, min_count).items():
                if not throttle.should_alert(label, now):
                    continue
                body = {
                    "source": "softmind-ai-worker",
                    "caption": f"IA: {label} detectado ({n})",
                    "description": f"{n} objeto(s) '{label}' en {source}",
                    "cameraIds": [camera_id] if camera_id else [],
                }
                try:
                    http.post(f"{backend}/api/events/generic", json=body).raise_for_status()
                    log.info("Evento enviado: %s", body["caption"])
                except httpx.HTTPError as exc:
                    log.error("No se pudo enviar el evento: %s", exc)
        cap.release()
        time.sleep(2)


if __name__ == "__main__":
    main()
