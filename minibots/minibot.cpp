#include "minibot.h"

// PWM channels (0-7 for low speed mode)
#define LEFT_MOTOR_CHANNEL  LEDC_CHANNEL_0
#define RIGHT_MOTOR_CHANNEL LEDC_CHANNEL_1
#define PWM_TIMER           LEDC_TIMER_0
#define PWM_SPEED_MODE      LEDC_LOW_SPEED_MODE

Minibot::Minibot(const char* id, uint8_t l, uint8_t r)
    : robotId(id), leftPin(l), rightPin(r),
      leftChannel(LEFT_MOTOR_CHANNEL), rightChannel(RIGHT_MOTOR_CHANNEL),
      leftX(127), leftY(127), rightX(127), rightY(127),
      buttons(0), gameStatus(0), emergencyStop(false), connected(false),
      assignedPort(0), lastPingTime(0), lastCommandTime(0)
{
    Serial.begin(115200);
    delay(100);
    Serial.println("\n=== Minibot Starting ===");
    Serial.println("2-Motor Drive Configuration");

    // Pin configuration
    Serial.println("Pin configuration:");
    Serial.print("  Left Motor:  GPIO"); Serial.println(leftPin);
    Serial.print("  Right Motor: GPIO"); Serial.println(rightPin);

    // 1. Configure PWM Timer
    ledc_timer_config_t timer_conf;
    timer_conf.speed_mode = PWM_SPEED_MODE;
    timer_conf.timer_num = PWM_TIMER;
    timer_conf.duty_resolution = (ledc_timer_bit_t)PWM_RES;
    timer_conf.freq_hz = PWM_FREQ;
    ledc_timer_config(&timer_conf);

    // 2. Configure Left Motor Channel
    ledc_channel_config_t left_channel_conf;
    left_channel_conf.gpio_num = leftPin;
    left_channel_conf.speed_mode = PWM_SPEED_MODE;
    left_channel_conf.channel = leftChannel;
    left_channel_conf.intr_type = LEDC_INTR_DISABLE;
    left_channel_conf.timer_sel = PWM_TIMER;
    left_channel_conf.duty = 0;
    left_channel_conf.hpoint = 0;
    ledc_channel_config(&left_channel_conf);

    // 3. Configure Right Motor Channel
    ledc_channel_config_t right_channel_conf = left_channel_conf; // Copy config
    right_channel_conf.gpio_num = rightPin;
    right_channel_conf.channel = rightChannel;
    ledc_channel_config(&right_channel_conf);

    Serial.println("PWM setup complete (using ESP-IDF).");

    // Connect to WiFi
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    Serial.print("WiFi connecting");
    int attempts = 0;
    while(WiFi.status() != WL_CONNECTED && attempts < 20) {
        delay(500);
        Serial.print(".");
        attempts++;
    }

    if(WiFi.status() == WL_CONNECTED) {
        Serial.println("\nConnected!");
        Serial.print("IP: ");
        Serial.println(WiFi.localIP());
    } else {
        Serial.println("\nFailed to connect!");
        Serial.print("SSID: "); Serial.println(WIFI_SSID);
        Serial.print("Password: "); Serial.println(WIFI_PASSWORD);
    }

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
    // 1.5ms neutral pulse for 100Hz, 16-bit res -> duty cycle of 9830
    uint32_t neutral_duty = (uint32_t)((1.5 / 10.0) * (1 << PWM_RES));
    ledc_set_duty(PWM_SPEED_MODE, leftChannel, neutral_duty);
    ledc_update_duty(PWM_SPEED_MODE, leftChannel);
    ledc_set_duty(PWM_SPEED_MODE, rightChannel, neutral_duty);
    ledc_update_duty(PWM_SPEED_MODE, rightChannel);
}

void Minibot::writeMotor(uint8_t channel, float value) {
    if(emergencyStop || value < -1.0 || value > 1.0) {
        stopAllMotors();
        return;
    }
    // Convert -1.0 to 1.0 into 1ms to 2ms pulse width
    float pulseMs = 1.5 + (value * 0.5);
    // Convert pulse width in ms to duty cycle
    uint32_t duty = (uint32_t)((pulseMs / (1000.0 / PWM_FREQ)) * (1 << PWM_RES));
    
    ledc_set_duty(PWM_SPEED_MODE, (ledc_channel_t)channel, duty);
    ledc_update_duty(PWM_SPEED_MODE, (ledc_channel_t)channel);
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
    writeMotor(leftChannel, value);
}

void Minibot::driveRight(float value) {
    writeMotor(rightChannel, value);
}
