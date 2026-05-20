import numpy as np

def check_brightness(image, min_value, max_value):
    mean = np.mean(image)

    return {
        "passed": min_value <= mean <= max_value,
        "score": mean
    }