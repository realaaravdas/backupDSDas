#include "minibot.h"

// Constructor
Minibot::Minibot(const char* robotId,
                 int leftMotorPin, int rightMotorPin,
                 int dcMotorPin, int servoMotorPin)
                  : robotId(robotId),
                      leftPin(leftMotorPin), rightPin(rightMotorPin),
                      dcMotorPin(dcMotorPin), servoMotorPin(servoMotorPin),
                      leftX(127), leftY(127), rightX(127), rightY(127),
                      cross(false), circle(false), square(false), triangle(false),
                      gameStatus("standby"), emergencyStop(false), connected(false),
                      assignedPort(0), lastPingTime(0), lastCommandTime(0)
{
  Serial.begin(115200);

  pinMode(leftPin, OUTPUT);
  pinMode(rightPin, OUTPUT);
  pinMode(dcMotorPin, OUTPUT);
  pinMode(servoMotorPin, OUTPUT);
  bool left = ledcAttachChannel(leftPin, freq, resolution, LEFT_PWM_CHANNEL);
  bool right = ledcAttachChannel(rightPin, freq, resolution, RIGHT_PWM_CHANNEL);
  bool dc = ledcAttachChannel(dcMotorPin, freq, resolution, DC_PWM_CHANNEL);
  bool servo = ledcAttachChannel(servoMotorPin, freq, resolution, SERVO_PWM_CHANNEL);

  Serial.println(left);
  Serial.println(right);
  Serial.println(dc);
  Serial.println(servo);

  // Wi-Fi connection
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nConnected! IP: " + WiFi.localIP().toString());

  // Start UDP on discovery port
  udp.begin(DISCOVERY_PORT);
  Serial.println("Listening on discovery port " + String(DISCOVERY_PORT));

  // Stop all motors initially
  stopAllMotors();
}



void Minibot::sendDiscoveryPing() {
  // Format: "DISCOVER:<robotId>:<IP>"
  String msg = "DISCOVER:" + String(robotId) + ":" + WiFi.localIP().toString();
  udp.beginPacket(IPAddress(255, 255, 255, 255), DISCOVERY_PORT);
  udp.write((const uint8_t*)msg.c_str(), msg.length());
  udp.endPacket();
  Serial.println("Sent discovery ping: " + msg);
}

void Minibot::stopAllMotors() {
  driveLeft(0);
  driveRight(0);
  driveDCMotor(0);
  driveServoMotor(0);
}

void Minibot::updateController() {
  // Send discovery pings if not connected (every 2 seconds)
  unsigned long now = millis();
  if (!connected && (now - lastPingTime > 2000)) {
    sendDiscoveryPing();
    lastPingTime = now;
  }

  // Check for timeout (5 seconds without command = disconnect)
  if (connected && (now - lastCommandTime > 5000)) {
    Serial.println("Connection timeout - reverting to discovery mode");
    connected = false;
    assignedPort = 0;
    udp.stop();
    udp.begin(DISCOVERY_PORT);
    stopAllMotors();
  }

  int packetSize = udp.parsePacket();
  if (packetSize) {
    int len = udp.read(incomingPacket, 255);
    if (len > 0) incomingPacket[len] = '\0';

    String packetStr = String(incomingPacket);

    // Handle port assignment response: "PORT:<robotId>:<port>"
    if (!connected && packetStr.startsWith("PORT:")) {
      int sep1 = packetStr.indexOf(':', 5);
      if (sep1 != -1) {
        String name = packetStr.substring(5, sep1);
        if (name == robotId) {
          assignedPort = packetStr.substring(sep1 + 1).toInt();
          if (assignedPort > 0) {
            udp.stop();
            udp.begin(assignedPort);
            connected = true;
            lastCommandTime = now;
            Serial.println("Assigned port " + String(assignedPort) + " - connected!");
          }
        }
      }
      return;
    }

    // Handle emergency stop: "ESTOP"
    if (packetStr == "ESTOP") {
      emergencyStop = true;
      stopAllMotors();
      Serial.println("EMERGENCY STOP ACTIVATED");
      lastCommandTime = now;
      return;
    }

    // Handle emergency stop release: "ESTOP_OFF"
    if (packetStr == "ESTOP_OFF") {
      emergencyStop = false;
      Serial.println("Emergency stop released");
      lastCommandTime = now;
      return;
    }

    // Only process movement commands if connected and not emergency stopped
    if (!connected || emergencyStop) return;

    // Check if it's a game status packet (text format)
    if (packetStr.startsWith(robotId)) {
      int sepIndex = packetStr.indexOf(':');
      if (sepIndex != -1) {
        gameStatus = packetStr.substring(sepIndex + 1);
        lastCommandTime = now;
      }
    }

    // Decode controller data (binary format) - only in teleop mode
    if (len >= 24 && gameStatus == "teleop") {
      char robotName[17];
      uint8_t axes[6];
      uint8_t buttons[2];

      memcpy(robotName, incomingPacket, 16);
      robotName[16] = '\0';
      memcpy(axes, incomingPacket + 16, 6);
      memcpy(buttons, incomingPacket + 22, 2);

      if (String(robotName) == robotId) {
        leftX = axes[0];
        leftY = axes[1];
        rightX = axes[2];
        rightY = axes[3];

        cross = buttons[0] & 0x01;
        circle = buttons[0] & 0x02;
        square = buttons[0] & 0x04;
        triangle = buttons[0] & 0x08;

        lastCommandTime = now;
      }
    }
  }
}

int Minibot::getLeftX() { return leftX; }
int Minibot::getLeftY() { return leftY; }
int Minibot::getRightX() { return rightX; }
int Minibot::getRightY() { return rightY; }

bool Minibot::getCross() { return cross; }
bool Minibot::getCircle() { return circle; }
bool Minibot::getSquare() { return square; }
bool Minibot::getTriangle() { return triangle; }

String Minibot::getGameStatus() { return gameStatus; }

bool Minibot::driveDCMotor(float value) {
  if (value < -1 || value > 1)
    {
    return false;
  }

    float pulseWidthMs = 0.5 * value + 1.5;
    int dutyCycle = (pulseWidthMs / 10.0) * 65535;
    ledcWriteChannel(DC_PWM_CHANNEL, dutyCycle);
  return true;
}

bool Minibot::driveLeft(float value) {
  if (value < -1 || value > 1)
  {
    return false;
  }
  float pulseWidthMs = 0.5 * value + 1.5;
  int dutyCycle = (pulseWidthMs / 10.0) * 65535;
  ledcWriteChannel(LEFT_PWM_CHANNEL, dutyCycle);
  return true;
}

bool Minibot::driveRight(float value) {
  if (value < -1 || value > 1)
  {
    return false;
  }
  float pulseWidthMs = 0.5 * value + 1.5;
  int dutyCycle = (pulseWidthMs / 10.0) * 65535;
  ledcWriteChannel(RIGHT_PWM_CHANNEL, dutyCycle);
  return true;
}

bool Minibot::driveServoMotor(int angle) {
  if (angle < -50 || angle > 50) {
    return false;
  }
  float pulseWidthMs = 0.01 * angle + 1.5;
  int dutyCycle = (pulseWidthMs / 10.0) * 65535;
  ledcWriteChannel(SERVO_PWM_CHANNEL, dutyCycle);
  return true;
}
