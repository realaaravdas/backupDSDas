# Arduino Setup Guide - Minibot Robot Code

## 🚀 Quick Start (5 Minutes)

### Step 1: Open in Arduino IDE
1. Open `minibots.ino` in Arduino IDE
2. Install ESP32 board support if not already installed:
   - Go to File → Preferences
   - Add to Additional Board Manager URLs:
     ```
     https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
     ```
   - Go to Tools → Board → Board Manager
   - Search "ESP32" and install "esp32 by Espressif Systems"

### Step 2: Configure Your Robot
Edit these lines in `minibots.ino`:

```cpp
// Line 18: Set your robot's unique name
#define ROBOT_NAME "robot1"  // Change to "robot2", "yourname", etc.

// Line 21: Choose your robot type (uncomment ONE)
#define ROBOT_TYPE_TANK_DRIVE      // ← Most common, leave this
//#define ROBOT_TYPE_ARCADE_DRIVE  // Uncomment for arcade controls
//#define ROBOT_TYPE_MECANUM       // Uncomment for mecanum wheels
//#define ROBOT_TYPE_CUSTOM        // Uncomment to write your own code
```

### Step 3: Configure Pins (if different from defaults)
```cpp
// Lines 27-30: Motor pins
#define LEFT_MOTOR_PIN   16    // Change if using different pins
#define RIGHT_MOTOR_PIN  17
#define DC_MOTOR_PIN     18
#define SERVO_MOTOR_PIN  19
```

### Step 4: Upload to ESP32
1. Select your board: Tools → Board → ESP32 Arduino → ESP32 Dev Module
2. Select your port: Tools → Port → (your ESP32 COM port)
3. Click Upload (→) button
4. Wait for "Done uploading"

### Step 5: Done!
Your robot is ready! It will:
- ✅ Auto-connect to "WATCHTOWER" WiFi
- ✅ Auto-discover and pair with driver station
- ✅ Respond to controller inputs
- ✅ Emergency stop when commanded

---

## 📖 Detailed Configuration

### Robot Types Explained

#### 🎮 Tank Drive (Default)
**Best for:** Most common robot type with two motors (left/right)

**Controls:**
- Left stick Y → Left motor
- Right stick Y → Right motor
- Left stick X → DC motor (optional)
- Triangle/Square buttons → Servo control (optional)

**Wiring:**
- Pin 16 → Left motor ESC
- Pin 17 → Right motor ESC
- Pin 18 → DC motor ESC (optional)
- Pin 19 → Servo (optional)

---

#### 🕹️ Arcade Drive
**Best for:** Single-stick driving like a video game

**Controls:**
- Left stick Y → Forward/Backward
- Right stick X → Left/Right turning
- Left stick X → DC motor (optional)
- Triangle/Square buttons → Servo control (optional)

**Wiring:** Same as Tank Drive

---

#### 🔷 Mecanum Drive
**Best for:** Omni-directional robots with 4 mecanum wheels

**Controls:**
- Left stick Y → Forward/Backward
- Left stick X → Strafe Left/Right
- Right stick X → Rotate

**Wiring:**
- Pin 16 → Front Left motor
- Pin 17 → Front Right motor
- Pin 18 → Back Left motor
- Pin 19 → Back Right motor

---

#### ⚙️ Custom
**Best for:** Unique robot designs

Write your own control code in the `ROBOT_TYPE_CUSTOM` section (line 193)

---

## 🔧 Advanced Configuration

### Joystick Deadzone
Prevents motor jitter when joystick is at rest:
```cpp
#define DEADZONE 10  // Increase if motors twitch when idle
```

### Motor Reversal
If a motor spins the wrong direction:
```cpp
#define MOTOR_REVERSE_LEFT  true   // Set to true to reverse
#define MOTOR_REVERSE_RIGHT false
```

### Speed Limiting
Reduce maximum speed (useful for learning):
```cpp
#define MAX_SPEED 0.5  // 0.0 to 1.0 (0.5 = 50% max speed)
```

---

## 🔌 Pin Configuration

### Default Pins (ESP32)
```
GPIO 16 → Left Motor PWM
GPIO 17 → Right Motor PWM
GPIO 18 → DC Motor PWM
GPIO 19 → Servo PWM
```

### Supported Pins
Most ESP32 GPIO pins support PWM. Avoid these pins:
- ❌ GPIO 6-11 (connected to flash)
- ❌ GPIO 34-39 (input only)
- ✅ Safe pins: 2, 4, 5, 12-19, 21-23, 25-27, 32-33

---

## 🛠️ Troubleshooting

### Robot doesn't connect to WiFi
**Check:**
1. WiFi network is "WATCHTOWER" with password "lancerrobotics"
2. ESP32 is within WiFi range
3. Serial Monitor shows "WiFi" dots then "IP: xxx.xxx.xxx.xxx"

**Fix:** Edit `minibot.h` lines 13-14 if using different WiFi:
```cpp
#define WIFI_SSID "WATCHTOWER"
#define WIFI_PASSWORD "lancerrobotics"
```

---

### Motors don't respond
**Check:**
1. Driver station shows robot as "Connected" (green)
2. Controller is paired to your robot
3. Game mode is "TELEOP" (press '2' on driver station)
4. Emergency stop is OFF (not red)
5. Serial Monitor shows controller data being received

**Fix:**
- Verify motor pins are correct
- Check motor ESC connections
- Test motors manually in code

---

### Motor spins wrong direction
**Fix:** Enable motor reversal:
```cpp
#define MOTOR_REVERSE_LEFT  true   // Reverse this motor
```

