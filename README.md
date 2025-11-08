# Minibot Driver Station

A complete, production-ready system for controlling ESP32-based robots with PS5 controllers via a Python GUI.

## ⚡ Quick Start

### For Robot (ESP32):
1. Open `minibots/minibots.ino` in Arduino IDE
2. Change `ROBOT_NAME` to your robot's name (line 18)
3. Upload to ESP32
4. Done! Robot auto-connects

**See [ARDUINO_READY.md](ARDUINO_READY.md) for complete Arduino setup guide.**

### For Driver Station (PC):
```bash
pip install -r requirements.txt
python driver_station.py
```

Click orange "Refresh" button to discover robots, pair controllers, and drive!

## ✨ Features

- **Plug-and-Play Robot Code**: 4 robot types (Tank, Arcade, Mecanum, Custom)
- **Automatic Robot Discovery**: Robots auto-connect via UDP broadcast
- **Dual Robot Support**: Control up to 2 robots simultaneously
- **PS5 Controller Integration**: Full joystick and button support
- **Game Status Management**: Standby, Teleop, and Autonomous modes
- **Emergency Stop**: Instant safety cutoff for all robots
- **Visual Feedback**: Real-time connection status and controller display
- **Refresh Button**: One-click robot rediscovery

## 📦 Installation

### Robot Setup (ESP32)
1. Open `minibots/minibots.ino` in Arduino IDE
2. Install ESP32 board support (if needed)
3. Configure robot:
   ```cpp
   #define ROBOT_NAME "robot1"        // Change this!
   #define ROBOT_TYPE_TANK_DRIVE      // Choose your type
   ```
4. Select Board: ESP32 Dev Module
5. Upload to ESP32

**Complete guide:** [minibots/README_ARDUINO.md](minibots/README_ARDUINO.md)
**Examples:** [minibots/EXAMPLES.md](minibots/EXAMPLES.md)

### Driver Station Setup (PC)
1. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run driver station:
   ```bash
   python driver_station.py
   ```

## 🎮 Usage

### Getting Started
1. **Power on robot** - It will auto-connect to "WATCHTOWER" WiFi
2. **Connect PS5 controllers** to your computer (USB or Bluetooth)
3. **Start driver station**: `python driver_station.py`
4. **Wait for discovery** - Robot appears automatically (or click "Refresh")
5. **Pair controller**:
   - Click robot box (left side)
   - Click controller box (right side)
   - Click "PAIR" button
6. **Start driving**:
   - Press `2` for Teleop mode
   - Use controller joysticks to drive!

### ⚠️ Important: Demo Mode on Windows
**Note:** If robots don't appear when testing demo mode on Windows, this is expected! Windows blocks UDP localhost loopback on the same port. **Real ESP32 robots WILL work correctly** because they're on different machines. See [ROBOT_DISCOVERY_FIX.md](ROBOT_DISCOVERY_FIX.md) for details.

## Controls

### Keyboard Controls
- `1` - Set all robots to **Standby** mode
- `2` - Set all robots to **Teleop** mode (controllers active)
- `3` - Set all robots to **Autonomous** mode
- `SPACE` - Toggle **Emergency Stop** (stops all robots immediately)
- `ESC` - Quit the application

### PS5 Controller
- **Left Joystick**: Left X/Y axis (leftX, leftY)
- **Right Joystick**: Right X/Y axis (rightX, rightY)
- **Cross (X)**: Cross button
- **Circle (O)**: Circle button
- **Square (□)**: Square button
- **Triangle (△)**: Triangle button

## Network Protocol

The driver station communicates with robots using UDP packets:

### Discovery
- Robots broadcast: `DISCOVER:<robotId>:<IP>` on port 12345
- Driver station responds: `PORT:<robotId>:<port>`

### Game Status
- Format: `<robotId>:<status>` (e.g., "robot1:teleop")
- Status values: "standby", "teleop", "autonomous"

### Controller Data (Binary, 24 bytes)
- Bytes 0-15: Robot name (null-terminated string)
- Bytes 16-21: Axes (leftX, leftY, rightX, rightY, unused, unused)
- Bytes 22-23: Button states (bitfield)

### Emergency Stop
- Enable: `ESTOP`
- Disable: `ESTOP_OFF`

## 🤖 Robot Code

The robot code in `minibots/` is **production-ready** and **plug-and-play** for ESP32 microcontrollers.

### Built-in Robot Types
Choose from 4 pre-configured robot types:

1. **Tank Drive** - Independent left/right motor control (most common)
2. **Arcade Drive** - Video game style: one stick for forward/turn
3. **Mecanum Drive** - Omni-directional 4-wheel drive
4. **Custom** - Write your own control logic

### Configuration (3 steps)
```cpp
// Step 1: Set unique robot name
#define ROBOT_NAME "robot1"

// Step 2: Choose robot type (uncomment ONE)
#define ROBOT_TYPE_TANK_DRIVE

// Step 3: Configure pins (if needed)
#define LEFT_MOTOR_PIN   16
#define RIGHT_MOTOR_PIN  17
```

### Features
- ✅ Automatic WiFi connection
- ✅ Auto-discovery protocol
- ✅ Safety timeout (5 seconds)
- ✅ Emergency stop support
- ✅ Joystick deadzone
- ✅ Motor reversal options
- ✅ Speed limiting
- ✅ Memory optimized (15-20 KB flash)

**See [minibots/README_ARDUINO.md](minibots/README_ARDUINO.md) for complete documentation.**

## Troubleshooting

### Robots not discovered
- Verify WiFi network name is "WATCHTOWER" with password "lancerrobotics"
- Check that robots and driver station are on the same network
- Ensure firewall allows UDP traffic on port 12345

### Controllers not detected
- Verify controllers are connected and recognized by the system
- Try disconnecting and reconnecting the controllers
- Restart the driver station application

### Controller input not working
- Ensure game status is set to "Teleop" mode (press `2`)
- Verify emergency stop is not active (press `SPACE` to toggle)
- Check that the controller is paired with the robot

## 📚 Documentation

- **[ARDUINO_READY.md](ARDUINO_READY.md)** - Complete Arduino quick start guide
- **[minibots/README_ARDUINO.md](minibots/README_ARDUINO.md)** - Detailed robot setup and API reference
- **[minibots/EXAMPLES.md](minibots/EXAMPLES.md)** - 10+ ready-to-use robot configurations
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System architecture and design
- **[QUICKSTART.md](QUICKSTART.md)** - Quick start guide
- **[CHANGES.md](CHANGES.md)** - Recent updates and optimizations
- **[SECURITY.md](SECURITY.md)** - Security considerations

## 🔧 Technical Details

### Driver Station
- **Language**: Python 3.x
- **GUI Framework**: pygame
- **Protocol**: UDP broadcast and unicast
- **Network Ports**:
  - Discovery: 12345
  - Command: 12346+ (assigned per robot)
- **Update Rate**: 60 Hz
- **Packet Format**: Binary (controller data) and text (status/control)

### Robot (ESP32)
- **Platform**: ESP32 Arduino (all variants supported)
- **Memory**: 15-20 KB flash, 2-3 KB RAM
- **WiFi**: 2.4 GHz 802.11 b/g/n
- **PWM**: 100 Hz, 16-bit resolution
- **Protocol**: UDP unicast/broadcast
- **Safety**: 5-second timeout, emergency stop
