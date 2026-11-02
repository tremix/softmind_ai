import numpy as np

from detector import Detection, MotionDetector, yolo_postprocess
from worker import AlertThrottle, summarize


def test_yolo_postprocess_scales_boxes_and_filters():
    out = np.zeros((1, 84, 3), dtype=np.float32)
    # Detección 0: persona con confianza 0.9 en el centro de una entrada 640x640.
    out[0, :4, 0] = [320, 320, 100, 200]
    out[0, 4 + 0, 0] = 0.9
    # Detección 1: coche con confianza baja (se descarta).
    out[0, :4, 1] = [100, 100, 50, 50]
    out[0, 4 + 2, 1] = 0.2
    # Detección 2: clase no vigilada (índice 10) → se ignora.
    out[0, :4, 2] = [500, 500, 50, 50]
    out[0, 4 + 10, 2] = 0.95

    dets = yolo_postprocess(out, frame_w=1280, frame_h=720, input_size=640, conf_threshold=0.5)
    assert len(dets) == 1
    d = dets[0]
    assert d.label == "persona"
    assert d.box == (540, 247, 200, 225)  # escala x2 en ancho, x1.125 en alto


def test_motion_detector_finds_moving_square():
    det = MotionDetector(min_area=100)
    blank = np.zeros((240, 320, 3), dtype=np.uint8)
    noisy = np.full((240, 320, 3), 200, dtype=np.uint8)
    assert det.detect(noisy) == []  # el primer frame no cuenta como movimiento
    for _ in range(30):
        det.detect(blank)
    frame = blank.copy()
    frame[100:150, 100:150] = 255
    assert any(d.label == "movimiento" for d in det.detect(frame))


def test_summarize_and_throttle():
    dets = [Detection("persona", 0.9, (0, 0, 1, 1))] * 3 + [Detection("coche", 0.8, (0, 0, 1, 1))]
    assert summarize(dets, {"persona"}, min_count=2) == {"persona": 3}
    t = AlertThrottle(cooldown_s=30)
    assert t.should_alert("persona", 0)
    assert not t.should_alert("persona", 10)
    assert t.should_alert("persona", 31)
