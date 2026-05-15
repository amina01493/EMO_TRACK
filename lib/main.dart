import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:camera/camera.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:path_provider/path_provider.dart';
import 'package:open_filex/open_filex.dart';
import 'dart:io';
import 'dart:async';
import 'package:geolocator/geolocator.dart';
import 'package:battery_plus/battery_plus.dart';
import 'package:package_info_plus/package_info_plus.dart';
import 'package:device_info_plus/device_info_plus.dart';
import 'dart:math' as math;

List<CameraDescription> cameras = [];
String serverIp = '';
String braceletCode = '';
bool remoteLoggingEnabled = false;

Future<void> remoteLog(String message) async {
  debugPrint(message);
  if (!remoteLoggingEnabled || serverIp.isEmpty) return;
  try {
    await http.post(
      Uri.parse('http://$serverIp:5000/api/logs'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'log': message}),
    ).timeout(const Duration(seconds: 2));
  } catch (_) {}
}

class DiscoveryService {
  /// Gets the device's local IP address to determine the subnet.
  static Future<String?> _getLocalIp() async {
    try {
      for (var interface in await NetworkInterface.list()) {
        for (var addr in interface.addresses) {
          if (addr.type == InternetAddressType.IPv4 && !addr.isLoopback) {
            return addr.address;
          }
        }
      }
    } catch (e) {
      debugPrint("Failed to get local IP: $e");
    }
    return null;
  }

  /// Checks if a specific IP is running the EMO_TRACK server.
  static Future<String?> _probeIp(String ip) async {
    try {
      final response = await http.get(
        Uri.parse('http://$ip:5000/api/app-version'),
      ).timeout(const Duration(milliseconds: 800));
      if (response.statusCode == 200) {
        return ip;
      }
    } catch (_) {}
    return null;
  }

  /// Scans the local subnet in parallel for the server.
  static Future<String?> findServer({Function(String)? onStatus}) async {
    final localIp = await _getLocalIp();
    if (localIp == null) {
      debugPrint("DiscoveryService: Could not determine local IP.");
      return null;
    }

    // Extract subnet prefix (e.g., "192.168.1")
    final parts = localIp.split('.');
    if (parts.length != 4) return null;
    final subnet = '${parts[0]}.${parts[1]}.${parts[2]}';

    debugPrint("DiscoveryService: Local IP is $localIp, scanning $subnet.0/24...");
    onStatus?.call("Scanning $subnet.*");

    // Launch all 254 probes in parallel with a global timeout
    final completer = Completer<String?>();
    int remaining = 254;

    for (int i = 1; i <= 254; i++) {
      final targetIp = '$subnet.$i';
      _probeIp(targetIp).then((result) {
        if (result != null && !completer.isCompleted) {
          debugPrint("DiscoveryService: Server found at $result!");
          completer.complete(result);
        }
        remaining--;
        if (remaining == 0 && !completer.isCompleted) {
          completer.complete(null);
        }
      });
    }

    // Global timeout of 12 seconds
    return completer.future.timeout(
      const Duration(seconds: 12),
      onTimeout: () => null,
    );
  }
}

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  try {
    cameras = await availableCameras();
  } on CameraException catch (e) {
    debugPrint('Error initializing cameras: $e');
  }
  
  final prefs = await SharedPreferences.getInstance();
  serverIp = prefs.getString('serverIp') ?? '';
  braceletCode = prefs.getString('braceletCode') ?? '';
  remoteLoggingEnabled = prefs.getBool('remoteLoggingEnabled') ?? false;

  if (braceletCode.isEmpty) {
    try {
      final deviceInfo = DeviceInfoPlugin();
      if (Platform.isAndroid) {
        final androidInfo = await deviceInfo.androidInfo;
        braceletCode = androidInfo.id; // Unique hardware ID
        await prefs.setString('braceletCode', braceletCode);
      }
    } catch (e) {
      final random = math.Random();
      final id = List.generate(4, (_) => random.nextInt(10)).join();
      braceletCode = 'WATCH-$id'; // Fallback
    }
  }

  runApp(const ChildSafetyApp());
}

class ChildSafetyApp extends StatelessWidget {
  const ChildSafetyApp({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Child Safety App',
      theme: ThemeData(
        primaryColor: const Color(0xFF4A90E2),
        scaffoldBackgroundColor: const Color(0xFFF7F7F7),
        useMaterial3: true,
      ),
      home: const SplashScreen(),
    );
  }
}

// Splash Screen
class SplashScreen extends StatefulWidget {
  const SplashScreen({Key? key}) : super(key: key);

