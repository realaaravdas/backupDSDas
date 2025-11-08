#ifndef MINIBOT_H
#define MINIBOT_H

#include <Arduino.h>
#include <WiFi.h>
#include <WiFiUdp.h>

// PWM settings
#define PWM_FREQ 100
#define PWM_RES 16

// WiFi Configuration
#define WIFI_SSID "WATCHTOWER"
#define WIFI_PASSWORD "lancerrobotic"
#define DISCOVERY_PORT 12345

class Minibot {
private:
    const char* robotId;
    uint8_t pins[4];  // [left, right, dc, servo]

    uint8_t leftX, leftY, rightX, rightY;
    uint8_t buttons;  // bitfield

    uint8_t gameStatus;  // 0=standby, 1=teleop, 2=auto
    bool emergencyStop;
    bool connected;
    uint16_t assignedPort;
    uint32_t lastPingTime;
    uint32_t lastCommandTime;

    WiFiUDP udp;
    char packet[256];

    void sendDiscoveryPing();
    void stopAllMotors();
    void writeMotor(uint8_t channel, float value);

public:
    Minibot(const char* id, uint8_t l=16, uint8_t r=17, uint8_t d=18, uint8_t s=19);

    void updateController();

    // Getters
    inline uint8_t getLeftX() { return leftX; }
    inline uint8_t getLeftY() { return leftY; }
    inline uint8_t getRightX() { return rightX; }
    inline uint8_t getRightY() { return rightY; }

    inline bool getCross() { return buttons & 0x01; }
    inline bool getCircle() { return buttons & 0x02; }
    inline bool getSquare() { return buttons & 0x04; }
    inline bool getTriangle() { return buttons & 0x08; }

    inline bool isTeleop() { return gameStatus == 1; }
    inline bool isAuto() { return gameStatus == 2; }

    // Motor control
    void driveLeft(float value);
    void driveRight(float value);
    void driveDCMotor(float value);
    void driveServoMotor(int angle);
};

#endif
