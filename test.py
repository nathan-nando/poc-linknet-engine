import sys
try:
    from ultralytics import YOLO
    print("Success! Ultralytics imported without torch.")
except Exception as e:
    print(f"Error importing ultralytics: {e}")