  @override
  State<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends State<SplashScreen> {
  String _status = "Initializing...";

  @override
  void initState() {
    super.initState();
    _initApp();
  }

  Future<void> _initApp() async {
    setState(() => _status = "Scanning network for server...");
    
    // Attempt auto-discovery via HTTP subnet scan
    String? foundIp = await DiscoveryService.findServer(
      onStatus: (msg) {
        if (mounted) setState(() => _status = msg);
      },
    );
    
    if (foundIp != null) {
      serverIp = foundIp;
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString('serverIp', foundIp);
      setState(() => _status = "Server found: $foundIp ✓");
    } else if (serverIp.isNotEmpty) {
      setState(() => _status = "Using saved IP: $serverIp");
    } else {
      setState(() => _status = "No server found. Set IP in Settings.");
    }

    await Future.delayed(const Duration(seconds: 2));
    
    if (mounted) {
      Navigator.of(context).pushReplacement(
        MaterialPageRoute(builder: (context) => const LoginScreen()),
      );
    }
    
    remoteLog("App ready. Server IP: $serverIp");
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
            colors: [Color(0xFF4A90E2), Color(0xFF357ABD)],
          ),
        ),
        child: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Text(
                '🛡️',
                style: TextStyle(fontSize: 80),
              ),
              const SizedBox(height: 20),
              const Text(
                'Child Safety App',
                style: TextStyle(
                  fontSize: 28,
                  fontWeight: FontWeight.bold,
                  color: Colors.white,
                ),
              ),
              const SizedBox(height: 10),
              Text(
                _status,
                style: const TextStyle(
                  fontSize: 14,
                  color: Colors.white70,
                ),
              ),
              const SizedBox(height: 30),
              const SizedBox(
                width: 40,
                child: LinearProgressIndicator(
                  backgroundColor: Colors.white24,
                  valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

// Login Screen
class LoginScreen extends StatefulWidget {
  const LoginScreen({Key? key}) : super(key: key);

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  bool _isLoading = false;
  bool _obscurePassword = true;

  Future<void> _login() async {
    setState(() => _isLoading = true);
    
    try {
      final response = await http.post(
        Uri.parse('http://$serverIp:5000/login'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'username': _emailController.text,
          'password': _passwordController.text,
        }),
      );

      if (response.statusCode == 200) {
        final responseData = jsonDecode(response.body);
        if (responseData['success'] == true) {
          Navigator.of(context).pushReplacement(
            MaterialPageRoute(builder: (context) => const ChildModeScreen()),
          );
        } else {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Invalid credentials')),
          );
        }
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Login failed - Server Error')),
        );
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error: $e')),
      );
    } finally {
      setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: SingleChildScrollView(
          child: Padding(
            padding: const EdgeInsets.all(24.0),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const SizedBox(height: 40),
                const Text(
                  '🛡️',
                  style: TextStyle(fontSize: 60),
                ),
                const SizedBox(height: 20),
                const Text(
                  'Child Safety App',
                  style: TextStyle(
                    fontSize: 24,
                    fontWeight: FontWeight.bold,
                    color: Color(0xFF4A90E2),
                  ),
                ),
                const SizedBox(height: 40),
                TextField(
                  controller: _emailController,
                  decoration: InputDecoration(
                    labelText: 'Email Address',
                    prefixIcon: const Icon(Icons.email),
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(8),
                    ),
                  ),
                ),
                const SizedBox(height: 16),
                TextField(
                  controller: _passwordController,
                  obscureText: _obscurePassword,
                  decoration: InputDecoration(
                    labelText: 'Password',
                    prefixIcon: const Icon(Icons.lock),
                    suffixIcon: IconButton(
                      icon: Icon(
                        _obscurePassword
                            ? Icons.visibility_off
                            : Icons.visibility,
                      ),
                      onPressed: () {
                        setState(
                          () => _obscurePassword = !_obscurePassword,
                        );
                      },
                    ),
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(8),
                    ),
                  ),
                ),
                const SizedBox(height: 24),
                SizedBox(
                  width: double.infinity,
                  height: 50,
                  child: ElevatedButton(
                    onPressed: _isLoading ? null : _login,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(0xFF4A90E2),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(8),
                      ),
                    ),
                    child: _isLoading
                        ? const SizedBox(
                            height: 20,
                            width: 20,
                            child: CircularProgressIndicator(
                              color: Colors.white,
                            ),
                          )
                        : const Text(
                            'Login',
                            style: TextStyle(
                              fontSize: 16,
                              fontWeight: FontWeight.bold,
                              color: Colors.white,
                            ),
                          ),
                  ),
                ),
                const SizedBox(height: 16),
                Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    const Text("Don't have an account? "),
                    TextButton(
                      onPressed: () {
                        Navigator.of(context).push(
                          MaterialPageRoute(
                            builder: (context) => const RegisterScreen(),
                          ),
                        );
                      },
                      child: const Text(
                        'Register',
                        style: TextStyle(color: Color(0xFF4A90E2)),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

// Register Screen
class RegisterScreen extends StatefulWidget {
  const RegisterScreen({Key? key}) : super(key: key);

  @override
  State<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends State<RegisterScreen> {
  final _usernameController = TextEditingController();
  final _emailController = TextEditingController();
  final _phoneController = TextEditingController();
  final _passwordController = TextEditingController();
  final _confirmPasswordController = TextEditingController();
  bool _isLoading = false;

  Future<void> _register() async {
    setState(() => _isLoading = true);

    try {
      final response = await http.post(
        Uri.parse('http://$serverIp:5000/register'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'username': _usernameController.text,
          'email': _emailController.text,
          'phone_number': _phoneController.text,
          'password': _passwordController.text,
        }),
      );

      if (response.statusCode == 200) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Registration successful!')),
        );
        Navigator.of(context).pop();
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Registration failed')),
        );
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error: $e')),
      );
    } finally {
      setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        elevation: 0,
        backgroundColor: Colors.transparent,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, color: Color(0xFF4A90E2)),
          onPressed: () => Navigator.of(context).pop(),
        ),
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          child: Padding(
            padding: const EdgeInsets.all(24.0),
            child: Column(
              children: [
                const Text(
                  'Create Account',
                  style: TextStyle(
                    fontSize: 24,
                    fontWeight: FontWeight.bold,
                    color: Color(0xFF4A90E2),
                  ),
                ),
                const SizedBox(height: 32),
                TextField(
                  controller: _usernameController,
                  decoration: InputDecoration(
                    labelText: 'Full Name',
                    prefixIcon: const Icon(Icons.person),
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(8),
                    ),
                  ),
                ),
                const SizedBox(height: 16),
                TextField(
                  controller: _emailController,
                  decoration: InputDecoration(
                    labelText: 'Email Address',
                    prefixIcon: const Icon(Icons.email),
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(8),
                    ),
                  ),
                ),
                const SizedBox(height: 16),
                TextField(
                  controller: _phoneController,
                  decoration: InputDecoration(
                    labelText: 'Phone Number',
                    prefixIcon: const Icon(Icons.phone),
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(8),
                    ),
                  ),
                ),
                const SizedBox(height: 16),
                TextField(
                  controller: _passwordController,
                  obscureText: true,
                  decoration: InputDecoration(
                    labelText: 'Password',
                    prefixIcon: const Icon(Icons.lock),
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(8),
                    ),
                  ),
                ),
                const SizedBox(height: 16),
                TextField(
                  controller: _confirmPasswordController,
                  obscureText: true,
                  decoration: InputDecoration(
                    labelText: 'Confirm Password',
                    prefixIcon: const Icon(Icons.lock),
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(8),
                    ),
                  ),
                ),
                const SizedBox(height: 24),
                SizedBox(
                  width: double.infinity,
                  height: 50,
                  child: ElevatedButton(
                    onPressed: _isLoading ? null : _register,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(0xFF4A90E2),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(8),
                      ),
                    ),
                    child: _isLoading
                        ? const SizedBox(
                            height: 20,
                            width: 20,
                            child: CircularProgressIndicator(
                              color: Colors.white,
                            ),
                          )
                        : const Text(
                            'Register',
                            style: TextStyle(
                              fontSize: 16,
                              fontWeight: FontWeight.bold,
                              color: Colors.white,
                            ),
                          ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

// Child Mode Screen - Simplified for Watch
class ChildModeScreen extends StatefulWidget {
  const ChildModeScreen({Key? key}) : super(key: key);

  @override
  State<ChildModeScreen> createState() => _ChildModeScreenState();
}

class _ChildModeScreenState extends State<ChildModeScreen> {
  bool _isMonitoring = false;
  bool _isRemoteLocked = false;
  String _status = "Disconnected";
  Timer? _monitoringTimer;
  CameraController? _cameraController;

  @override
  void initState() {
    super.initState();
    _checkServer();
    _initCamera();
  }

  Future<void> _initCamera() async {
    if (cameras.isEmpty) return;
    _cameraController = CameraController(cameras[0], ResolutionPreset.low);
    try {
      await _cameraController!.initialize();
      if (mounted) setState(() {});
    } catch (e) {
      print('Camera Error: $e');
    }
  }

  @override
  void dispose() {
    _monitoringTimer?.cancel();
    _cameraController?.dispose();
    super.dispose();
  }

  Future<void> _checkServer() async {
    try {
      final response = await http.get(Uri.parse('http://$serverIp:5000/api/app-version')).timeout(const Duration(seconds: 3));
      if (response.statusCode == 200) {
        setState(() => _status = "Connected");
      }
    } catch (e) {
      setState(() => _status = "Server Offline");
    }
  }

  void _toggleMonitoring(bool value) {
    setState(() {
      _isMonitoring = value;
    });
    
    if (_isMonitoring) {
      _startMonitoring();
    } else {
      _stopMonitoring();
    }
  }

  void _startMonitoring() {
    // Check location permission once
    Geolocator.requestPermission();

    // Capture every 5 seconds for live dashboard
    _monitoringTimer = Timer.periodic(const Duration(seconds: 5), (timer) {
      _captureAndSend();
      _sendWatchStatus();
    });
  }

  Future<void> _sendWatchStatus() async {
    if (serverIp.isEmpty) return;
    try {
      final battery = Battery();
      final level = await battery.batteryLevel;
      
      Position? pos;
      try {
        pos = await Geolocator.getCurrentPosition(
          desiredAccuracy: LocationAccuracy.high,
          timeLimit: const Duration(seconds: 2),
        );
      } catch (_) {}

      final response = await http.post(
        Uri.parse('http://$serverIp:5000/api/watch/location'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'bracelet_code': braceletCode,
          'latitude': pos?.latitude,
          'longitude': pos?.longitude,
          'battery_level': level,
          'heart_rate': 72 + (DateTime.now().second % 10), // Simulated variation for now
        }),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        if (data['is_locked'] != null) {
          setState(() {
            _isRemoteLocked = data['is_locked'];
          });
        }
      }
    } catch (e) {
      debugPrint("Watch Status Error: $e");
    }
  }

  void _stopMonitoring() {
    _monitoringTimer?.cancel();
  }

  Future<void> _captureAndSend() async {
    if (_cameraController == null || !_cameraController!.value.isInitialized || !_isMonitoring) return;
    
    try {
      final image = await _cameraController!.takePicture();
      var request = http.MultipartRequest('POST', Uri.parse('http://$serverIp:5000/api/detect-emotion'));
      request.fields['source'] = 'watch-app';
      request.fields['bracelet_code'] = braceletCode;
      request.files.add(await http.MultipartFile.fromPath('image', image.path));
      
      var response = await request.send();
      if (response.statusCode == 200) {
        print("Watch: Frame sent successfully");
      }
    } catch (e) {
      print("Watch: Capture error: $e");
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF5F7FB),
      body: Stack(
        children: [
          SafeArea(
            child: Padding(
              padding: const EdgeInsets.all(12.0),
              child: Column(
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      const Text(
                        "WATCH MODE",
                        style: TextStyle(
                          fontSize: 10,
                          fontWeight: FontWeight.bold,
                          color: Colors.grey,
                        ),
                      ),
                      IconButton(
                        icon: const Icon(Icons.settings, size: 18),
                        onPressed: () {
                          Navigator.of(context).push(
                            MaterialPageRoute(builder: (context) => const SettingsScreen()),
                          );
                        },
                      ),
                    ],
                  ),
                  const Spacer(),
                  // Camera Preview (Small Circle)
                  Container(
                    width: 100,
                    height: 100,
                    decoration: BoxDecoration(
                      color: Colors.white,
                      shape: BoxShape.circle,
                      border: Border.all(
                        color: _isMonitoring ? const Color(0xFF4A90E2) : Colors.grey,
                        width: 3,
                      ),
                      boxShadow: [
                        BoxShadow(
                          color: Colors.black.withOpacity(0.1),
                          blurRadius: 10,
                        ),
                      ],
                    ),
                    child: ClipOval(
                      child: _cameraController != null && _cameraController!.value.isInitialized
                          ? AspectRatio(
                              aspectRatio: 1,
                              child: CameraPreview(_cameraController!),
                            )
                          : Center(
                              child: Text(
                                _isMonitoring ? "📡" : "💤",
                                style: const TextStyle(fontSize: 30),
                              ),
                            ),
                    ),
                  ),
                  const SizedBox(height: 15),
                  Text(
                    _isMonitoring ? "Monitoring Active" : "Monitoring Paused",
                    style: const TextStyle(
                      fontSize: 14,
                      fontWeight: FontWeight.bold,
                      color: Color(0xFF2D3436),
                    ),
                  ),
                  const SizedBox(height: 5),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Container(
                        width: 6,
                        height: 6,
                        decoration: BoxDecoration(
                          color: _status == "Connected" ? Colors.green : Colors.red,
                          shape: BoxShape.circle,
                        ),
                      ),
                      const SizedBox(width: 6),
                      Text(
                        _status,
                        style: TextStyle(
                          fontSize: 10,
                          color: Colors.grey[600],
                        ),
                      ),
                    ],
                  ),
                  const Spacer(),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                    decoration: BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Row(
                      children: [
                        const Icon(Icons.security, color: Color(0xFF4A90E2), size: 16),
                        const SizedBox(width: 8),
                        const Expanded(
                          child: Text(
                            "Sending live face and mood data.",
                            style: TextStyle(fontSize: 9, color: Colors.grey),
                          ),
                        ),
                        if (!_isRemoteLocked)
                          Transform.scale(
                            scale: 0.8,
                            child: Switch(
                              value: _isMonitoring,
                              onChanged: _toggleMonitoring,
                              activeColor: const Color(0xFF4A90E2),
                            ),
                          ),
                        if (_isRemoteLocked)
                          const Padding(
                            padding: EdgeInsets.only(right: 8.0),
                            child: Icon(Icons.lock, size: 16, color: Colors.grey),
                          ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
          if (_isRemoteLocked)
            Positioned.fill(
              child: IgnorePointer(
                ignoring: false, // Catch all touches
                child: Container(
                  color: Colors.black.withOpacity(0.85), // Very dark
                  child: const Center(
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(Icons.lock, color: Colors.white54, size: 40),
                        SizedBox(height: 16),
                        Text(
                          "Device Locked",
                          style: TextStyle(color: Colors.white54, fontSize: 18, fontWeight: FontWeight.bold),
                        ),
                        Text(
                          "By Guardian",
                          style: TextStyle(color: Colors.white38, fontSize: 12),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            ),
        ],
      ),
    );
  }
}

// Legacy Dashboard Screen (Hidden in Watch Mode)
class DashboardScreen extends StatefulWidget {
  const DashboardScreen({Key? key}) : super(key: key);

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  int _selectedIndex = 0;

  final List<Widget> _screens = [
    const HomeScreen(),
    const ChildrenScreen(),
    const CameraScreen(),
    const LocationsScreen(),
    const SettingsScreen(),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: _screens[_selectedIndex],
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _selectedIndex,
        type: BottomNavigationBarType.fixed,
        items: const [
          BottomNavigationBarItem(
            icon: Icon(Icons.dashboard),
            label: 'Home',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.child_care),
            label: 'Children',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.camera_alt),
            label: 'Camera',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.location_on),
            label: 'Location',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.settings),
            label: 'Settings',
          ),
        ],
        onTap: (index) {
          setState(() => _selectedIndex = index);
        },
      ),
    );
  }
}

