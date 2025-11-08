# System Architecture

## Overview

The Minibot Driver Station system consists of ESP32-based robots and a Python GUI driver station that communicate over WiFi using UDP.

## System Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    WiFi Network (WATCHTOWER)                 │
│                                                               │
│  ┌──────────────┐         UDP Broadcast/Unicast             │
│  │   ESP32      │◄────────────────────────────────┐         │
│  │   Robot 1    │                                  │         │
│  │              │─────────────────────────────────┐│         │
│  └──────────────┘          Port 12345             ││         │
│                           (Discovery)              ││         │
│                                                    ││         │
│  ┌──────────────┐         Port 12346+             ││         │
│  │   ESP32      │◄────────(Commands)──────────────┘│         │
│  │   Robot 2    │                                  │         │
│  │              │─────────────────────────────────┐│         │
│  └──────────────┘                                 ││         │
│                                                    ││         │
│                                                    ▼▼         │
│                                          ┌──────────────────┐│
│                                          │  Driver Station  ││
│  ┌──────────────┐    USB/BT             │   (Python GUI)   ││
│  │ PS5 Control  │───────────────────────►│                  ││
│  │  (Player 1)  │                        │  - Robot Disc.   ││
│  └──────────────┘                        │  - Controller    ││
│                                          │  - Game Status   ││
│  ┌──────────────┐    USB/BT             │  - Emergency     ││
│  │ PS5 Control  │───────────────────────►│                  ││
│  │  (Player 2)  │                        └──────────────────┘│
│  └──────────────┘                                            │
└─────────────────────────────────────────────────────────────┘
```

## Component Details

### ESP32 Robots (minibot.cpp/h)
- **Hardware**: ESP32 microcontroller with motor controllers
- **Motors**: Left, Right, DC, Servo (4 motors per robot)
- **Network**: Connects to WATCHTOWER WiFi network
- **Communication**: UDP-based protocol
- **Behavior**:
  - Broadcasts discovery packets every 2 seconds when not connected
  - Listens for port assignment from driver station
  - Receives controller data and game status
  - Auto-disconnects after 5 seconds without commands

### Driver Station (driver_station.py)
- **Platform**: Python 3.x with pygame
- **Interface**: GUI (1200x700 pixels) at 60 FPS
- **Network**: UDP listener on port 12345 (discovery)
- **Controllers**: Supports up to 2 PS5 controllers via pygame
- **Functions**:
  - Discovers robots on network
  - Assigns unique command ports to robots (12346+)
  - Pairs controllers to robots
  - Sends controller data at 60 Hz
  - Manages game status (standby/teleop/autonomous)
  - Provides emergency stop functionality

## Communication Protocol

### 1. Discovery Phase

```
Robot → Broadcast:  "DISCOVER:<robotId>:<IP>"
                                ↓
Driver Station → Robot:  "PORT:<robotId>:<port>"
                                ↓
           Robot switches to assigned port
```

### 2. Operational Phase

**Game Status Updates:**
```
Driver Station → Robot:  "<robotId>:<status>"
Status values: "standby", "teleop", "autonomous"
```

**Controller Data (Binary - 24 bytes):**
```
Bytes 0-15:   Robot name (null-terminated string)
Bytes 16-21:  Axes (leftX, leftY, rightX, rightY, unused, unused)
Bytes 22-23:  Button states (bitfield)

Button bits:
  Bit 0: Cross
  Bit 1: Circle
  Bit 2: Square
  Bit 3: Triangle
```

**Emergency Stop:**
```
Driver Station → All Robots:  "ESTOP"      (activate)
Driver Station → All Robots:  "ESTOP_OFF"  (deactivate)
```

### 3. Timeout & Reconnection

- **Robot Timeout**: 5 seconds without commands → disconnect
- **Driver Station Timeout**: 10 seconds without discovery → remove robot
- **Reconnection**: Robot automatically restarts discovery when disconnected

## Data Flow

### Controller Input → Robot Output

```
┌─────────────┐
│  PS5 Pad    │
│  Joysticks  │  Analog Values (-1.0 to +1.0)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Pygame    │  Read joystick axes and buttons
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Mapping   │  Convert to 0-255 range
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Packet    │  Format as 24-byte binary packet
└──────┬──────┘
       │
       ▼  UDP (60 Hz)
