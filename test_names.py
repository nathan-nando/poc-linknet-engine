from ultralytics import YOLO

print("Loading PT...")
model_pt = YOLO('models/best.pt', task='detect')
print('PT Names:', model_pt.names)
