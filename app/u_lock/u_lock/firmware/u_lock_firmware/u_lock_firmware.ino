/*
  U-Lock firmware for ESP32-C3 (BLE peripheral + SG90 servo)

  Libraries (Arduino Library Manager):
    - NimBLE-Arduino by h2zero (v2.x)
    - ESP32Servo

  BLE contract (must match lib/core/constants.dart):
    command (write)        : 0x01 = lock, 0x00 = unlock
    state   (read, notify) : 0x01 = locked, 0x00 = unlocked
    battery (read, notify) : 1 byte, 0-100 (%)
*/
#include <NimBLEDevice.h>
#include <ESP32Servo.h>

#define SERVICE_UUID "c0de0001-7a1b-4c2d-9e3f-0a1b2c3d4e5f"
#define CMD_UUID     "c0de0002-7a1b-4c2d-9e3f-0a1b2c3d4e5f"
#define STATE_UUID   "c0de0003-7a1b-4c2d-9e3f-0a1b2c3d4e5f"
#define BATT_UUID    "c0de0004-7a1b-4c2d-9e3f-0a1b2c3d4e5f"

const int SERVO_PIN = 4;
const int LOCK_ANGLE = 90;    // tune after mounting the pin on the lever
const int UNLOCK_ANGLE = 0;

// Battery sense: voltage divider (100k + 100k) into this ADC pin.
// Measure the cell BEFORE any regulator. Set these for your battery type.
const int BATT_PIN = 3;
const int BATT_FULL_MV = 3000;   // CR123A fresh ~3.0 V
const int BATT_EMPTY_MV = 2000;

Servo lockServo;
NimBLECharacteristic *stateChar, *battChar;

bool isLocked = false;
volatile int pendingCmd = -1;    // set in BLE callback, handled in loop()
unsigned long lastBatt = 0;

int readBatteryPercent() {
  int mv = analogReadMilliVolts(BATT_PIN) * 2;  // undo the 1:2 divider
  int pct = map(mv, BATT_EMPTY_MV, BATT_FULL_MV, 0, 100);
  return constrain(pct, 0, 100);
}

void publishState() {
  uint8_t v = isLocked ? 1 : 0;
  stateChar->setValue(v);
  stateChar->notify();
}

void publishBattery() {
  uint8_t v = (uint8_t)readBatteryPercent();
  battChar->setValue(v);
  battChar->notify();
}

void applyLock(bool lock) {
  lockServo.write(lock ? LOCK_ANGLE : UNLOCK_ANGLE);
  delay(500);                    // give the servo time to move
  isLocked = lock;
  publishState();
}

class ServerCb : public NimBLEServerCallbacks {
  void onDisconnect(NimBLEServer *s, NimBLEConnInfo &info, int reason) override {
    NimBLEDevice::startAdvertising();   // let the phone reconnect
  }
};

class CmdCb : public NimBLECharacteristicCallbacks {
  void onWrite(NimBLECharacteristic *c, NimBLEConnInfo &info) override {
    NimBLEAttValue v = c->getValue();
    if (v.size() >= 1) pendingCmd = v.data()[0];
  }
};

void setup() {
  Serial.begin(115200);
  lockServo.attach(SERVO_PIN);
  lockServo.write(UNLOCK_ANGLE);   // fail-safe default: unlocked at boot

  NimBLEDevice::init("U-Lock");
  NimBLEServer *server = NimBLEDevice::createServer();
  server->setCallbacks(new ServerCb());

  NimBLEService *svc = server->createService(SERVICE_UUID);
  NimBLECharacteristic *cmd = svc->createCharacteristic(CMD_UUID, NIMBLE_PROPERTY::WRITE);
  cmd->setCallbacks(new CmdCb());
  stateChar = svc->createCharacteristic(STATE_UUID, NIMBLE_PROPERTY::READ | NIMBLE_PROPERTY::NOTIFY);
  battChar  = svc->createCharacteristic(BATT_UUID,  NIMBLE_PROPERTY::READ | NIMBLE_PROPERTY::NOTIFY);
  svc->start();

  NimBLEAdvertising *adv = NimBLEDevice::getAdvertising();
  adv->addServiceUUID(SERVICE_UUID);   // the app scans for this UUID
  adv->enableScanResponse(true);
  adv->start();

  publishState();
  publishBattery();
  Serial.println("U-Lock advertising");
}

void loop() {
  if (pendingCmd >= 0) {
    int c = pendingCmd;
    pendingCmd = -1;
    Serial.println(c == 1 ? "LOCK" : "UNLOCK");
    applyLock(c == 1);
  }
  if (millis() - lastBatt > 30000) {
    lastBatt = millis();
    publishBattery();
  }
  delay(10);
}
