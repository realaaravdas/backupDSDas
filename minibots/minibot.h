#ifndef MINIBOT_H
#define MINIBOT_H

#include <Arduino.h>
#include <WiFi.h>
#include <WiFiUdp.h>

// PWM Channel Definitions
const int LEFT_PWM_CHANNEL = 0;
const int RIGHT_PWM_CHANNEL = 1;
const int DC_PWM_CHANNEL = 2;
const int SERVO_PWM_CHANNEL = 3;
const int freq = 100;
const int resolution = 16;

// WiFi Configuration
#define WIFI_SSID "WATCHTOWER"
#define WIFI_PASSWORD "lancerrobotics"
#define DISCOVERY_PORT 12345
#define COMMAND_PORT_BASE 12346

class Minibot {
private:
    const char* robotId;
    int leftPin;
    int rightPin;
    int dcMotorPin;
    int servoMotorPin;

    int leftX;
    int leftY;
    int rightX;
    int rightY;

    bool cross;
    bool circle;
    bool square;
    bool triangle;

    String gameStatus;
    bool emergencyStop;
    bool connected;
    unsigned int assignedPort;
    unsigned long lastPingTime;
    unsigned long lastCommandTime;

    WiFiUDP udp;
    char incomingPacket[256];

    void sendDiscoveryPing();
    void stopAllMotors();


public:
    // Constructor
    Minibot(const char* robotId,
          int leftMotorPin = 16, int rightMotorPin = 17,
          int dcMotorPin = 18, int servoMotorPin = 19);

    // Update controller state from UDP packets
    void updateController();

    // Getter methods for joystick axes
    int getLeftX();
    int getLeftY();
    int getRightX();
    int getRightY();

    // Getter methods for buttons
    bool getCross();
    bool getCircle();
    bool getSquare();
    bool getTriangle();

    // Get game status
    String getGameStatus();

    // Motor control methods
    bool driveDCMotor(float value);      // value: -1.0 to 1.0
    bool driveLeft(float value);         // value: -1.0 to 1.0
    bool driveRight(float value);        // value: -1.0 to 1.0
    bool driveServoMotor(int angle);     // angle: -50 to 50 degrees
};

#endif // MINIBOT_H
