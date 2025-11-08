# Quick Start Guide

## For Testing Without Hardware (Demo Mode)

1. **Install dependencies**:
```bash
pip install -r requirements.txt
```

2. **Start simulated robots** (in one terminal):
```bash
python3 demo_mode.py
```

3. **Start driver station** (in another terminal):
```bash
python3 driver_station.py
```

You should see the robots appear in the driver station GUI within a few seconds.

## For Real Hardware

### Robot Setup

1. Flash your ESP32 with the code in `minibots/` folder using Arduino IDE
2. Edit `minibots/minibots.ino` and set your robot name:
   ```cpp
   Minibot bot("Robot1");  // Change "Robot1" to your robot's name
   ```
3. Ensure WiFi credentials match:
   - SSID: `WATCHTOWER`
   - Password: `lancerrobotics`
4. Upload to ESP32 and power on

### Driver Station Setup

1. **Connect PS5 Controllers**:
   - Connect via USB or Bluetooth to your computer
   - Both controllers should be recognized by the OS

2. **Start Driver Station**:
```bash
python3 driver_station.py
```

3. **Verify Robot Connection**:
   - Robots should appear in the left panel within 2-3 seconds
   - Status should show "Connected" in green

### Pairing Controllers to Robots

1. Click on a robot box (left side)
2. Click on a controller box (right side)
3. Click the "PAIR" button at the bottom
4. The pairing is now active!

### Operating the Robots

1. **Set to Teleop Mode**: Press `2` key
2. **Control with PS5 Controller**:
   - Left joystick for left axis values
   - Right joystick for right axis values
   - X, O, □, △ buttons are available
3. **Emergency Stop**: Press `SPACE` (press again to release)
4. **Return to Standby**: Press `1`

## Troubleshooting

**"No controllers detected"**
- Make sure controllers are connected and powered on
- Try reconnecting the controllers
- Restart the driver station

**"Robots not appearing"**
- Check WiFi network (must be on same network)
- Verify firewall allows UDP port 12345
- Check robot serial output for errors

**"Controller not responding"**
- Make sure you're in Teleop mode (press `2`)
- Check that emergency stop is not active
- Verify controller is paired to the robot

## Network Requirements

- All devices must be on the same WiFi network
- UDP ports must be open:
  - Port 12345 (discovery)
  - Ports 12346+ (command, assigned dynamically)
- Broadcast packets must be allowed

## Controller Button Mapping

| Button | PS5 Name | Code |
|--------|----------|------|
| Cross  | X        | 0x01 |
| Circle | O        | 0x02 |
| Square | □        | 0x04 |
| Triangle | △      | 0x08 |

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| 1 | Standby Mode |
| 2 | Teleop Mode |
| 3 | Autonomous Mode |
| SPACE | Emergency Stop (toggle) |
| ESC | Quit Application |
