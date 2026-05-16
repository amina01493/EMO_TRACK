# EMO_TRACK: Watch-to-Server Emotion Detection Handover

## Overview
This project integrates real-time emotion detection into a child safety system, utilizing a Flutter mobile application designed for the Modio ST13 smartwatch and a Python/Flask backend server powered by YOLOv8 and DeepFace.

## Current Project State
The project is fully functional and ready for local network testing.
- **Backend (`app.py` & `detection_utils.py`)**: The server initializes YOLOv8 and DeepFace upon startup and listens for incoming image POST requests at the `/api/detect-emotion` endpoint.
- **Frontend (`lib/main.dart`)**: The Flutter app successfully captures images using the device's camera, sends them to the configured server IP, and dynamically displays the returned emotion along with its confidence score.
- **Settings**: A Network Configuration section in the `SettingsScreen` allows users to dynamically update the server's local IP address, saving it persistently via `shared_preferences`.
- **Build**: The production-ready APK (`app-release.apk`) has been successfully built for deployment to the Modio ST13 watch.

## Important Details & Requirements
- **Local Network**: The watch and the computer running the server *must* be connected to the exact same Wi-Fi network.
- **Model Loading Delay**: The initial detection request might take slightly longer (around 10-20 seconds) as YOLOv8 and DeepFace load their models into memory for the first time.
- **Windows Firewall**: If the app fails to connect to the server, ensure that your Windows Firewall allows inbound connections on port `5000` (the default port for the Flask app).

## Getting Started
1. Start the Flask server:
   ```bash
   python app.py
   ```
2. Note your PC's IP address (e.g., `192.168.1.X`).
3. Install the generated APK on the smartwatch (`build\app\outputs\flutter-apk\app-release.apk`).
4. Open the app, navigate to Settings, enter the PC's IP address, and proceed to the Camera screen to test detection.

## Future Recommendations
- Implement loading state animations while the AI model processes the first image.
- Add offline fallback handling if the local server is unreachable.
- Optimize the YOLOv8 model (e.g., using a `.tflite` or `.onnx` version) if you plan to move detection entirely to the smartwatch in the future.
