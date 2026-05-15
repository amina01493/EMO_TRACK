# 🛡️ EMO_TRACK: Modio Smartwatch Safety Ecosystem

A production-grade ecosystem for the **Modio ST13** smartwatch, enabling parents to remotely monitor their child's location, health, and emotional state.

![Dashboard Preview](static/latest_capture.jpg)

## ✨ Key Features

- **🎭 Emotion Detection:** Real-time AI analysis of the child's mood using the watch camera.
- **🔒 Remote Security:** Instant remote screen lock and control dimming from the dashboard.
- **📈 Telemetry History:** Detailed logs of heart rate, battery level, and location.
- **📍 Smart Geo-Fencing:** Create safe zones and receive alerts if the child exits them.
- **🎥 Live Monitoring:** On-demand camera feed and recording capabilities.
- **🔄 Auto-Update Sync:** Direct integration with GitHub releases for easy watch app updates.

---

## 🖥️ Server Setup (Windows & macOS)

The backend is built with Flask and Python 3.10+.

### 1. Prerequisites
- **Python 3.10+** installed.
- **Git** installed.

### 2. Installation Steps

#### Windows (PowerShell)
```powershell
# Clone the repository
git clone https://github.com/simplehima/EMO_TRACK.git
cd EMO_TRACK

# Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Start the server
python app.py
```

#### macOS / Linux (Terminal)
```bash
# Clone the repository
git clone https://github.com/simplehima/EMO_TRACK.git
cd EMO_TRACK

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start the server
python3 app.py
```

---

## ⌚ Watch App Setup (Flutter)

The watch app is built with Flutter and optimized for Android-based smartwatches.

### 1. Prerequisites
- **Flutter SDK** (Stable channel).
- **Android SDK** (Command-line tools or Android Studio).

### 2. Build Instructions
```bash
# Get dependencies
flutter pub get

# Build for all architectures
flutter build apk --release --split-per-abi
```

### 3. Installation
1. Locate the APKs in `build/app/outputs/flutter-apk/`.
2. For the **Modio ST13**, use the **`app-armeabi-v7a-release.apk`**.
3. Install via ADB or by transferring the file to the watch storage.

---

## 🔗 Connecting the Watch to the Server

1. **Auto-Discovery:** The watch will automatically scan your local network for the server IP when launched.
2. **Manual Setup:** If auto-discovery fails, go to **Settings** on the watch and enter the **Server IP** manually (e.g., `192.168.1.100`).
3. **Identity:** Each watch generates a unique Hardware ID. Register this ID in your Parent Dashboard to start monitoring.

---

## 🛠️ Development & Versions
- **Server Version:** 1.0.5
- **App Version:** 1.0.5+1005
- **Database:** SQLite (SQLAlchemy)

## 📄 License
This project is for educational and security research purposes. All rights reserved.
