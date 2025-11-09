#include <WiFi.h>
#include <WiFiUdp.h>

// ============ CONFIGURATION ============
// WiFi credentials
const char WIFI_SSID[] = "WATCHTOWER";
const char WIFI_PASSWORD[] = "lancerrobotics";

// Robot identification - CHANGE THIS FOR EACH ROBOT
const char ROBOT_ID[] = "robot1";

// Network ports
const uint16_t DISCOVERY_PORT = 12345;

// Motor pins
const uint8_t MOTOR_LEFT_PIN = 16;
const uint8_t MOTOR_RIGHT_PIN = 19;

// PWM configuration
const uint16_t PWM_FREQ = 100;
const uint8_t PWM_RES = 16;
const uint16_t PWM_NEUTRAL = 9830;  // 1.5ms pulse
const uint16_t PWM_MIN = 6553;      // 1.0ms pulse
const uint16_t PWM_MAX = 13107;     // 2.0ms pulse

// Timing constants
const uint16_t DISCOVERY_INTERVAL = 2000;  // ms
const uint16_t COMMAND_TIMEOUT = 5000;     // ms

// ============ GLOBAL STATE ============
WiFiUDP udp;
uint16_t assignedPort = 0;
bool portAssigned = false;
unsigned long lastDiscovery = 0;
unsigned long lastCommand = 0;

// Game state
enum { STANDBY = 0, TELEOP = 1, AUTO = 2 };
uint8_t gameStatus = STANDBY;
bool emergencyStop = false;

// Controller data
uint8_t leftX = 127, leftY = 127, rightX = 127, rightY = 127;
uint16_t buttons = 0;

// ============ HELPER FUNCTIONS ============

void connectWiFi() {
  Serial.print("Connecting to WiFi");
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\nConnected!");
  Serial.print("IP: ");
  Serial.println(WiFi.localIP());
}

void sendDiscovery() {
  char msg[64];
  snprintf(msg, sizeof(msg), "DISCOVER:%s:%s",
           ROBOT_ID, WiFi.localIP().toString().c_str());

  udp.beginPacket("255.255.255.255", DISCOVERY_PORT);
  udp.write((uint8_t*)msg, strlen(msg));
  udp.endPacket();

  Serial.print("Discovery: ");
  Serial.println(msg);
}

int speedToPWM(float speed) {
  // Clamp to [-1.0, 1.0]
  if (speed > 1.0) speed = 1.0;
  if (speed < -1.0) speed = -1.0;

  // Map to PWM
  if (speed >= 0) {
    return PWM_NEUTRAL + (int)(speed * (PWM_MAX - PWM_NEUTRAL));
  } else {
    return PWM_NEUTRAL + (int)(speed * (PWM_NEUTRAL - PWM_MIN));
  }
}

void updateMotors() {
  // Convert controller bytes (0-255) to speed (-1.0 to 1.0)
  // Invert Y axis (controller forward is negative)
  float leftSpeed = -(leftY - 127) / 127.0;
  float rightSpeed = -(rightY - 127) / 127.0;

  // Write to motors
  ledcWrite(MOTOR_LEFT_PIN, speedToPWM(leftSpeed));
  ledcWrite(MOTOR_RIGHT_PIN, speedToPWM(rightSpeed));
}

void stopMotors() {
  ledcWrite(MOTOR_LEFT_PIN, PWM_NEUTRAL);
  ledcWrite(MOTOR_RIGHT_PIN, PWM_NEUTRAL);
}

