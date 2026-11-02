"""Detectores: YOLO (ONNX) y detección de movimiento como alternativa sin modelo."""

from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

# Nombres de clases COCO más útiles para videovigilancia (índice → nombre).
COCO_NAMES = {0: "persona", 1: "bicicleta", 2: "coche", 3: "moto", 5: "autobús", 7: "camión"}


@dataclass
class Detection:
    label: str
    score: float
    box: tuple[int, int, int, int]  # x, y, ancho, alto en píxeles del frame original


def yolo_postprocess(
    output: np.ndarray, frame_w: int, frame_h: int, input_size: int,
    conf_threshold: float, nms_threshold: float = 0.45,
) -> list[Detection]:
    """Convierte la salida de YOLOv8/YOLO11 (1, 4+clases, N) en detecciones."""
    preds = output[0].T  # (N, 4+clases)
    scores = preds[:, 4:]
    class_ids = scores.argmax(axis=1)
    confs = scores[np.arange(len(scores)), class_ids]
    keep = confs >= conf_threshold
    preds, class_ids, confs = preds[keep], class_ids[keep], confs[keep]
    if len(preds) == 0:
        return []

    sx, sy = frame_w / input_size, frame_h / input_size
    boxes = []
    for cx, cy, w, h in preds[:, :4]:
        boxes.append([int((cx - w / 2) * sx), int((cy - h / 2) * sy), int(w * sx), int(h * sy)])

    idxs = cv2.dnn.NMSBoxes(boxes, confs.tolist(), conf_threshold, nms_threshold)
    result = []
    for i in np.array(idxs).flatten():
        cid = int(class_ids[i])
        if cid in COCO_NAMES:
            result.append(Detection(COCO_NAMES[cid], float(confs[i]), tuple(boxes[i])))
    return result


class YoloDetector:
    def __init__(self, model_path: str, conf_threshold: float = 0.5, input_size: int = 640):
        import onnxruntime as ort

        self.session = ort.InferenceSession(model_path, providers=ort.get_available_providers())
        self.input_name = self.session.get_inputs()[0].name
        self.conf_threshold = conf_threshold
        self.input_size = input_size

    def detect(self, frame: np.ndarray) -> list[Detection]:
        h, w = frame.shape[:2]
        img = cv2.resize(frame, (self.input_size, self.input_size))
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
        tensor = np.transpose(img, (2, 0, 1))[None]
        output = self.session.run(None, {self.input_name: tensor})[0]
        return yolo_postprocess(output, w, h, self.input_size, self.conf_threshold)


class MotionDetector:
    """Detecta zonas en movimiento con sustracción de fondo. No necesita modelo."""

    def __init__(self, min_area: int = 1500, warmup_frames: int = 5):
        self.bg = cv2.createBackgroundSubtractorMOG2(history=300, varThreshold=32, detectShadows=False)
        self.min_area = min_area
        # Los primeros frames se usan solo para aprender el fondo (si no, todo parece movimiento).
        self.warmup_frames = warmup_frames
        self._seen = 0

    def detect(self, frame: np.ndarray) -> list[Detection]:
        mask = self.bg.apply(frame)
        self._seen += 1
        if self._seen <= self.warmup_frames:
            return []
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        return [
            Detection("movimiento", 1.0, cv2.boundingRect(c))
            for c in contours if cv2.contourArea(c) >= self.min_area
        ]
