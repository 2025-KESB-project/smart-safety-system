import os

class Config:
    PORT = int(os.getenv("PORT", 8080))
    MODEL_PATH = os.getenv("MODEL_PATH", "models/yolo_models/best.pt")
    THRESHOLD = float(os.getenv("THRESHOLD", 0.45))