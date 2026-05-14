from ultralytics import YOLO
from deepface import DeepFace
import cv2
import numpy as np

# Load YOLO (general model)
model = YOLO("yolov8n.pt")

# Open webcam
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    results = model(frame)

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

            emotion = analysis[0]['dominant_emotion']

            # Draw bounding box
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 3)

            # Draw emotion text
            cv2.putText(frame, emotion, (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)

        except:
            pass

    # Display result
    cv2.imshow("Emotion Detection (Face Only)", frame)

    # Press Q to quit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()