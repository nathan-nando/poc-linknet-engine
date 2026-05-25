import os
from ultralytics import YOLO

def main():
    model_path = "models/best.pt"
    if not os.path.exists(model_path):
        print(f"Error: Could not find model at {model_path}")
        print("Please ensure you run this script from the 'engine' directory.")
        return

    print(f"Loading PyTorch model from {model_path}...")
    model = YOLO(model_path)

    print("\nExporting model to ONNX format...")
    print("Optimization parameters: format='onnx', half=True (FP16), dynamic=True")
    
    # Export to ONNX
    # half=True: Uses FP16 precision for faster inference
    # dynamic=False, simplify=False: Mencegah OOM (Error 137) di memori lokal (WSL)
    # imgsz=832: Cocokkan dengan resolusi training agar akurasi tetap tinggi
    model.export(format="onnx", half=True, dynamic=False, simplify=False, imgsz=832)
    
    onnx_path = model_path.replace(".pt", ".onnx")
    if os.path.exists(onnx_path):
        print(f"\nSuccess! ONNX model exported to: {onnx_path}")
        print("The engine will automatically detect and use this optimized model.")
    else:
        print("\nExport failed. Check the logs above.")

if __name__ == "__main__":
    main()
