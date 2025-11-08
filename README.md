# Minibot Driver Station

A GUI-based driver station for controlling ESP32-based minibots using PS5 controllers via pygame.

## Features

- **Automatic Robot Discovery**: Automatically discovers robots on the network via UDP broadcast
- **Dual Robot Support**: Control up to 2 robots simultaneously
- **PS5 Controller Integration**: Pair PS5 controllers with robots using pygame
- **Game Status Management**: Switch between Standby, Teleop, and Autonomous modes
- **Emergency Stop**: Quick emergency stop for all robots
- **Visual Feedback**: Real-time display of robot connections and controller states

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. **Connect Robots**: Ensure your ESP32 robots are running the minibot code and connected to the WiFi network "WATCHTOWER"

2. **Connect Controllers**: Connect your PS5 controllers to your computer via USB or Bluetooth

3. **Start Driver Station**:
```bash
python3 driver_station.py
```

4. **Pair Controllers to Robots**:
   - Click on a robot box (left side)
   - Click on a controller box (right side)
   - Click the "PAIR" button
   - The robot will now respond to the paired controller's inputs

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

## Robot Code

The robot code is located in the `minibots/` directory and runs on ESP32 microcontrollers. The driver station is designed to be fully compatible with the existing robot code without modifications.

### Robot Configuration
In `minibots/minibots.ino`, set your robot ID:
```cpp
Minibot bot("YOUR NAME HERE");
```

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

## Technical Details

- **Language**: Python 3.x
- **GUI Framework**: pygame
- **Protocol**: UDP broadcast and unicast
- **Network Ports**: 
  - Discovery: 12345
  - Command: 12346+ (assigned per robot)
- **Update Rate**: 60 Hz
- **Packet Format**: Binary (controller data) and text (status/control)
