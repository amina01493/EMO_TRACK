import cv2
import numpy as np
from ultralytics import YOLO
from deepface import DeepFace

class EmotionDetector:
    def __init__(self):
        # Load YOLO model
        print("Loading YOLOv8 model...")
        self.model = YOLO("yolov8n.pt")
        print("YOLOv8 model loaded.")
        
    def detect_emotion(self, image_bytes):
        """
        Takes raw image bytes, runs face detection using YOLO,
        and emotion detection using DeepFace.
        Returns a dict with emotion, confidence, and bounding box.
        """
        # Convert bytes to numpy array
        nparr = np.frombuffer(image_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if frame is None:
            return {"error": "Invalid image format"}

        results = self.model(frame)
        
        detected_emotions = []

        for box in results[0].boxes:
            # Detect class (0 = person)
            cls = int(box.cls[0])
            
            # Skip anything that is NOT a person
            if cls != 0:
                continue
                
            # Extract bounding box
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            
            # Crop face region
            face_roi = frame[y1:y2, x1:x2]
            
            if face_roi.size == 0:
                continue
                
            try:
                # Run emotion detection on the face ONLY
                analysis = DeepFace.analyze(
                    face_roi,
                    actions=['emotion'],
                    enforce_detection=False
                )
                
                if isinstance(analysis, list):
                    analysis = analysis[0]
                    
                emotion = analysis['dominant_emotion']
                emotion_scores = analysis['emotion']
                confidence = emotion_scores[emotion]
                
                detected_emotions.append({
                    "emotion": emotion,
                    "confidence": confidence,
                    "bbox": [x1, y1, x2, y2]
                })
            except Exception as e:
                print(f"DeepFace analysis failed: {e}")
                pass
                
        if not detected_emotions:
            return {"error": "No person/emotion detected"}
            
        # Return the first detected person's emotion
        return {"success": True, "data": detected_emotions[0]}
