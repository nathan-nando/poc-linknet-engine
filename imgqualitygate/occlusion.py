import numpy as np

def check_occlusion(image, near_black, threshold):
    gray = image.mean(axis=2)

    black_pixels = np.sum(gray < near_black)

    ratio = black_pixels / gray.size

    return {
        "passed": ratio < threshold,
        "score": ratio
    }