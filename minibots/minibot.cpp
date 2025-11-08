#include "minibot.h"

Minibot::Minibot(const char* id, uint8_t l, uint8_t r, uint8_t d, uint8_t s)
    : robotId(id), leftX(127), leftY(127), rightX(127), rightY(127),
      buttons(0), gameStatus(0), emergencyStop(false), connected(false),
      assignedPort(0), lastPingTime(0), lastCommandTime(0)
{
    pins[0] = l; pins[1] = r; pins[2] = d; pins[3] = s;

    Serial.begin(115200);
    Serial.println("\n=== Minibot Starting ===");

    // Setup PWM channels
    for(uint8_t i = 0; i < 4; i++) {
        pinMode(pins[i], OUTPUT);
        ledcAttach(pins[i], PWM_FREQ, PWM_RES);
    }

    // Connect to WiFi
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    Serial.print("WiFi");
    while(WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    Serial.println("\nIP: " + WiFi.localIP().toString());

    // Start UDP
    udp.begin(DISCOVERY_PORT);
    stopAllMotors();
    Serial.println("Ready!");
}

void Minibot::sendDiscoveryPing() {
    char msg[64];
    snprintf(msg, 64, "DISCOVER:%s:%s", robotId, WiFi.localIP().toString().c_str());
    udp.beginPacket(IPAddress(255,255,255,255), DISCOVERY_PORT);
    udp.write((uint8_t*)msg, strlen(msg));
    udp.endPacket();
}

void Minibot::stopAllMotors() {
    for(uint8_t i = 0; i < 4; i++) {
        ledcWrite(pins[i], 9830); // 1.5ms neutral
    }
}

void Minibot::writeMotor(uint8_t channel, float value) {
    if(emergencyStop || value < -1.0 || value > 1.0) {
        ledcWrite(pins[channel], 9830);
        return;
    }
    float pulseMs = 0.5 * value + 1.5;
    uint16_t duty = (uint16_t)((pulseMs / 10.0) * 65535.0);
    ledcWrite(pins[channel], duty);
}

void Minibot::updateController() {
    uint32_t now = millis();

    // Send discovery if not connected
    if(!connected && (now - lastPingTime > 2000)) {
        sendDiscoveryPing();
        lastPingTime = now;
    }

    // Check timeout
    if(connected && (now - lastCommandTime > 5000)) {
        Serial.println("Timeout");
        connected = false;
        assignedPort = 0;
        udp.stop();
        udp.begin(DISCOVERY_PORT);
        stopAllMotors();
    }

    // Check for packets
    int len = udp.parsePacket();
    if(!len) return;

    len = udp.read(packet, 255);
    if(len <= 0) return;
    packet[len] = '\0';

    // PORT assignment
    if(!connected && strncmp(packet, "PORT:", 5) == 0) {
        char* sep = strchr(packet + 5, ':');
        if(sep) {
            *sep = '\0';
            if(strcmp(packet + 5, robotId) == 0) {
                assignedPort = atoi(sep + 1);
                if(assignedPort > 0) {
                    udp.stop();
                    udp.begin(assignedPort);
                    connected = true;
                    lastCommandTime = now;
                    Serial.println("Connected: " + String(assignedPort));
                }
            }
        }
        return;
    }

    // ESTOP
    if(strcmp(packet, "ESTOP") == 0) {
        emergencyStop = true;
        stopAllMotors();
        lastCommandTime = now;
        Serial.println("ESTOP!");
        return;
    }

    if(strcmp(packet, "ESTOP_OFF") == 0) {
        emergencyStop = false;
        lastCommandTime = now;
        Serial.println("ESTOP OFF");
        return;
    }

    if(!connected || emergencyStop) return;

    // Game status
    if(strncmp(packet, robotId, strlen(robotId)) == 0 && packet[strlen(robotId)] == ':') {
        char* status = packet + strlen(robotId) + 1;
        if(strcmp(status, "standby") == 0) gameStatus = 0;
        else if(strcmp(status, "teleop") == 0) gameStatus = 1;
        else if(strcmp(status, "autonomous") == 0) gameStatus = 2;
        lastCommandTime = now;
    }

    // Controller data (binary, 24 bytes)
    if(len >= 24 && gameStatus == 1) {
        char name[17];
        memcpy(name, packet, 16);
        name[16] = '\0';

        if(strcmp(name, robotId) == 0) {
            leftX = packet[16];
            leftY = packet[17];
            rightX = packet[18];
            rightY = packet[19];
            buttons = packet[22];
            lastCommandTime = now;
        }
    }
}

void Minibot::driveLeft(float value) {
    writeMotor(0, value);
}

void Minibot::driveRight(float value) {
    writeMotor(1, value);
}

void Minibot::driveDCMotor(float value) {
    writeMotor(2, value);
}

void Minibot::driveServoMotor(int angle) {
    if(angle < -50 || angle > 50 || emergencyStop) {
        ledcWrite(pins[3], 9830);
        return;
    }
    float pulseMs = 0.01 * angle + 1.5;
    uint16_t duty = (uint16_t)((pulseMs / 10.0) * 65535.0);
    ledcWrite(pins[3], duty);
}