// Home Screen
class HomeScreen extends StatelessWidget {
  const HomeScreen({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: SingleChildScrollView(
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                'Welcome Back! 👋',
                style: TextStyle(
                  fontSize: 24,
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 20),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceAround,
                children: [
                  _StatCard('3', 'Children'),
                  _StatCard('2', 'Alerts'),
                  _StatCard('12', 'Check-ins'),
                ],
              ),
              const SizedBox(height: 24),
              const Text(
                'My Children',
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 12),
              _ChildCard(
                name: 'Ahmed Ali',
                age: 5,
                emotion: 'Happy',
                emotionEmoji: '😊',
                emotionColor: const Color(0xFFFFD93D),
              ),
              const SizedBox(height: 12),
              _ChildCard(
                name: 'Fatima Khan',
                age: 7,
                emotion: 'Surprised',
                emotionEmoji: '😲',
                emotionColor: const Color(0xFF1ABC9C),
              ),
              const SizedBox(height: 12),
              _ChildCard(
                name: 'Hassan Mustafa',
                age: 6,
                emotion: 'Neutral',
                emotionEmoji: '😐',
                emotionColor: const Color(0xFF95A5A6),
              ),
              const SizedBox(height: 24),
              const Text(
                'Recent Alerts',
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 12),
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: const Color(0xFFFFE0E0),
                  borderRadius: BorderRadius.circular(8),
                  border: Border(
                    left: BorderSide(
                      color: const Color(0xFFD0021B),
                      width: 4,
                    ),
                  ),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      '⚠️ Ahmed Ali - Angry Emotion Detected',
                      style: TextStyle(fontWeight: FontWeight.bold),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      'During school hours (Confidence: 92%)',
                      style: TextStyle(
                        fontSize: 12,
                        color: Colors.grey[600],
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 12),
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: const Color(0xFFFFE0E0),
                  borderRadius: BorderRadius.circular(8),
                  border: Border(
                    left: BorderSide(
                      color: const Color(0xFFD0021B),
                      width: 4,
                    ),
                  ),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      '💊 Medication Reminder',
                      style: TextStyle(fontWeight: FontWeight.bold),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      'Fatima Khan - Cough syrup due in 30 minutes',
                      style: TextStyle(
                        fontSize: 12,
                        color: Colors.grey[600],
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

// Stat Card Widget
class _StatCard extends StatelessWidget {
  final String number;
  final String label;

  const _StatCard(this.number, this.label);

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 8,
          ),
        ],
      ),
      child: Column(
        children: [
          Text(
            number,
            style: const TextStyle(
              fontSize: 24,
              fontWeight: FontWeight.bold,
              color: Color(0xFF4A90E2),
            ),
          ),
          const SizedBox(height: 4),
          Text(
            label,
            style: TextStyle(
              fontSize: 12,
              color: Colors.grey[600],
            ),
          ),
        ],
      ),
    );
  }
}

