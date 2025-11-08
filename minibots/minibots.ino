/*
 * MINIBOT DRIVER STATION - ROBOT CODE
 * Plug-and-play ready for ESP32
 *
 * QUICK START:
 * 1. Change ROBOT_NAME to your robot's unique name (line 15)
 * 2. Choose your robot type (line 18) - uncomment ONE option
 * 3. Adjust pin numbers if needed (lines 21-24)
 * 4. Upload to ESP32
 * 5. Done! Robot will auto-connect to driver station
 */

#include "minibot.h"

// ============ CONFIGURATION ============

// Set your robot's unique name here (must match driver station)
#define ROBOT_NAME "robot1"  // Change this to: "robot2", "yourname", etc.

// Choose your robot type (uncomment ONE):
#define ROBOT_TYPE_TANK_DRIVE      // Two motors, left and right (most common)
//#define ROBOT_TYPE_ARCADE_DRIVE  // Two motors, arcade-style control
//#define ROBOT_TYPE_MECANUM       // Four motors, omni-directional
//#define ROBOT_TYPE_CUSTOM        // Write your own control code

// Motor pin configuration (adjust if using different pins)
#define LEFT_MOTOR_PIN   18    // Left motor PWM pin
#define RIGHT_MOTOR_PIN  19    // Right motor PWM pin
#define DC_MOTOR_PIN     20    // DC motor or back-left for mecanum
#define SERVO_MOTOR_PIN  20    // Servo or back-right for mecanum

// Advanced settings (usually don't need to change)
#define DEADZONE 10            // Joystick deadzone (0-127)
#define MOTOR_REVERSE_LEFT  false   // Set true to reverse left motor
#define MOTOR_REVERSE_RIGHT false   // Set true to reverse right motor
#define MAX_SPEED 1.0          // Max speed multiplier (0.0 to 1.0)

// ============ END CONFIGURATION ============

// Create robot instance
Minibot bot(ROBOT_NAME, LEFT_MOTOR_PIN, RIGHT_MOTOR_PIN, DC_MOTOR_PIN, SERVO_MOTOR_PIN);

// Helper function: Apply deadzone and scale
float applyDeadzone(uint8_t value, uint8_t deadzone = DEADZONE) {
    // Convert 0-255 to -1.0 to 1.0
    float scaled = (value - 127.5) / 127.5;

    // Apply deadzone
    if (abs(scaled) < (deadzone / 127.5)) {
        return 0.0;
    }

    // Apply max speed limit
    return constrain(scaled * MAX_SPEED, -1.0, 1.0);
}

void setup() {
    // All setup is handled in Minibot constructor
    Serial.println("Robot Type: "
    #if defined(ROBOT_TYPE_TANK_DRIVE)
        "Tank Drive"
    #elif defined(ROBOT_TYPE_ARCADE_DRIVE)
        "Arcade Drive"
    #elif defined(ROBOT_TYPE_MECANUM)
        "Mecanum Drive"
    #elif defined(ROBOT_TYPE_CUSTOM)
        "Custom"
    #else
        "NOT CONFIGURED - Please select a robot type!"
    #endif
    );
}

