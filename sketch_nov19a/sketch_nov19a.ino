
#include <Arduino.h>
#include <ESP32Servo.h>

#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLE2902.h>

// ---------------- BLE CONFIGURATION ----------------

#define DEVICE_NAME "U-LOCK"

#define SERVICE_UUID \
  "12345678-1234-5678-1234-56789abcdef0"

#define WRITE_UUID \
  "12345678-1234-5678-1234-56789abcdef1"

#define NOTIFY_UUID \
  "12345678-1234-5678-1234-56789abcdef2"

// ---------------- SERVO CONFIGURATION ----------------

#define SERVO_PIN 4

const int LOCK_ANGLE = 110;
const int UNLOCK_ANGLE = 20;

Servo servo;

// ---------------- BLE VARIABLES ----------------
// ---------------- BLE VARIABLES ----------------

BLECharacteristic *notifyCharacteristic = nullptr;
BLE2902 *notifyDescriptor = nullptr;

// BLE connection tracking
volatile bool restartAdvertising = false;
volatile bool phoneConnected = false;
volatile bool initialStatusPending = false;
volatile bool notificationsSubscribed = false;

// Current commanded lock state
// false = unlocked, true = locked
bool isLocked = false;

// ---------------- NOTIFICATION FUNCTIONS ----------------

void notifyLockState() {

  if (!phoneConnected ||
      notifyCharacteristic == nullptr ||
      notifyDescriptor == nullptr) {
    return;
  }

  if (!notificationsSubscribed) {
  Serial.println("[BLE] Notifications are not subscribed.");
  return;
  }

  const char *currentState = isLocked ? "LOCKED" : "UNLOCKED";

  notifyCharacteristic->setValue(currentState);
  notifyCharacteristic->notify();

  Serial.print("[BLE] Current lock state sent: ");
  Serial.println(currentState);
}

// ---------------- SERVO FUNCTIONS ----------------

void lockDevice() {

  servo.write(LOCK_ANGLE);
  isLocked = true;

  Serial.println("[U-LOCK] LOCKED");

  notifyLockState();
}

void unlockDevice() {

  servo.write(UNLOCK_ANGLE);
  isLocked = false;

  Serial.println("[U-LOCK] UNLOCKED");

  notifyLockState();
}

// ---------------- BLE CALLBACKS ----------------

class ServerCallbacks : public BLEServerCallbacks {

  void onConnect(BLEServer *server) override {

    Serial.println("[BLE] Phone connected!");

    phoneConnected = true;
    initialStatusPending = true;

    Serial.println("[BLE] Waiting for notification subscription...");
  }

  void onDisconnect(BLEServer *server) override {

    Serial.println("[BLE] Phone disconnected!");

    phoneConnected = false;
    initialStatusPending = false;
    notificationsSubscribed = false;
    restartAdvertising = true;
  }
};

class WriteCallbacks : public BLECharacteristicCallbacks {

  void onWrite(BLECharacteristic *characteristic) override {

    String command = characteristic->getValue();

    Serial.println("\n========== BLE DEBUG ==========");

    Serial.print("Raw command: [");
    Serial.print(command);
    Serial.println("]");

    Serial.print("Command length: ");
    Serial.println(command.length());

    Serial.print("HEX values: ");

    for (int i = 0; i < command.length(); i++) {
      Serial.printf("%02X ", (uint8_t)command[i]);
    }

    Serial.println();

    command.trim();
    command.toUpperCase();

    Serial.print("Processed command: [");
    Serial.print(command);
    Serial.println("]");

    if (command == "LOCK") {
      lockDevice();
    }
    else if (command == "UNLOCK") {
      unlockDevice();
    }
    else {
      Serial.println("[BLE] UNKNOWN COMMAND!");
    }

    Serial.println("===============================");
  }
};

