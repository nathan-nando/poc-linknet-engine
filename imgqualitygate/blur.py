import cv2

def check_blur(image, threshold):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    score = cv2.Laplacian(
        gray,
        cv2.CV_64F
    ).var()

    return {
        "passed": score >= threshold,
        "score": score
    }