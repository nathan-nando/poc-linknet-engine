import numpy as np

def check_orientation(image: np.ndarray, expected: str = "portrait") -> dict:
    """
    Checks if the image matches the expected orientation.
    expected can be "portrait" or "landscape".
    Returns a dict with 'passed' and 'score' (which is just 1.0 or 0.0 for this rule).
    """
    height, width = image.shape[:2]
    
    is_portrait = height >= width
    is_landscape = width > height
    
    if expected.lower() == "portrait":
        passed = is_portrait
    elif expected.lower() == "landscape":
        passed = is_landscape
    else:
        # Default fallback if config is weird
        passed = True

    return {
        "passed": passed,
        "score": 1.0 if passed else 0.0,
        "width": width,
        "height": height
    }