void loop() {
    // Get latest controller data from driver station
    bot.updateController();

    // Only control motors in teleop mode
    if (bot.isTeleop()) {

        // Get joystick values
        float leftX = applyDeadzone(bot.getLeftX());
        float leftY = applyDeadzone(bot.getLeftY());
        float rightX = applyDeadzone(bot.getRightX());
        float rightY = applyDeadzone(bot.getRightY());

        // Get button states
        bool btnCross = bot.getCross();
        bool btnCircle = bot.getCircle();
        bool btnSquare = bot.getSquare();
        bool btnTriangle = bot.getTriangle();

        // ========== ROBOT CONTROL CODE ==========

        #if defined(ROBOT_TYPE_TANK_DRIVE)
        // TANK DRIVE
        // Left stick Y controls left motor
        // Right stick Y controls right motor
        {
            float leftSpeed = -leftY;   // Negative because joystick up = negative
            float rightSpeed = -rightY;

            // Apply motor reversal if needed
            if (MOTOR_REVERSE_LEFT) leftSpeed = -leftSpeed;
            if (MOTOR_REVERSE_RIGHT) rightSpeed = -rightSpeed;

            bot.driveLeft(leftSpeed);
            bot.driveRight(rightSpeed);

            // Optional: DC motor controlled by left stick X
            bot.driveDCMotor(leftX);

            // Optional: Servo controlled by buttons
            if (btnTriangle) {
                bot.driveServoMotor(45);   // Triangle = servo right
            } else if (btnSquare) {
                bot.driveServoMotor(-45);  // Square = servo left
            } else {
                bot.driveServoMotor(0);    // Center
            }
        }

        #elif defined(ROBOT_TYPE_ARCADE_DRIVE)
        // ARCADE DRIVE
        // Left stick Y controls forward/backward
        // Right stick X controls turning
        {
            float forward = -leftY;
            float turn = rightX;

            // Mix forward and turn for differential drive
            float leftSpeed = forward + turn;
            float rightSpeed = forward - turn;

            // Normalize if over limits
            float maxMag = max(abs(leftSpeed), abs(rightSpeed));
            if (maxMag > 1.0) {
                leftSpeed /= maxMag;
                rightSpeed /= maxMag;
            }

            // Apply motor reversal if needed
            if (MOTOR_REVERSE_LEFT) leftSpeed = -leftSpeed;
            if (MOTOR_REVERSE_RIGHT) rightSpeed = -rightSpeed;

            bot.driveLeft(leftSpeed);
            bot.driveRight(rightSpeed);

            // Optional: DC motor speed control with left stick X
            bot.driveDCMotor(leftX);

            // Optional: Servo position with buttons
            if (btnTriangle) {
                bot.driveServoMotor(45);
            } else if (btnSquare) {
                bot.driveServoMotor(-45);
            } else {
                bot.driveServoMotor(0);
            }
        }

        #elif defined(ROBOT_TYPE_MECANUM)
        // MECANUM DRIVE (4-wheel omni-directional)
        // Uses all 4 motor outputs
        {
            float forward = -leftY;   // Forward/backward
            float strafe = leftX;     // Left/right strafing
            float turn = rightX;      // Rotation

            // Mecanum wheel mixing
            float frontLeft = forward + strafe + turn;
            float frontRight = forward - strafe - turn;
            float backLeft = forward - strafe + turn;
            float backRight = forward + strafe - turn;

            // Normalize speeds
            float maxMag = max(max(abs(frontLeft), abs(frontRight)),
                              max(abs(backLeft), abs(backRight)));
            if (maxMag > 1.0) {
                frontLeft /= maxMag;
                frontRight /= maxMag;
                backLeft /= maxMag;
                backRight /= maxMag;
            }

            // Apply to motors
            bot.driveLeft(frontLeft);      // Front left
            bot.driveRight(frontRight);    // Front right
            bot.driveDCMotor(backLeft);    // Back left
            bot.driveServoMotor((int)(backRight * 50));  // Back right (using servo output)
        }

        #elif defined(ROBOT_TYPE_CUSTOM)
        // CUSTOM ROBOT CODE
        // Write your own control logic here
        {
            // Example: Simple forward/backward with left stick
            bot.driveLeft(-leftY);
            bot.driveRight(-leftY);

            // TODO: Add your custom robot control code here
            // You have access to:
            //   - leftX, leftY, rightX, rightY (joystick values, -1.0 to 1.0)
            //   - btnCross, btnCircle, btnSquare, btnTriangle (button states)
            //   - bot.driveLeft(speed), bot.driveRight(speed)
            //   - bot.driveDCMotor(speed), bot.driveServoMotor(angle)
        }

        #else
        #error "No robot type selected! Please uncomment one ROBOT_TYPE_* define above"
        #endif

        // ========== END ROBOT CONTROL ==========

    } else {
        // Not in teleop mode - stop all motors
        bot.driveLeft(0);
        bot.driveRight(0);
        bot.driveDCMotor(0);
        bot.driveServoMotor(0);
    }

    // Small delay for stability (don't remove)
    delay(10);
}
