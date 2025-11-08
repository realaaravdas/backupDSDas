#include "minibot.h"

// Create minibot object with robot ID and motor pins
// Preferred motor pins: left=16, right=17, dcMotor=18, servoMotor=19
Minibot bot("YOUR NAME HERE");

void setup() {

}

void loop() {
  // Update controller values from the remote
  bot.updateController();

  // TODO: Write your robot control code here

}