class NotifyCallbacks : public BLECharacteristicCallbacks {
    void onSubscribe(
    BLECharacteristic *characteristic,
    ble_gap_conn_desc *desc,
    uint16_t subValue
  ) override {

    notificationsSubscribed = (subValue & 0x0001) != 0;

    Serial.print("[BLE SUBSCRIBE] Notification subscription: ");
    Serial.println(notificationsSubscribed ? "ENABLED" : "DISABLED");

    Serial.print("[BLE SUBSCRIBE] Subscription value: ");
    Serial.println(subValue);
  }
  void onStatus(
    BLECharacteristic *characteristic,
    Status status,
    uint32_t code
  ) override {

    switch (status) {

      case SUCCESS_NOTIFY:
        Serial.println("[BLE NOTIFY] SUCCESS_NOTIFY");
        break;

      case ERROR_NO_CLIENT:
        Serial.println("[BLE NOTIFY] ERROR_NO_CLIENT");
        break;

      case ERROR_NO_SUBSCRIBER:
        Serial.println("[BLE NOTIFY] ERROR_NO_SUBSCRIBER");
        break;

      case ERROR_NOTIFY_DISABLED:
        Serial.println("[BLE NOTIFY] ERROR_NOTIFY_DISABLED");
        break;

      case ERROR_GATT:
        Serial.printf(
          "[BLE NOTIFY] ERROR_GATT, code: %lu\n",
          (unsigned long)code
        );
        break;

      default:
        Serial.printf(
          "[BLE NOTIFY] Other status: %d, code: %lu\n",
          (int)status,
          (unsigned long)code
        );
        break;
    }
  }
};

// ---------------- SETUP ----------------

void setup() {

  Serial.begin(115200);

  Serial.println();
  Serial.println("========== U-LOCK STARTING ==========");

  // Initialize servo
  servo.setPeriodHertz(50);
  servo.attach(SERVO_PIN, 500, 2400);

  // Start in unlocked position
  servo.write(UNLOCK_ANGLE);

  Serial.println("[SERVO] Initialized");

  // Initialize BLE
  BLEDevice::init(DEVICE_NAME);

  BLEServer *server = BLEDevice::createServer();
  server->setCallbacks(new ServerCallbacks());

  BLEService *service = server->createService(SERVICE_UUID);

  // Write characteristic: receives LOCK / UNLOCK
  BLECharacteristic *writeCharacteristic =
      service->createCharacteristic(
        WRITE_UUID,
        BLECharacteristic::PROPERTY_WRITE
      );

  writeCharacteristic->setCallbacks(new WriteCallbacks());

  // Notify characteristic: sends status back to phone
  notifyCharacteristic =
      service->createCharacteristic(
        NOTIFY_UUID,
        BLECharacteristic::PROPERTY_NOTIFY
      );

    // Create and attach the notification descriptor.
  notifyDescriptor = new BLE2902();

  notifyCharacteristic->addDescriptor(notifyDescriptor);
  notifyCharacteristic->setCallbacks(new NotifyCallbacks());

  Serial.println("[BLE] Notification descriptor initialized.");

  // Start BLE service
  service->start();

  // Start advertising
  BLEAdvertising *advertising = BLEDevice::getAdvertising();

  advertising->addServiceUUID(SERVICE_UUID);
  advertising->setScanResponse(true);

  BLEDevice::startAdvertising();

  Serial.println("[BLE] Device name: U-LOCK");
  Serial.println("[BLE] Advertising started!");
  Serial.println("====================================");
}

// ---------------- MAIN LOOP ----------------

void loop() {

  // Restart advertising after the phone disconnects.
  if (restartAdvertising) {

    delay(500);

    BLEDevice::startAdvertising();

    Serial.println("[BLE] Advertising restarted!");

    restartAdvertising = false;
  }

  // Wait until Android enables BLE notifications.
  if (phoneConnected &&
    initialStatusPending &&
    notificationsSubscribed) {

    initialStatusPending = false;

    Serial.println("[BLE] Notification subscription detected.");

    // Send the current lock state to the phone.
    notifyLockState();
  }

  delay(20);
}