void parseTextPacket(char* packet) {
  Serial.print("Text: ");
  Serial.println(packet);

  // PORT assignment: "PORT:<robotId>:<port>"
  if (strncmp(packet, "PORT:", 5) == 0) {
    char* idStart = packet + 5;
    char* portStart = strchr(idStart, ':');
    if (portStart) {
      *portStart = '\0';
      portStart++;

      if (strcmp(idStart, ROBOT_ID) == 0) {
        assignedPort = atoi(portStart);
        portAssigned = true;
        udp.begin(assignedPort);
        Serial.print("Port assigned: ");
        Serial.println(assignedPort);
      }
    }
    return;
  }

  // Emergency stop
  if (strcmp(packet, "ESTOP") == 0) {
    emergencyStop = true;
    stopMotors();
    Serial.println("ESTOP ON");
    return;
  }

  if (strcmp(packet, "ESTOP_OFF") == 0) {
    emergencyStop = false;
    Serial.println("ESTOP OFF");
    return;
  }

  // Game status: "<robotId>:<status>"
  char* statusStart = strchr(packet, ':');
  if (statusStart) {
    *statusStart = '\0';
    statusStart++;

    if (strcmp(packet, ROBOT_ID) == 0) {
      if (strcmp(statusStart, "standby") == 0) {
        gameStatus = STANDBY;
        Serial.println("Mode: STANDBY");
      } else if (strcmp(statusStart, "teleop") == 0) {
        gameStatus = TELEOP;
        Serial.println("Mode: TELEOP");
      } else if (strcmp(statusStart, "autonomous") == 0) {
        gameStatus = AUTO;
        Serial.println("Mode: AUTO");
      }
    }
  }
}

void parseBinaryPacket(uint8_t* packet) {
  // Binary format (24 bytes):
  // 0-15: Robot name
  // 16-21: leftX, leftY, rightX, rightY, unused, unused
  // 22-23: Button states

  char packetName[16];
  memcpy(packetName, packet, 16);
  packetName[15] = '\0';

  // Check if for us
  if (strcmp(packetName, ROBOT_ID) != 0) return;

  // Extract data
  leftX = packet[16];
  leftY = packet[17];
  rightX = packet[18];
  rightY = packet[19];
  buttons = packet[22] | (packet[23] << 8);

  Serial.printf("LX=%d LY=%d RX=%d RY=%d\n", leftX, leftY, rightX, rightY);
}

void receivePackets() {
  int packetSize = udp.parsePacket();
  if (packetSize == 0) return;

  uint8_t buffer[256];
  int len = udp.read(buffer, sizeof(buffer) - 1);
  if (len <= 0) return;

  lastCommand = millis();

  // Binary packet (controller data) is exactly 24 bytes
  if (len == 24) {
    parseBinaryPacket(buffer);
  } else {
    // Text packet
    buffer[len] = '\0';
    parseTextPacket((char*)buffer);
  }
}

// ============ ARDUINO FUNCTIONS ============

void setup() {
  Serial.begin(115200);
  Serial.println("\n=== Minibot Starting ===");
  Serial.print("Robot ID: ");
  Serial.println(ROBOT_ID);

  // Setup motors
  ledcAttach(MOTOR_LEFT_PIN, PWM_FREQ, PWM_RES);
  ledcAttach(MOTOR_RIGHT_PIN, PWM_FREQ, PWM_RES);
  stopMotors();

  // Connect to WiFi
  connectWiFi();

  // Start UDP on discovery port
  udp.begin(DISCOVERY_PORT);

  Serial.println("Ready!");
}

void loop() {
  unsigned long now = millis();

  // Handle timeout - return to discovery
  if (portAssigned && (now - lastCommand > COMMAND_TIMEOUT)) {
    Serial.println("Timeout - back to discovery");
    portAssigned = false;
    assignedPort = 0;
    stopMotors();
    udp.begin(DISCOVERY_PORT);
  }

  // Send discovery broadcast
  if (!portAssigned || (now - lastDiscovery > DISCOVERY_INTERVAL)) {
    sendDiscovery();
    lastDiscovery = now;
  }

  // Receive packets
  receivePackets();

  // Update motors (only in teleop mode, not estopped)
  if (portAssigned && gameStatus == TELEOP && !emergencyStop) {
    updateMotors();
  } else {
    stopMotors();
  }

  delay(10);  // Small delay to prevent watchdog issues
}
