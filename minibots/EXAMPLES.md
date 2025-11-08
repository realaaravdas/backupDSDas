# Robot Configuration Examples

Copy and paste these configurations into your `minibots.ino` for quick setup.

---

## Example 1: Basic Tank Drive Robot

**Use case:** Simple 2-wheeled robot, one motor on each side

```cpp
// Configuration
#define ROBOT_NAME "tank1"
#define ROBOT_TYPE_TANK_DRIVE

#define LEFT_MOTOR_PIN   16
#define RIGHT_MOTOR_PIN  17
#define DC_MOTOR_PIN     18
#define SERVO_MOTOR_PIN  19

#define DEADZONE 15
#define MOTOR_REVERSE_LEFT  false
#define MOTOR_REVERSE_RIGHT false
#define MAX_SPEED 1.0
```

**Controls:**
- Left stick → Left motor
- Right stick → Right motor

---

## Example 2: Arcade Drive Robot

**Use case:** Video game style controls with one stick

```cpp
// Configuration
#define ROBOT_NAME "arcade1"
#define ROBOT_TYPE_ARCADE_DRIVE

#define LEFT_MOTOR_PIN   16
#define RIGHT_MOTOR_PIN  17
#define DC_MOTOR_PIN     18
#define SERVO_MOTOR_PIN  19

#define DEADZONE 20
#define MOTOR_REVERSE_LEFT  false
#define MOTOR_REVERSE_RIGHT false
#define MAX_SPEED 1.0
```

**Controls:**
- Left stick Y → Forward/Backward
- Right stick X → Turn left/right

---

## Example 3: Robot with Arm Servo

**Use case:** Tank drive with servo-controlled arm

```cpp
// Configuration
#define ROBOT_NAME "arm_bot"
#define ROBOT_TYPE_TANK_DRIVE

#define LEFT_MOTOR_PIN   16
#define RIGHT_MOTOR_PIN  17
#define DC_MOTOR_PIN     18
#define SERVO_MOTOR_PIN  19  // Arm servo

#define DEADZONE 10
#define MOTOR_REVERSE_LEFT  false
#define MOTOR_REVERSE_RIGHT false
#define MAX_SPEED 1.0
```

**Controls:**
- Left stick → Left motor
- Right stick → Right motor
- Triangle button → Arm up (45°)
- Square button → Arm down (-45°)

---

## Example 4: Slow Speed Learner Robot

**Use case:** Beginner robot with limited speed for safety

```cpp
// Configuration
#define ROBOT_NAME "learner1"
#define ROBOT_TYPE_ARCADE_DRIVE

#define LEFT_MOTOR_PIN   16
#define RIGHT_MOTOR_PIN  17
#define DC_MOTOR_PIN     18
#define SERVO_MOTOR_PIN  19

#define DEADZONE 25          // Large deadzone
#define MOTOR_REVERSE_LEFT  false
#define MOTOR_REVERSE_RIGHT false
#define MAX_SPEED 0.3        // Only 30% speed!
```

**Features:**
- Limited to 30% max speed
- Large deadzone for stable control
- Perfect for learning

---

## Example 5: Competition Robot (Reversed Motors)

**Use case:** Competition robot with reversed motor wiring

```cpp
// Configuration
#define ROBOT_NAME "comp_bot"
#define ROBOT_TYPE_TANK_DRIVE

#define LEFT_MOTOR_PIN   16
#define RIGHT_MOTOR_PIN  17
#define DC_MOTOR_PIN     18
#define SERVO_MOTOR_PIN  19

#define DEADZONE 10
#define MOTOR_REVERSE_LEFT  true   // Motor wired backwards
#define MOTOR_REVERSE_RIGHT false
#define MAX_SPEED 1.0
```

**Features:**
- Left motor reversed in software
- Full speed operation
- Competition ready

---

## Example 6: Mecanum Drive Robot

**Use case:** 4-wheel omni-directional robot

```cpp
// Configuration
#define ROBOT_NAME "mecanum1"
#define ROBOT_TYPE_MECANUM

// Pin mapping:
// Front Left  → 16
// Front Right → 17
// Back Left   → 18
// Back Right  → 19
#define LEFT_MOTOR_PIN   16
#define RIGHT_MOTOR_PIN  17
#define DC_MOTOR_PIN     18
#define SERVO_MOTOR_PIN  19

#define DEADZONE 15
#define MOTOR_REVERSE_LEFT  false
#define MOTOR_REVERSE_RIGHT false
#define MAX_SPEED 1.0
```

**Controls:**
- Left stick Y → Forward/Backward
- Left stick X → Strafe left/right
- Right stick X → Rotate

---

## Example 7: Custom - Claw Robot

**Use case:** Robot with custom claw mechanism

Add this to the `ROBOT_TYPE_CUSTOM` section:

