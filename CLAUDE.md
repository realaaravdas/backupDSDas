# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a GUI-based driver station for controlling ESP32-based minibots with PS5 controllers. The system consists of:
- **Python driver station** (`driver_station.py`) - GUI application using pygame for robot control
- **ESP32 robot code** (`minibots/`) - Arduino code running on robots (DO NOT MODIFY)
- **UDP-based protocol** - Custom binary protocol for discovery and control

## Recent Updates (2025)

The robot code has been **optimized and revamped** for ESP32 compatibility and reduced memory footprint:
- Replaced String objects with char arrays for lower memory usage
- Changed to inline getters for better performance
- Simplified PWM setup using `ledcAttach()` (newer ESP32 API)
- Reduced code size to fit comfortably in ESP32 flash
- Added working tank drive example in minibots.ino

The driver station now includes a **Refresh button** (orange button next to "Robots:" label) to clear and rediscover robots.

## Common Commands

### Running the Application
```bash
# Install dependencies
pip install -r requirements.txt

# Run driver station (connects to real robots)
python3 driver_station.py

# Run demo mode (simulated robots for testing)
python3 demo_mode.py
```

### Testing
```bash
# Run protocol compatibility tests
python3 test_protocol.py

# Run network diagnostics
python3 test_connection.py
```

### Development Workflow
When testing without hardware:
1. Terminal 1: `python3 demo_mode.py` (starts simulated robots)
2. Terminal 2: `python3 driver_station.py` (starts GUI)

## Protocol Architecture

The system uses a UDP-based protocol with three communication phases:

### 1. Discovery Phase (Port 12345)
- Robots broadcast: `DISCOVER:<robotId>:<IP>` every 2 seconds
- Driver station responds: `PORT:<robotId>:<port>` (assigns unique port 12346+)
- Robot switches to assigned port

### 2. Game Status Updates
Text format sent to robot's assigned port:
```
<robotId>:<status>
```
Status values: `standby`, `teleop`, `autonomous`

### 3. Controller Data (Binary - 24 bytes)
Binary packet format sent at 60 Hz:
- Bytes 0-15: Robot name (null-terminated string)
- Bytes 16-21: Axes (leftX, leftY, rightX, rightY, unused, unused) - values 0-255
- Bytes 22-23: Button states (bitfield: cross=bit 0, circle=bit 1, square=bit 2, triangle=bit 3)

Controller axes are mapped from pygame's -1.0 to +1.0 range → 0-255 byte range:
```python
byte_value = int((joystick_value + 1.0) * 127.5)
```

### 4. Emergency Stop
Broadcast to all robots:
- Enable: `ESTOP`
- Disable: `ESTOP_OFF`

### Timeout Behavior
- **Robot timeout**: 5 seconds without commands → robot disconnects and returns to discovery
- **Driver station timeout**: 10 seconds without discovery → removes robot from list

## Code Architecture

### Main Application (`driver_station.py`)
- **DriverStation class**: Main application logic
  - Network thread: Listens for robot discovery packets
  - Main loop: Handles GUI rendering and controller input at 60 FPS
  - Controller pairing: User clicks robot → controller → PAIR button
  - Game modes: Keyboard controls (1=standby, 2=teleop, 3=autonomous, SPACE=estop)

### Key Data Structures
- `RobotInfo`: Tracks discovered robots (id, IP, port, last_seen, connected status)
- `ControllerState`: Tracks PS5 controller state (axes, buttons, pygame joystick handle)
- `robot_controller_pairs`: Dict mapping robot_id → controller_index

### Threading Model
- **Main thread**: pygame event loop, rendering, controller reading (60 Hz)
- **Network thread**: UDP socket listener for robot discovery (non-blocking with 0.1s timeout)

### Packet Construction
Controller data packets are built using `struct.pack`:
```python
packet = struct.pack(
    "16s6BB",  # 16 char string + 6 bytes + 2 bytes
    robot_name_bytes,
    left_x, left_y, right_x, right_y, 0, 0,  # axes + unused
    buttons & 0xFF, (buttons >> 8) & 0xFF    # button bitfield
)
```

## Network Configuration

The system is designed for the "WATCHTOWER" WiFi network:
- **SSID**: WATCHTOWER
- **Password**: lancerrobotics
- **Discovery port**: 12345 (UDP broadcast)
- **Command ports**: 12346+ (UDP unicast, one per robot)
- **Update rate**: 60 Hz (controller data)

**Security Note**: This is a trusted local network. No authentication or encryption is used by design. Binding to all interfaces (`bind(('', PORT))`) is intentional for UDP broadcast reception.

## Extending the System

### Adding Support for More Robots
Current limit is 2 robots. To expand:
1. Increase UI layout in `_draw_robots()` and `_draw_controllers()`
2. Modify `range(2)` loops to support more slots
3. No protocol changes needed - port assignment is dynamic

