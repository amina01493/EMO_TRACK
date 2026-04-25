# Child Safety & Emotion Detection - Flutter Mobile App

## 📱 Mobile App Setup Guide

This is a complete **Flutter mobile application** for the Child Safety & Emotion Detection system.

### What's Included

✅ **Flutter App (main.dart)** - Complete mobile application with:
- Splash screen
- Login & Register screens
- Dashboard with child cards
- Children management
- Camera screen for emotion detection
- Location tracking
- Medical reports
- Settings & profile

✅ **Project Configuration (pubspec.yaml)** - All dependencies configured

### System Requirements

- **Flutter SDK**: 3.0.0 or higher
- **Dart**: 3.0.0 or higher
- **Android**: API 21+ (for Android development)
- **iOS**: iOS 11.0+ (for iOS development)

### Installation Steps

#### 1. Install Flutter
```bash
# Download Flutter from https://flutter.dev/docs/get-started/install
# Add Flutter to your PATH
flutter doctor
```

#### 2. Create New Flutter Project
```bash
flutter create child_safety_app
cd child_safety_app
```

#### 3. Replace Files
Copy these files into your Flutter project:
- Replace `lib/main.dart` with the provided `main.dart`
- Replace `pubspec.yaml` with the provided `pubspec.yaml`

#### 4. Get Dependencies
```bash
flutter pub get
```

#### 5. Run the App

**Android:**
```bash
flutter run -d <device_id>
# Or for emulator:
flutter run
```

**iOS:**
```bash
flutter run -d <device_id>
# Or for simulator:
flutter run
```

**Web (Optional):**
```bash
flutter run -d chrome
```

### Project Structure

```
child_safety_app/
├── lib/
│   └── main.dart                 # Main app file (all screens)
├── android/                       # Android native code
├── ios/                          # iOS native code
├── pubspec.yaml                  # Dependencies
└── README.md                      # This file
```

### App Features

#### 🏠 Home Screen
- Welcome message
- Statistics (Total children, alerts, check-ins)
- Child cards with emotion status
- Recent alerts display

#### 👶 Children Management
- View all children
- Add new children
- Child details (age, gender, bracelet code)
- Edit child information
- Emotion detection status

#### 📹 Camera Screen
- Real-time emotion detection
- Emotion confidence score
- Record video
- Upload recordings

#### 📍 Location Tracking
- Google Maps integration
- Location history
- Time spent at locations
- Location markers

#### 🏥 Medical Information
- Disease records
- Medication tracking
- Allergy management
- Medical history

#### ⚙️ Settings
- Account management
- Password change
- Language selection (English/Arabic)
- Notification preferences
- Location tracking toggle
- Logout

### API Integration

The app connects to your Flask backend at: `http://192.168.1.100:5000`

**Update the API URL in main.dart:**
```dart
// Change this line in the _login() and _register() functions:
Uri.parse('http://192.168.1.100:5000/login'),  // Change IP address
```

### API Endpoints Required

- `POST /login` - User authentication
- `POST /register` - User registration
- `GET /children` - Fetch children list
- `POST /children` - Add new child
- `PUT /children/<id>` - Update child
- `GET /children/<id>/emotions` - Emotion history
- `GET /children/<id>/locations` - Location history
- `POST /upload/recording` - Upload video

### Dependencies Explained

```yaml
http:                    # HTTP requests to backend
camera:                  # Camera access for emotion detection
image_picker:           # Select images from gallery
geolocator:            # GPS location tracking
google_maps_flutter:    # Google Maps integration
provider:              # State management
shared_preferences:    # Local data storage
intl:                  # Localization (English/Arabic)
```

### Firebase Setup (Optional)

For push notifications and real-time updates:

#### Android Setup
1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Create new project
3. Download `google-services.json`
4. Place in `android/app/`

#### iOS Setup
1. Download `GoogleService-Info.plist`
2. Add to iOS project in Xcode

### Building for Release

#### Android APK
```bash
flutter build apk
```

#### Android App Bundle (Google Play)
```bash
flutter build appbundle
```

#### iOS App
```bash
flutter build ios
```

### Debugging

**View logs:**
```bash
flutter logs
```

**Connect to device:**
```bash
flutter devices
flutter run -d <device_id>
```

**Run in debug mode:**
```bash
flutter run -v
```

### Common Issues

**1. Device not found:**
```bash
flutter doctor -v
flutter devices
```

**2. Build fails:**
```bash
flutter clean
flutter pub get
flutter run
```

**3. Permissions issues:**
Edit `android/app/src/main/AndroidManifest.xml`:
```xml
<uses-permission android:name="android.permission.CAMERA" />
<uses-permission android:name="android.permission.ACCESS_FINE_LOCATION" />
<uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION" />
<uses-permission android:name="android.permission.INTERNET" />
```

### Color Scheme

- **Primary:** #4A90E2 (Trust Blue)
- **Secondary:** #F5A623 (Warm Orange)
- **Success:** #7ED321 (Green)
- **Danger:** #D0021B (Red)
- **Happy:** #FFD93D (Yellow)
- **Sad:** #6C63FF (Purple)
- **Angry:** #E94B3C (Red-Orange)
- **Neutral:** #95A5A6 (Gray)
- **Surprised:** #1ABC9C (Teal)

### App Screens

1. **Splash Screen** - App intro
2. **Login Screen** - User authentication
3. **Register Screen** - New user signup
4. **Dashboard** - Home with children overview
5. **Children Screen** - Manage children
6. **Camera Screen** - Emotion detection
7. **Locations Screen** - Location tracking
8. **Settings Screen** - User preferences

### Testing

```bash
# Run unit tests
flutter test

# Run widget tests
flutter test test/

# Run integration tests
flutter drive --target=test_driver/app.dart
```

### Deployment Checklist

- [ ] Update API URLs for production
- [ ] Set proper app icons
- [ ] Configure app name and version
- [ ] Test on real devices
- [ ] Setup signing keys
- [ ] Configure privacy policy
- [ ] Test all features
- [ ] Performance optimization
- [ ] Release notes

### Support & Documentation

- **Flutter Docs:** https://flutter.dev/docs
- **Dart Docs:** https://dart.dev/guides
- **Package Pub:** https://pub.dev
- **Firebase:** https://firebase.google.com/docs/flutter/setup

### License

Copyright © 2026 Child Safety App. All rights reserved.

---

**Created:** January 18, 2026
**Version:** 1.0.0
**Platform:** iOS & Android