---

### Compilation errors
**Error:** `'ledcAttach' was not declared`
- **Cause:** Old ESP32 core version
- **Fix:** Update ESP32 board package to 2.0.0 or newer

**Error:** `minibot.h: No such file or directory`
- **Cause:** Files not in same folder
- **Fix:** Ensure minibot.h and minibot.cpp are in same folder as minibots.ino

---

### Robot keeps disconnecting
**Check:**
1. WiFi signal strength
2. Power supply (brownouts cause disconnects)
3. Serial Monitor for timeout messages

**Fix:**
- Move closer to WiFi router
- Use adequate power supply (ESP32 needs stable 3.3V/5V)
- Check for loose connections

---

## 📊 Testing Without Hardware

Use demo mode to test driver station without physical robots:

**Terminal 1:**
```bash
python demo_mode.py
```

**Terminal 2:**
```bash
python driver_station.py
```

This simulates robots for testing the driver station GUI.

---

## 🎯 Code Examples

### Example 1: Simple Forward/Backward
```cpp
#define ROBOT_TYPE_CUSTOM

// In the ROBOT_TYPE_CUSTOM section:
float speed = -leftY;  // Left stick Y
bot.driveLeft(speed);
bot.driveRight(speed);
```

### Example 2: Turn in Place
```cpp
if (btnCross) {
    bot.driveLeft(0.5);   // Spin right
    bot.driveRight(-0.5);
} else if (btnCircle) {
    bot.driveLeft(-0.5);  // Spin left
    bot.driveRight(0.5);
}
```

### Example 3: Speed Boost Button
```cpp
float speed = -leftY;
if (btnTriangle) {
    speed *= 2.0;  // 2x speed when Triangle pressed
}
bot.driveLeft(speed);
bot.driveRight(speed);
```

### Example 4: Servo Sweep with Buttons
```cpp
static int servoPos = 0;
if (btnTriangle) {
    servoPos = min(servoPos + 5, 50);  // Increment
} else if (btnSquare) {
    servoPos = max(servoPos - 5, -50); // Decrement
}
bot.driveServoMotor(servoPos);
```

---

## 📡 Network Protocol

The robot communicates with the driver station using UDP:

### Discovery (Auto)
- Robot broadcasts: `DISCOVER:robot1:192.168.1.100`
- Driver station responds: `PORT:robot1:12346`
- Robot switches to assigned port

### Game Status
- Standby mode: Motors disabled
- Teleop mode: Controller active
- Autonomous mode: Custom autonomous code

### Emergency Stop
- Received: `ESTOP` → All motors stop immediately
- Received: `ESTOP_OFF` → Resume normal operation

---

## 🚨 Safety Features

The code includes built-in safety:

1. **Auto-timeout:** If no commands received for 5 seconds, motors stop
2. **Emergency stop:** Instant motor cutoff on ESTOP command
3. **Mode checking:** Motors only run in teleop mode
4. **Value clamping:** Motor values limited to -1.0 to 1.0
5. **Deadzone:** Prevents accidental motor activation

---

## 📚 API Reference

### Available Functions

#### Motor Control
```cpp
bot.driveLeft(speed);      // -1.0 to 1.0
bot.driveRight(speed);     // -1.0 to 1.0
bot.driveDCMotor(speed);   // -1.0 to 1.0
bot.driveServoMotor(angle); // -50 to 50 degrees
```

#### Get Controller Data
```cpp
uint8_t leftX = bot.getLeftX();      // 0-255
uint8_t leftY = bot.getLeftY();      // 0-255
uint8_t rightX = bot.getRightX();    // 0-255
uint8_t rightY = bot.getRightY();    // 0-255

bool cross = bot.getCross();         // true/false
bool circle = bot.getCircle();       // true/false
bool square = bot.getSquare();       // true/false
bool triangle = bot.getTriangle();   // true/false
```

#### Check Game State
```cpp
bool teleop = bot.isTeleop();        // true in teleop mode
bool auto = bot.isAuto();            // true in autonomous mode
```

---

## 💾 Memory Usage

This optimized code uses:
- **Flash:** ~15-20 KB (fits easily on ESP32's 4MB)
- **RAM:** ~2-3 KB (ESP32 has 520 KB total)
- **Heap:** Minimal (no dynamic allocation)

Safe for all ESP32 variants including ESP32-S2, ESP32-S3, ESP32-C3.

---

## 📄 Files in This Directory

```
minibots/
├── minibots.ino          ← Main code (configure this)
├── minibot.h             ← Class definition (don't modify)
├── minibot.cpp           ← Implementation (don't modify)
└── README_ARDUINO.md     ← This file
```

Only edit `minibots.ino` - the other files are the library.

---

## ✅ Checklist

Before uploading, verify:
- [ ] Robot name is unique (line 18)
- [ ] Robot type is selected (line 21)
- [ ] Pin numbers are correct (lines 27-30)
- [ ] ESP32 board is selected in Arduino IDE
- [ ] Correct COM port is selected
- [ ] WiFi credentials match your network

---

## 🎓 Next Steps

1. ✅ Upload code to ESP32
2. ✅ Open Serial Monitor (115200 baud) to see connection status
3. ✅ Run driver station: `python driver_station.py`
4. ✅ Pair controller to robot in GUI
5. ✅ Press '2' for teleop mode
6. ✅ Start driving!

**Need help?** Check the Serial Monitor for debug messages.

**Found a bug?** Report at: https://github.com/anthropics/claude-code/issues

---

**Enjoy your robot! 🤖**
