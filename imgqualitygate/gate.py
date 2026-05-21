import cv2
import numpy as np

# Asumsi fungsi blur, brightness, occlusion sudah kamu buat dan menerima np.ndarray
from .blur import check_blur
from .brightness import check_brightness
from .occlusion import check_occlusion
from .orientation import check_orientation

def run_quality_gate(image: np.ndarray, config: dict):
    reasons = []
    scores = {}

    # Mengambil dari struktur YAML yang sudah kita standarisasi
    iq_config = config.get("image_quality_gate", {})

    # ORIENTATION
    orient_cfg = iq_config.get("orientation", {})
    if orient_cfg:
        orient_result = check_orientation(
            image=image,
            expected=orient_cfg.get("expected", "portrait")
        )
        scores["orientation"] = orient_result["score"]
        if not orient_result["passed"]:
            reasons.append(orient_cfg.get("reject_reason", "Orientasi gambar salah"))

    # BLUR
    blur_cfg = iq_config.get("blur", {})
    blur_result = check_blur(
        image=image,
        threshold=blur_cfg.get("threshold", 100.0)
    )
    scores["blur"] = blur_result["score"]
    if not blur_result["passed"]:
        reasons.append(blur_cfg.get("reject_reason", "Gambar terlalu blur"))

    # BRIGHTNESS
    bright_cfg = iq_config.get("brightness", {})
    brightness_result = check_brightness(
        image=image,
        min_value=bright_cfg.get("min", 40),
        max_value=bright_cfg.get("max", 220)
    )
    scores["brightness"] = brightness_result["score"]
    if not brightness_result["passed"]:
        if brightness_result["score"] < bright_cfg.get("min", 80):
            reasons.append(bright_cfg.get("reject_reason_dark", "Gambar terlalu gelap, pastikan pencahayaan cukup"))
        else:
            reasons.append(bright_cfg.get("reject_reason_over", "Gambar terlalu terang (overexposed), hindari cahaya langsung ke lensa"))

    # OCCLUSION
    occ_cfg = iq_config.get("occlusion", {})
    occlusion_result = check_occlusion(
        image=image,
        near_black=occ_cfg.get("near_black_value", 15),
        threshold=occ_cfg.get("threshold", 0.85)
    )
    scores["occlusion"] = occlusion_result["score"]
    if not occlusion_result["passed"]:
        reasons.append(occ_cfg.get("reject_reason", "Lensa tertutup"))

    return {
        "passed": len(reasons) == 0,
        "reasons": reasons,
        "scores": scores
    }