```cpp
#define ROBOT_TYPE_CUSTOM

// Your custom code in the CUSTOM section:
{
    // Drive with left stick
    float leftSpeed = -leftY;
    float rightSpeed = -rightY;

    bot.driveLeft(leftSpeed);
    bot.driveRight(rightSpeed);

    // Claw control
    static int clawPos = 0;  // Current claw position

    if (btnTriangle) {
        clawPos = 50;   // Open claw
    } else if (btnCross) {
        clawPos = -50;  // Close claw
    }

    bot.driveServoMotor(clawPos);

    // Arm lift on DC motor
    if (btnSquare) {
        bot.driveDCMotor(0.5);   // Lift up
    } else if (btnCircle) {
        bot.driveDCMotor(-0.5);  // Lower down
    } else {
        bot.driveDCMotor(0);     // Hold position
    }
}
```

---

## Example 8: Custom - Line Following Robot

**Use case:** Tank drive with autonomous line following

```cpp
#define ROBOT_TYPE_CUSTOM

// Add at top of file:
#define LINE_SENSOR_LEFT  25
#define LINE_SENSOR_RIGHT 26

// In setup(), add:
pinMode(LINE_SENSOR_LEFT, INPUT);
pinMode(LINE_SENSOR_RIGHT, INPUT);

// Your custom code in the CUSTOM section:
{
    if (bot.isTeleop()) {
        // Manual control in teleop
        bot.driveLeft(-leftY);
        bot.driveRight(-rightY);
    } else if (bot.isAuto()) {
        // Line following in autonomous
        bool leftSensor = digitalRead(LINE_SENSOR_LEFT);
        bool rightSensor = digitalRead(LINE_SENSOR_RIGHT);

        if (!leftSensor && !rightSensor) {
            // Both on line - go straight
            bot.driveLeft(0.5);
            bot.driveRight(0.5);
        } else if (leftSensor && !rightSensor) {
            // Turn right
            bot.driveLeft(0.7);
            bot.driveRight(0.3);
        } else if (!leftSensor && rightSensor) {
            // Turn left
            bot.driveLeft(0.3);
            bot.driveRight(0.7);
        } else {
            // Lost line - stop
            bot.driveLeft(0);
            bot.driveRight(0);
        }
    }
}
```

**Controls:**
- Teleop mode (press '2'): Manual control
- Autonomous mode (press '3'): Line following

---

## Example 9: Two Robots - Different Names

**Robot 1:**
```cpp
#define ROBOT_NAME "robot1"
#define ROBOT_TYPE_TANK_DRIVE
// ... rest of config
```

**Robot 2:**
```cpp
#define ROBOT_NAME "robot2"
#define ROBOT_TYPE_TANK_DRIVE
// ... rest of config
```

**Important:** Each robot MUST have a unique name!

---

## Example 10: Custom WiFi Network

If not using "WATCHTOWER" network, edit `minibot.h`:

```cpp
// In minibot.h, lines 13-14:
#define WIFI_SSID "YOUR_NETWORK_NAME"
#define WIFI_PASSWORD "your_password"
```

Then update driver station config to match.

---

## Pin Reference Chart

```
Common ESP32 Pinout:

GPIO 16 ─────► Motor 1 (Left)
GPIO 17 ─────► Motor 2 (Right)
GPIO 18 ─────► Motor 3 (DC/Back Left)
GPIO 19 ─────► Motor 4 (Servo/Back Right)

Safe to use:
2, 4, 5, 12-19, 21-23, 25-27, 32-33

Avoid:
0 (Boot), 1 (TX), 3 (RX), 6-11 (Flash), 34-39 (Input only)
```

---

## Troubleshooting Common Issues

### Issue: Robot drives backwards
**Solution:** Swap motor reversal flags:
```cpp
#define MOTOR_REVERSE_LEFT  true   // ← Change these
#define MOTOR_REVERSE_RIGHT true
```

### Issue: Robot spins instead of going straight
**Solution:** Reverse one motor:
```cpp
#define MOTOR_REVERSE_LEFT  true   // Try reversing just one
```

### Issue: Dead joystick zones too sensitive
**Solution:** Increase deadzone:
```cpp
#define DEADZONE 25  // Increase from 10 to 25
```

### Issue: Robot too fast to control
**Solution:** Reduce max speed:
```cpp
#define MAX_SPEED 0.5  // Start with 50%
```

---

## Testing Your Configuration

1. **Upload code** to ESP32
2. **Open Serial Monitor** (115200 baud)
3. **Check output:**
   ```
   === Minibot Starting ===
   WiFi.........
   IP: 192.168.1.XXX
   Ready!
   Robot Type: Tank Drive
   ```
4. **Run driver station** and test controls
5. **Adjust configuration** as needed

---

## Need More Help?

- Check Serial Monitor for debug info
- Try `demo_mode.py` to test without hardware
- Verify pin connections with multimeter
- Test each motor individually

**Happy robot building! 🤖**
