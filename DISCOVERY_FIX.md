# Robot Discovery Fix - November 8, 2025

## Problem
Robots were not being discovered by the driver station, preventing connection and control.

## Root Cause
The discovery protocol had two issues:

1. **Demo Mode Issue**: Multiple simulated robots on localhost (127.0.0.1) all tried to bind to the same port (12345) using SO_REUSEPORT. This caused PORT assignment responses to be distributed randomly among the robots, preventing them from receiving their assignments.

2. **Response Addressing Issue**: The driver station was sending PORT responses to `(robot_ip, DISCOVERY_PORT)` instead of the actual sender address, which didn't work for multiple robots on the same IP.

## Solution

### Changes to demo_mode.py
- Changed robots to bind to any available port: `bind(('', 0))` 
- Removed SO_REUSEPORT which was causing packet distribution issues
- Robots now send discovery FROM their unique bound port
- Each robot receives responses at its own unique port
- Updated port switching logic to properly close old socket and bind to assigned port

### Changes to driver_station.py
- Line 151: Send PORT response to `addr` (actual sender address) from `recvfrom()`
- This works for both:
  - Demo mode: unique ports on localhost (127.0.0.1:random_port)
  - Real robots: unique IPs with port 12345 (192.168.1.x:12345)

## Protocol Flow (Fixed)

### Discovery Phase
```
1. Robot binds to a port (random for demo, 12345 for ESP32)
2. Robot sends: DISCOVER:<robotId>:<IP> to broadcast address port 12345
3. Driver station receives packet, captures sender address (IP, port)
4. Driver station assigns unique command port (12346+)
5. Driver station sends: PORT:<robotId>:<assigned_port> to sender address
6. Robot receives PORT message at its bound port
7. Robot switches to assigned port
8. Robot stops sending discovery broadcasts
```

### Command Phase
```
9. Driver station sends commands to (robot_ip, assigned_port)
10. Robot receives: game status, controller data, emergency stop
```

## Test Results

### Protocol Compatibility (test_protocol.py)
✅ All 6 tests pass:
- Controller packet format
- Discovery message format  
- Port assignment format
- Game status format
- Emergency stop format
- Axis mapping

### Integration Test
✅ Full workflow tested:
1. Robot discovery - 2 robots found
2. PORT assignment - unique ports assigned
3. Port switching - robots switch successfully
4. Game status - teleop commands received
5. Controller data - binary packets received correctly
6. Emergency stop - E-STOP commands received

### Manual Verification
✅ Demo robots:
- Create with unique ports (e.g., 37879, 32979)
- Send discovery broadcasts from their bound port
- Receive PORT assignments correctly
- Switch to assigned ports (12346, 12347)
- Stop broadcasting after assignment
- Receive and display all command types

## Compatibility

### ESP32 Real Robots
✅ The fix maintains full compatibility:
- ESP32 robots bind to port 12345 on their unique IP
- They send discovery FROM port 12345
- Driver station responds to (unique_ip, 12345)
- Each robot receives its own PORT message
- Protocol works as designed

### Demo Mode (Localhost)
✅ Now works correctly:
- Each simulated robot binds to unique random port
- They send discovery FROM their unique port
- Driver station responds to (127.0.0.1, unique_port)
- Each robot receives only its own PORT message
- Full simulation possible on single machine

## Security Notes
CodeQL flagged binding to all interfaces (`bind(('', port))`):
- **Status**: False positive / Acceptable by design
- **Rationale**: 
  - Required for UDP broadcast reception
  - System designed for trusted local network (WATCHTOWER)
  - Explicitly documented in CLAUDE.md
  - Demo code is for testing only, not production

## Testing Instructions

### Run Demo Mode
```bash
# Terminal 1: Start simulated robots
python3 demo_mode.py

# Terminal 2: In another terminal, test discovery
python3 test_protocol.py

# Expected output: All 6 tests pass
```

### With Real Robots
1. Ensure robots are on WATCHTOWER WiFi network
2. Run: `python3 driver_station.py`
3. Robots should appear in the "Robots:" section
4. Pair with controllers and test driving

## Files Modified
- `demo_mode.py`: Robot simulation for testing (35 insertions, 14 deletions)
- `driver_station.py`: Main driver station (4 insertions, 1 deletion)

## Verification
- ✅ Protocol tests pass
- ✅ Integration tests pass  
- ✅ Manual testing successful
- ✅ ESP32 compatibility maintained
- ✅ Security review completed