// Child Card Widget
class _ChildCard extends StatelessWidget {
  final String name;
  final int age;
  final String emotion;
  final String emotionEmoji;
  final Color emotionColor;

  const _ChildCard({
    required this.name,
    required this.age,
    required this.emotion,
    required this.emotionEmoji,
    required this.emotionColor,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 8,
          ),
        ],
      ),
      child: Row(
        children: [
          Container(
            width: 60,
            height: 60,
            decoration: BoxDecoration(
              color: emotionColor.withOpacity(0.2),
              borderRadius: BorderRadius.circular(30),
            ),
            child: Center(
              child: Text(
                emotionEmoji,
                style: const TextStyle(fontSize: 28),
              ),
            ),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  name,
                  style: const TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  'Age: $age years • $emotion',
                  style: TextStyle(
                    fontSize: 12,
                    color: Colors.grey[600],
                  ),
                ),
              ],
            ),
          ),
          Icon(
            Icons.arrow_forward_ios,
            color: Colors.grey[400],
            size: 16,
          ),
        ],
      ),
    );
  }
}

// Children Screen
class ChildrenScreen extends StatelessWidget {
  const ChildrenScreen({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: Scaffold(
        appBar: AppBar(
          title: const Text('My Children'),
          elevation: 0,
          backgroundColor: const Color(0xFF4A90E2),
        ),
        body: SingleChildScrollView(
          child: Padding(
            padding: const EdgeInsets.all(16.0),
            child: Column(
              children: [
                ElevatedButton.icon(
                  onPressed: () {
                    // Add child logic
                  },
                  icon: const Icon(Icons.add),
                  label: const Text('Add New Child'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFF4A90E2),
                    minimumSize: const Size(double.infinity, 50),
                  ),
                ),
                const SizedBox(height: 20),
                _ChildDetailCard(
                  name: 'Ahmed Ali',
                  age: 5,
                  gender: 'Boy',
                  braceletCode: 'AA-2024-001',
                  emotion: 'Happy',
                  emotionEmoji: '😊',
                ),
                const SizedBox(height: 12),
                _ChildDetailCard(
                  name: 'Fatima Khan',
                  age: 7,
                  gender: 'Girl',
                  braceletCode: 'FK-2024-002',
                  emotion: 'Neutral',
                  emotionEmoji: '😐',
                ),
                const SizedBox(height: 12),
                _ChildDetailCard(
                  name: 'Hassan Mustafa',
                  age: 6,
                  gender: 'Boy',
                  braceletCode: 'HM-2024-003',
                  emotion: 'Happy',
                  emotionEmoji: '😊',
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

// Child Detail Card Widget
class _ChildDetailCard extends StatelessWidget {
  final String name;
  final int age;
  final String gender;
  final String braceletCode;
  final String emotion;
  final String emotionEmoji;

  const _ChildDetailCard({
    required this.name,
    required this.age,
    required this.gender,
    required this.braceletCode,
    required this.emotion,
    required this.emotionEmoji,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 8,
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                name,
                style: const TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                ),
              ),
              Text(
                emotionEmoji,
                style: const TextStyle(fontSize: 24),
              ),
            ],
          ),
          const SizedBox(height: 12),
          _DetailRow('Age', '$age years'),
          _DetailRow('Gender', gender),
          _DetailRow('Bracelet Code', braceletCode),
          _DetailRow('Status', emotion),
          const SizedBox(height: 12),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceEvenly,
            children: [
              ElevatedButton(
                onPressed: () {},
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF4A90E2),
                ),
                child: const Text('View Details'),
              ),
              ElevatedButton(
                onPressed: () {},
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFFF5A623),
                ),
                child: const Text('Edit'),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

// Detail Row Widget
class _DetailRow extends StatelessWidget {
  final String label;
  final String value;

  const _DetailRow(this.label, this.value);

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4.0),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(
            label,
            style: TextStyle(
              color: Colors.grey[600],
              fontSize: 13,
            ),
          ),
          Text(
            value,
            style: const TextStyle(
              fontWeight: FontWeight.w500,
              fontSize: 13,
            ),
          ),
        ],
      ),
    );
  }
}

