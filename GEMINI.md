# Minibot Driver Station Project

## Project Overview

This project is a complete system for controlling ESP32-based robots ("minibots") from a graphical driver station running on a PC. The system is designed for robotics competitions or educational purposes.

*   **Driver Station:** A Python application using the `pygame` library to create a GUI. It discovers robots on the network, displays their status, handles pairing with PS5 controllers, and sends control commands.
*   **Robot:** An ESP32 microcontroller running C++ code within the Arduino framework. The robot code is designed to be plug-and-play, with support for different drive types (Tank, Arcade, Mecanum).
*   **Communication:** The driver station and robots communicate over a WiFi network using a custom UDP-based protocol. Robots are automatically discovered using a broadcast mechanism.

## Building and Running

### 1. Install Dependencies

The only Python dependency is `pygame`.

```bash
pip install -r requirements.txt
```

### 2. Running the Driver Station

To start the main GUI application:

```bash
python driver_station.py
```

### 3. Running in Demo Mode (No Hardware Required)

To test the driver station GUI without a physical robot, you can run a simulated robot.

*   **Start the simulated robot(s) in one terminal:**
    ```bash
    python demo_mode.py
    ```
*   **Start the driver station in a second terminal:**
    ```bash
    python driver_station.py
    ```

### 4. Flashing the Robot (ESP32)

The robot code is located in the `minibots/` directory and is intended to be compiled and uploaded using the Arduino IDE.

1.  Open `minibots/minibots.ino` in the Arduino IDE.
2.  Configure the `ROBOT_NAME` and `ROBOT_TYPE` macros.
3.  Ensure the WiFi credentials in `minibots/minibot.h` are correct (`WATCHTOWER`/`lancerrobotics`).
4.  Upload the code to your ESP32 board.

## Development Conventions

*   **Protocol:** The communication protocol is documented in `ARCHITECTURE.md`. It uses UDP broadcast for discovery on port `12345` and unicast for commands on dynamically assigned ports.
*   **Testing:** The project includes several test scripts:
    *   `test_full_system.py`: A basic test for the discovery protocol.
    *   `test_connection.py`: A network diagnostic tool.
    *   `test_protocol.py`: For testing protocol compatibility.
*   **Documentation:** The project is heavily documented in Markdown files (`.md`). `START_HERE.md` is the main entry point, and `ARCHITECTURE.md` provides a deep dive into the system design.
