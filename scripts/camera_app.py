#!/usr/bin/env python3
"""
camera_app.py

Lightweight webcam app that runs YOLO for person detection and DeepFace for
emotion analysis on detected faces. Usage:
    python camera_app.py --model yolov8n.pt --camera 0

This file reuses the logic from `emotion_detection.py` but adds CLI args,
FPS display, and safer error handling.
"""
import argparse
import time
from ultralytics import YOLO
from deepface import DeepFace
import cv2
import numpy as np


def parse_args():
    p = argparse.ArgumentParser(description="Webcam emotion detection (YOLO + DeepFace)")
    p.add_argument('--model', type=str, default='yolov8n.pt', help='Path to YOLO model')
    p.add_argument('--camera', type=int, default=0, help='Camera index for cv2.VideoCapture')
    p.add_argument('--width', type=int, default=640, help='Resize width for webcam frames (keeps aspect)')
    p.add_argument('--show-fps', action='store_true', help='Show FPS on the window')
    return p.parse_args()


def main():
    args = parse_args()

    # Load YOLO model
    model = YOLO(args.model)

    # Try opening camera with a couple of backends (helps on macOS)
    def open_camera(index):
        # Try AVFoundation first (macOS), then default
        backends = [cv2.CAP_AVFOUNDATION, cv2.CAP_ANY]
        for b in backends:
            cap = cv2.VideoCapture(index, b)
            if cap.isOpened():
                print(f"Opened camera index {index} using backend {b}")
                return cap
            else:
                try:
                    cap.release()
                except Exception:
                    pass
        return None

    cap = open_camera(args.camera)
    if cap is None:
        # Try a few other indices for convenience
        for i in range(1, 4):
            cap = open_camera(i)
            if cap is not None:
                break

    if cap is None or not cap.isOpened():
        print(f"Error: cannot open any camera (tried indices 0-3). On macOS ensure the Terminal/python has Camera permission.")
        return

    prev_time = time.time()
    fps = 0.0

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Failed to read frame from camera")
                break

            # Optionally resize to speed up processing
            h, w = frame.shape[:2]
            if args.width and w != args.width:
                new_h = int(h * (args.width / w))
                frame = cv2.resize(frame, (args.width, new_h))

            # Run YOLO on the frame
            results = model(frame)

            for box in results[0].boxes:
                cls = int(box.cls[0])
                if cls != 0:
                    continue

                x1, y1, x2, y2 = map(int, box.xyxy[0])
                # Clamp coordinates
                x1, y1 = max(0, x1), max(0, y1)
                x2, y2 = min(frame.shape[1], x2), min(frame.shape[0], y2)

                face_roi = frame[y1:y2, x1:x2]
                if face_roi.size == 0:
                    continue

                try:
                    analysis = DeepFace.analyze(face_roi, actions=['emotion'], enforce_detection=False)
                    # DeepFace returns a list or dict depending on version; handle both
                    emotion = None
                    if isinstance(analysis, list) and len(analysis) > 0:
                        emotion = analysis[0].get('dominant_emotion')
                    elif isinstance(analysis, dict):
                        emotion = analysis.get('dominant_emotion')

                    if emotion:
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                        cv2.putText(frame, str(emotion), (x1, max(0, y1 - 10)),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

                except Exception:
                    # Ignore per-face errors to keep the app running
                    pass

            # FPS calculation
            cur_time = time.time()
            dt = cur_time - prev_time
            prev_time = cur_time
            if dt > 0:
                fps = 0.9 * fps + 0.1 * (1.0 / dt) if fps else (1.0 / dt)

            if args.show_fps:
                cv2.putText(frame, f"FPS: {fps:.1f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 255), 2)

            cv2.imshow('Emotion Detection (webcam)', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    finally:
        cap.release()
        cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