// Camera Screen
class CameraScreen extends StatefulWidget {
  const CameraScreen({Key? key}) : super(key: key);

  @override
  State<CameraScreen> createState() => _CameraScreenState();
}

class _CameraScreenState extends State<CameraScreen> {
  CameraController? _controller;
  bool _isDetecting = false;
  String _emotion = "Waiting...";
  String _emotionEmoji = "⏳";
  String _confidence = "";
  
  @override
  void initState() {
    super.initState();
    _initCamera();
  }

  Future<void> _initCamera() async {
    if (cameras.isEmpty) return;
    _controller = CameraController(cameras[0], ResolutionPreset.medium);
    try {
      await _controller!.initialize();
      if (mounted) setState(() {});
    } catch (e) {
      print('Camera Error: $e');
    }
  }

  @override
  void dispose() {
    _controller?.dispose();
    super.dispose();
  }
  
  Future<void> _captureAndDetect() async {
    if (_controller == null || !_controller!.value.isInitialized || _isDetecting) return;
    
    setState(() {
      _isDetecting = true;
      _emotion = "Detecting...";
      _emotionEmoji = "🔍";
      _confidence = "";
    });
    
    try {
      final image = await _controller!.takePicture();
      var request = http.MultipartRequest('POST', Uri.parse('http://$serverIp:5000/api/detect-emotion'));
      request.fields['source'] = 'watch-app';
      request.files.add(await http.MultipartFile.fromPath('image', image.path));
      
      var response = await request.send();
      if (response.statusCode == 200) {
        final respStr = await response.stream.bytesToString();
        final data = jsonDecode(respStr);
        if (data['success'] == true) {
            final emotionData = data['data'];
            setState(() {
              _emotion = emotionData['emotion'].toString().toUpperCase();
              _confidence = "Confidence: ${(emotionData['confidence'] as num).toStringAsFixed(1)}%";
              switch(emotionData['emotion']) {
                  case 'happy': _emotionEmoji = "😊"; break;
                  case 'sad': _emotionEmoji = "😢"; break;
                  case 'angry': _emotionEmoji = "😠"; break;
                  case 'surprise': _emotionEmoji = "😲"; break;
                  case 'fear': _emotionEmoji = "😨"; break;
                  case 'neutral': _emotionEmoji = "😐"; break;
                  case 'disgust': _emotionEmoji = "🤢"; break;
                  default: _emotionEmoji = "🤔"; break;
              }
            });
        } else {
            setState(() {
                _emotion = "No Face Found";
                _emotionEmoji = "🤷";
            });
        }
      } else {
          setState(() {
              _emotion = "Server Error";
              _emotionEmoji = "⚠️";
          });
      }
    } catch (e) {
      print("Detection error: $e");
      setState(() {
          _emotion = "Network Error";
          _emotionEmoji = "📶";
      });
    } finally {
      if (mounted) {
        setState(() {
            _isDetecting = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: Scaffold(
        appBar: AppBar(
          title: const Text('Emotion Detection'),
          elevation: 0,
          backgroundColor: const Color(0xFF4A90E2),
        ),
        body: Column(
          children: [
            Expanded(
              child: Container(
                color: Colors.black,
                child: Center(
                  child: _controller != null && _controller!.value.isInitialized
                      ? CameraPreview(_controller!)
                      : const Text('Loading Camera...', style: TextStyle(color: Colors.white)),
                ),
              ),
            ),
            Container(
              padding: const EdgeInsets.all(16),
              color: Colors.white,
              child: Column(
                children: [
                  Container(
                    padding: const EdgeInsets.all(20),
                    decoration: BoxDecoration(
                      color: const Color(0xFF4A90E2),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Column(
                      children: [
                        Text(
                          _emotionEmoji,
                          style: const TextStyle(fontSize: 48),
                        ),
                        const SizedBox(height: 8),
                        Text(
                          _emotion,
                          style: const TextStyle(
                            fontSize: 18,
                            fontWeight: FontWeight.bold,
                            color: Colors.white,
                          ),
                        ),
                        if (_confidence.isNotEmpty) ...[
                          const SizedBox(height: 4),
                          Text(
                            _confidence,
                            style: const TextStyle(
                              fontSize: 12,
                              color: Colors.white70,
                            ),
                          ),
                        ]
                      ],
                    ),
                  ),
                  const SizedBox(height: 16),
                  ElevatedButton.icon(
                    onPressed: _isDetecting ? null : _captureAndDetect,
                    icon: _isDetecting ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2)) : const Icon(Icons.camera, color: Colors.white),
                    label: Text(_isDetecting ? 'Detecting...' : 'Detect Emotion', style: const TextStyle(color: Colors.white)),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(0xFF4A90E2),
                      minimumSize: const Size(double.infinity, 50),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// Locations Screen
class LocationsScreen extends StatelessWidget {
  const LocationsScreen({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: Scaffold(
        appBar: AppBar(
          title: const Text('Locations'),
          elevation: 0,
          backgroundColor: const Color(0xFF4A90E2),
        ),
        body: SingleChildScrollView(
          child: Padding(
            padding: const EdgeInsets.all(16.0),
            child: Column(
              children: [
                Container(
                  height: 250,
                  decoration: BoxDecoration(
                    color: Colors.grey[300],
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: const [
                        Icon(
                          Icons.location_on,
                          size: 48,
                          color: Color(0xFF4A90E2),
                        ),
                        SizedBox(height: 12),
                        Text('Google Map Integration'),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 24),
                const Text(
                  'Location History',
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 12),
                _LocationCard(
                  name: 'Home',
                  address: '123 Main Street',
                  time: 'Today, 3:15 PM - 8:45 PM',
                  duration: '5h 30m',
                  icon: '🏠',
                ),
                const SizedBox(height: 12),
                _LocationCard(
                  name: 'School',
                  address: 'Ahmed Ali School',
                  time: 'Today, 8:00 AM - 2:15 PM',
                  duration: '6h 15m',
                  icon: '🏫',
                ),
                const SizedBox(height: 12),
                _LocationCard(
                  name: 'Park',
                  address: 'Central Park',
                  time: 'Yesterday, 4:30 PM - 5:45 PM',
                  duration: '1h 15m',
                  icon: '🏀',
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

// Location Card Widget
class _LocationCard extends StatelessWidget {
  final String name;
  final String address;
  final String time;
  final String duration;
  final String icon;

  const _LocationCard({
    required this.name,
    required this.address,
    required this.time,
    required this.duration,
    required this.icon,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 8,
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Text(
                icon,
                style: const TextStyle(fontSize: 24),
              ),
              const SizedBox(width: 12),
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    name,
                    style: const TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    address,
                    style: TextStyle(
                      fontSize: 13,
                      color: Colors.grey[600],
                    ),
                  ),
                ],
              ),
            ],
          ),
          const SizedBox(height: 12),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                time,
                style: TextStyle(
                  fontSize: 12,
                  color: Colors.grey[600],
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(
                  horizontal: 8,
                  vertical: 4,
                ),
                decoration: BoxDecoration(
                  color: const Color(0xFF4A90E2).withOpacity(0.1),
                  borderRadius: BorderRadius.circular(4),
                ),
                child: Text(
                  duration,
                  style: const TextStyle(
                    fontSize: 12,
                    color: Color(0xFF4A90E2),
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

// Settings Screen
class SettingsScreen extends StatefulWidget {
  const SettingsScreen({Key? key}) : super(key: key);

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  bool _notificationsEnabled = true;
  bool _locationEnabled = true;
  String _language = 'English';
  bool _isScanning = false;
  bool _isUpdating = false;
  late TextEditingController _ipController;

  @override
  void initState() {
    super.initState();
    _ipController = TextEditingController(text: serverIp);
  }

  Future<void> _toggleRemoteLogging(bool value) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool('remoteLoggingEnabled', value);
    setState(() {
      remoteLoggingEnabled = value;
    });
    remoteLog("Remote logging toggled: $value");
  }

  Future<void> _checkForUpdates() async {
    setState(() => _isUpdating = true);
    remoteLog("Checking for updates...");
    
    try {
      final response = await http.get(Uri.parse('http://$serverIp:5000/api/app-version'));
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        final serverVersion = data['version'] ?? '1.0.0';
        
        final packageInfo = await PackageInfo.fromPlatform();
        final currentVersion = packageInfo.version;
        
        // Check if server version is newer (simple string comparison for now)
        if (serverVersion != currentVersion && mounted) {
          _showUpdateDialog(serverVersion);
        } else if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('App is up to date')),
          );
        }
      }
    } catch (e) {
      remoteLog("Update check error: $e");
    } finally {
      setState(() => _isUpdating = false);
    }
  }

  void _showUpdateDialog(String version) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('New Version Available ($version)'),
        content: const Text('A newer version of Child Guard is available on the server. Download and install now?'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text('Later')),
          ElevatedButton(
            onPressed: () {
              Navigator.pop(context);
              _downloadAndInstallApk();
            }, 
            child: const Text('Update Now')
          ),
        ],
      ),
    );
  }

  Future<void> _downloadAndInstallApk() async {
    setState(() => _isUpdating = true);
    remoteLog("Downloading APK...");
    
    try {
      final response = await http.get(Uri.parse('http://$serverIp:5000/api/latest-apk'));
      if (response.statusCode == 200) {
        final directory = await getTemporaryDirectory();
        final filePath = '${directory.path}/update.apk';
        final file = File(filePath);
        await file.writeAsBytes(response.bodyBytes);
        
        remoteLog("APK downloaded to $filePath. Opening installer...");
        await OpenFilex.open(filePath);
      } else {
        remoteLog("Failed to download APK: ${response.statusCode}");
      }
    } catch (e) {
      remoteLog("Download error: $e");
    } finally {
      if (mounted) setState(() => _isUpdating = false);
    }
  }

  Future<void> _scanForServer() async {
    setState(() => _isScanning = true);
    try {
      String? foundIp = await DiscoveryService.findServer();
      
      if (foundIp != null) {
        setState(() {
          serverIp = foundIp;
          _ipController.text = foundIp;
        });
        final prefs = await SharedPreferences.getInstance();
        await prefs.setString('serverIp', foundIp);
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('Server found at $foundIp')),
          );
        }
      } else {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('No server found. Make sure it is running.')),
          );
        }
      }
    } catch (e) {
      debugPrint("Scan error: $e");
    } finally {
      if (mounted) {
        setState(() => _isScanning = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: Scaffold(
        appBar: AppBar(
          title: const Text('Settings'),
          elevation: 0,
          backgroundColor: const Color(0xFF4A90E2),
        ),
        body: SingleChildScrollView(
          child: Column(
            children: [
              const SizedBox(height: 20),
              Container(
                margin: const EdgeInsets.symmetric(horizontal: 16),
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(12),
                  boxShadow: [
                    BoxShadow(
                      color: Colors.black.withOpacity(0.05),
                      blurRadius: 8,
                    ),
                  ],
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Account',
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 16),
                    _SettingRow('Email', 'parent@email.com'),
                    const Divider(),
                    _SettingRow('Phone', '+1 (555) 000-0000'),
                    const Divider(),
                    _SettingRow('Username', 'john_parent'),
                  ],
                ),
              ),
              const SizedBox(height: 16),
              Container(
                margin: const EdgeInsets.symmetric(horizontal: 16),
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(12),
                  boxShadow: [
                    BoxShadow(
                      color: Colors.black.withOpacity(0.05),
                      blurRadius: 8,
                    ),
                  ],
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Network Configuration',
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 16),
                    TextField(
                      decoration: const InputDecoration(
                        labelText: 'Server IP Address',
                        border: OutlineInputBorder(),
                        hintText: 'e.g. 192.168.1.100'
                      ),
                      controller: _ipController,
                      onSubmitted: (value) async {
                        final prefs = await SharedPreferences.getInstance();
                        await prefs.setString('serverIp', value);
                        serverIp = value;
                        if (mounted) {
                          ScaffoldMessenger.of(context).showSnackBar(
                            const SnackBar(content: Text('Server IP updated')),
                          );
                        }
                      },
                    ),
                    const SizedBox(height: 12),
                    SizedBox(
                      width: double.infinity,
                      child: ElevatedButton.icon(
                        onPressed: _isScanning ? null : _scanForServer,
                        icon: _isScanning 
                          ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2)) 
                          : const Icon(Icons.search),
                        label: Text(_isScanning ? 'Scanning...' : 'Scan for Server'),
                        style: ElevatedButton.styleFrom(
                          backgroundColor: const Color(0xFF4A90E2),
                          foregroundColor: Colors.white,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 16),
              Container(
                margin: const EdgeInsets.symmetric(horizontal: 16),
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(12),
                  boxShadow: [
                    BoxShadow(
                      color: Colors.black.withOpacity(0.05),
                      blurRadius: 8,
                    ),
                  ],
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Watch Identity',
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 12),
                    FutureBuilder<String>(
                      future: () async {
                        final deviceInfo = DeviceInfoPlugin();
                        if (Platform.isAndroid) {
                          final androidInfo = await deviceInfo.androidInfo;
                          return androidInfo.id;
                        }
                        return 'Unknown';
                      }(),
                      builder: (context, snapshot) {
                        return Text(
                          'Hardware ID: ${snapshot.data ?? "..."}',
                          style: const TextStyle(fontSize: 12, color: Colors.blueGrey),
                        );
                      }
                    ),
                    const SizedBox(height: 12),
                    TextField(
                      decoration: const InputDecoration(
                        labelText: 'Bracelet Code (Custom)',
                        border: OutlineInputBorder(),
                        hintText: 'e.g. BR-001',
                        helperText: 'Override with dashboard code if needed',
                      ),
                      controller: TextEditingController(text: braceletCode),
                      onChanged: (value) async {
                        braceletCode = value;
                        final prefs = await SharedPreferences.getInstance();
                        await prefs.setString('braceletCode', value);
                      },
                    ),
                    const SizedBox(height: 16),
                    const Divider(),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        const Text('Remote Logging'),
                        Switch(
                          value: remoteLoggingEnabled,
                          onChanged: _toggleRemoteLogging,
                          activeColor: const Color(0xFFF5A623),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 16),
              Container(
                margin: const EdgeInsets.symmetric(horizontal: 16),
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(12),
                  boxShadow: [
                    BoxShadow(
                      color: Colors.black.withOpacity(0.05),
                      blurRadius: 8,
                    ),
                  ],
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'App Updates',
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 16),
                    const Divider(),
                    const SizedBox(height: 8),
                    FutureBuilder<PackageInfo>(
                      future: PackageInfo.fromPlatform(),
                      builder: (context, snapshot) {
                        if (snapshot.hasData) {
                          return Center(
                            child: Text(
                              'Version: ${snapshot.data!.version}+${snapshot.data!.buildNumber}',
                              style: const TextStyle(color: Colors.grey, fontSize: 12),
                            ),
                          );
                        }
                        return const SizedBox.shrink();
                      },
                    ),
                    const SizedBox(height: 12),
                    SizedBox(
                      width: double.infinity,
                      child: ElevatedButton.icon(
                        onPressed: _isUpdating ? null : _checkForUpdates,
                        icon: _isUpdating 
                          ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white)) 
                          : const Icon(Icons.system_update),
                        label: Text(_isUpdating ? 'Checking...' : 'Check for Updates'),
                        style: ElevatedButton.styleFrom(
                          backgroundColor: const Color(0xFF1ABC9C),
                          foregroundColor: Colors.white,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 16),
              Container(
                margin: const EdgeInsets.symmetric(horizontal: 16),
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(12),
                  boxShadow: [
                    BoxShadow(
                      color: Colors.black.withOpacity(0.05),
                      blurRadius: 8,
                    ),
                  ],
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Preferences',
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 16),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        const Text('Notifications'),
                        Switch(
                          value: _notificationsEnabled,
                          onChanged: (value) {
                            setState(() => _notificationsEnabled = value);
                          },
                          activeColor: const Color(0xFF4A90E2),
                        ),
                      ],
                    ),
                    const Divider(),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        const Text('Location Tracking'),
                        Switch(
                          value: _locationEnabled,
                          onChanged: (value) {
                            setState(() => _locationEnabled = value);
                          },
                          activeColor: const Color(0xFF4A90E2),
                        ),
                      ],
                    ),
                    const Divider(),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        const Text('Language'),
                        DropdownButton<String>(
                          value: _language,
                          onChanged: (newValue) {
                            setState(() => _language = newValue!);
                          },
                          items: <String>['English', 'Arabic']
                              .map<DropdownMenuItem<String>>(
                                (String value) =>
                                    DropdownMenuItem<String>(
                                      value: value,
                                      child: Text(value),
                                    ),
                              )
                              .toList(),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 16),
              Container(
                margin: const EdgeInsets.symmetric(horizontal: 16),
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(12),
                  boxShadow: [
                    BoxShadow(
                      color: Colors.black.withOpacity(0.05),
                      blurRadius: 8,
                    ),
                  ],
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Security',
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 16),
                    SizedBox(
                      width: double.infinity,
                      child: ElevatedButton(
                        onPressed: () {},
                        style: ElevatedButton.styleFrom(
                          backgroundColor: const Color(0xFFF5A623),
                        ),
                        child: const Text('Change Password'),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 16),
              Container(
                margin: const EdgeInsets.symmetric(horizontal: 16),
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(12),
                  boxShadow: [
                    BoxShadow(
                      color: Colors.black.withOpacity(0.05),
                      blurRadius: 8,
                    ),
                  ],
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Danger Zone',
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                        color: Color(0xFFD0021B),
                      ),
                    ),
                    const SizedBox(height: 16),
                    SizedBox(
                      width: double.infinity,
                      child: ElevatedButton(
                        onPressed: () {
                          Navigator.of(context).pushReplacement(
                            MaterialPageRoute(
                              builder: (context) => const LoginScreen(),
                            ),
                          );
                        },
                        style: ElevatedButton.styleFrom(
                          backgroundColor: const Color(0xFFD0021B),
                        ),
                        child: const Text('Logout'),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 30),
            ],
          ),
        ),
      ),
    );
  }
}

// Setting Row Widget
class _SettingRow extends StatelessWidget {
  final String label;
  final String value;

  const _SettingRow(this.label, this.value);

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8.0),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(
            label,
            style: const TextStyle(fontWeight: FontWeight.w500),
          ),
          Text(
            value,
            style: TextStyle(
              color: Colors.grey[600],
              fontSize: 13,
            ),
          ),
        ],
      ),
    );
  }
}