┌─────────────┐
│   ESP32     │  Parse binary packet
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Robot     │  Drive motors based on values
│   Motors    │  (leftX, leftY, rightX, rightY)
└─────────────┘
```

## Network Ports

| Port  | Purpose              | Direction                    |
|-------|----------------------|------------------------------|
| 12345 | Discovery            | Bidirectional (broadcast)    |
| 12346 | Robot 1 Commands     | Driver Station → Robot       |
| 12347 | Robot 2 Commands     | Driver Station → Robot       |
| 12348+| Additional Robots    | Driver Station → Robot       |

## State Machine

### Robot States

```
┌─────────┐  Power On  ┌──────────────┐  PORT received  ┌───────────┐
│  INIT   │───────────►│  DISCOVERY   │────────────────►│ CONNECTED │
└─────────┘            └──────────────┘                 └─────┬─────┘
                              ▲                                │
                              │                                │
                              │        Timeout (5s)            │
                              └────────────────────────────────┘
```

### Driver Station States

```
┌──────────┐  Robot Found  ┌───────────┐  User Pairs   ┌─────────┐
│ STANDBY  │──────────────►│ CONNECTED │──────────────►│ TELEOP  │
└────┬─────┘               └─────┬─────┘               └────┬────┘
     │                           │                           │
     │      Emergency Stop       │                           │
     └───────────────────────────┴───────────────────────────┘
```

## File Structure

```
backupDSDas/
├── driver_station.py      # Main GUI application
├── requirements.txt       # Python dependencies
├── README.md             # User documentation
├── QUICKSTART.md         # Quick start guide
├── ARCHITECTURE.md       # This file
├── SECURITY.md           # Security considerations
├── test_protocol.py      # Protocol tests
├── demo_mode.py          # Simulation for testing
├── test_connection.py    # Network diagnostics
├── .gitignore           # Git ignore patterns
└── minibots/            # ESP32 Arduino code (unchanged)
    ├── minibot.h
    ├── minibot.cpp
    └── minibots.ino
```

## Performance Characteristics

- **Update Rate**: 60 Hz (controller → robot)
- **Discovery Rate**: Every 2 seconds (robot → driver station)
- **Timeout**: 5 seconds (robot), 10 seconds (driver station)
- **Network Latency**: <10ms typical on local WiFi
- **Packet Size**: 24 bytes (controller data)
- **GUI Frame Rate**: 60 FPS

## Scalability

Current implementation supports:
- **Robots**: 2 simultaneous (expandable)
- **Controllers**: 2 PS5 controllers (expandable)
- **Network**: Single broadcast domain
- **Throughput**: Minimal (~1.5 KB/s per robot)

To expand:
1. Increase `range(2)` in controller display code
2. Add more robot slots in UI layout
3. No protocol changes needed

## Error Handling

1. **Network Loss**: Robot auto-reverts to discovery mode
2. **Controller Disconnect**: Robot stops receiving updates (motors stop on timeout)
3. **Emergency Stop**: Immediate stop command to all robots
4. **Port Conflicts**: Driver station assigns unique ports per robot
5. **Invalid Data**: Robot validates packet format before processing

## Testing Strategy

1. **Unit Tests**: `test_protocol.py` validates packet formats
2. **Integration Tests**: `demo_mode.py` simulates robot behavior
3. **Network Tests**: `test_connection.py` validates connectivity
4. **Manual Tests**: Physical testing with real hardware

## Security Model

- **Trust Model**: Closed, trusted network (WATCHTOWER)
- **Authentication**: None (by design for simplicity)
- **Encryption**: None (local network only)
- **Access Control**: Network-level (WiFi password)
- **Threat Model**: Educational/competition environment

See SECURITY.md for detailed security analysis.