### Adding Controller Types
Currently supports PS5 controllers via pygame. To add more:
1. Update `_discover_controllers()` to detect new controller types
2. Map axes/buttons in `_read_controller()` to match protocol expectations
3. Update UI labels in `_draw_controllers()`

## Troubleshooting

### Common Issues

**Robots not discovered:**
- Verify WiFi network is "WATCHTOWER"
- Check firewall allows UDP port 12345
- Ensure robots and driver station on same network
- Run `test_connection.py` for diagnostics

**Controllers not detected:**
- Ensure pygame can see the controllers (`pygame.joystick.get_count()`)
- Try USB connection instead of Bluetooth
- Restart driver station after connecting controllers

**Controller input not working:**
- Must be in Teleop mode (press `2`)
- Emergency stop must be OFF (SPACE to toggle)
- Controller must be paired to robot (click robot → controller → PAIR)

## File Structure

```
backupDSDas/
├── driver_station.py      # Main GUI application (490 lines)
├── demo_mode.py          # Simulated robots for testing (122 lines)
├── test_protocol.py      # Protocol validation tests (151 lines)
├── test_connection.py    # Network diagnostics (153 lines)
├── requirements.txt      # Python dependencies (pygame>=2.5.0)
├── ARCHITECTURE.md       # Detailed system architecture
├── SECURITY.md           # Security analysis
├── QUICKSTART.md         # Quick start guide
├── README.md            # User documentation
└── minibots/            # ESP32 Arduino code (DO NOT MODIFY)
    ├── minibot.h        # Protocol definitions
    ├── minibot.cpp      # Robot logic
    └── minibots.ino     # Arduino sketch
```

## Development Guidelines

### Protocol Compatibility
When modifying driver station code:
1. Always verify against `test_protocol.py` tests
2. Test with `demo_mode.py` before testing with real hardware
3. Check packet format matches `minibot.cpp` expectations
4. Never change the binary packet structure (24 bytes fixed)

### Performance Requirements
- Controller data must be sent at 60 Hz minimum
- Discovery packets should be handled without blocking main loop
- UI must render at 60 FPS for smooth operation

### Error Handling
- Network errors should not crash the application
- Invalid packets should be silently dropped
- Robot disconnections should be handled gracefully (auto-cleanup)
- Controller disconnections should stop sending data to paired robot

## pygame Specifics

### Controller Axis Mapping
PS5 controller axes (typical pygame indices):
- Axis 0: Left stick X (leftX)
- Axis 1: Left stick Y (leftY)
- Axis 2: Right stick X (rightX)
- Axis 3: Right stick Y (rightY)

**Note**: Axis indices may vary by system. Verify with `joystick.get_axis()` testing.

### Button Mapping
PS5 buttons (typical pygame indices):
- Button 0: Cross/X
- Button 1: Circle/O
- Button 2: Square
- Button 3: Triangle

**Note**: Button indices may vary by system/driver. Current implementation uses hardcoded indices 0-3.

## ESP32 Code Optimization Details

The robot code has been optimized to minimize memory usage:

### Memory Optimizations
- **String → char arrays**: Replaced Arduino String with char buffers (saves ~1-2KB heap per string)
- **uint32_t/uint16_t/uint8_t**: Used exact-size types instead of int (saves RAM)
- **Inline functions**: Getters are now inline (reduces code size)
- **Bitfield buttons**: All button states in single byte (was 4 bools)
- **Game status enum**: Status stored as uint8_t (0=standby, 1=teleop, 2=auto)

### PWM Configuration
Uses modern ESP32 API:
```cpp
ledcAttach(pin, PWM_FREQ, PWM_RES);  // Attach channel to pin
ledcWrite(pin, dutyCycle);           // Write PWM value
```
- Frequency: 100 Hz
- Resolution: 16-bit (0-65535)
- Neutral position: 9830 (1.5ms pulse)

### Motor Value Mapping
Controller bytes (0-255) need conversion to motor speed (-1.0 to 1.0):
```cpp
float speed = (value - 127) / 127.0;
```

Servo angles work differently (-50 to 50 degrees):
```cpp
int servoAngle = (value - 127) * 50 / 127;
```

## Known Limitations

1. **No authentication**: Anyone on the network can control robots
2. **No encryption**: All data sent in plaintext
3. **UDP unreliability**: No packet delivery guarantee (acceptable for 60 Hz updates)
4. **Fixed packet size**: 24-byte limit restricts future expansion
5. **Broadcast only discovery**: Requires single broadcast domain
6. **No robot feedback**: One-way communication (driver → robot only)

## References

- Protocol specification: See `minibots/minibot.h` and `ARCHITECTURE.md`
- User guide: See `README.md` and `QUICKSTART.md`
- Security considerations: See `SECURITY.md`
