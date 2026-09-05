#include <Arduino.h>
#include <WiFi.h>
#include <WebServer.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include <ESP32Servo.h>
#include <ArduinoJson.h>

// --- OLED SSD1306 DISPLAY (I2C) ---
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, -1);

// --- GY-521 (MPU6050) ACCELEROMETER / GYROSCOPE ---
Adafruit_MPU6050 mpu;
bool mpuAvailable = false;

// --- SG90 MICRO SERVO (TILT / POURING MECHANISM) ---
Servo sg90;
const int PIN_SERVO_SG90 = 13;

// --- HC-SR04 ULTRASONIC SENSOR ---
const int PIN_TRIG = 5;
const int PIN_ECHO = 18;

// --- GY-MAX9814 MICROPHONE (ANALOG OUT) ---
// Dedicated ADC1 input pin on ESP32 (safe to use while Wi-Fi is active)
const int PIN_MIC_OUT = 35;

// --- BUZZER / SPEAKER (DELAY ALARM) ---
const int PIN_BUZZER = 19;

// --- BASE DOCK SWITCH (MECHANICAL / BUTTON INPUT) ---
const int PIN_BTN_BASE = 4;

WebServer server(80);

// --- ROUND / SESSION STATE ---
#define MAX_PARTICIPANTS 10
String participants[MAX_PARTICIPANTS] = {"Nahuel", "Santi", "Flor", "Mati"};
int totalParticipants = 4;
int currentTurn = 0;

bool mateOnDock = true;
bool delayAlarmActive = false;
unsigned long liftedTimestamp = 0;
const unsigned long DELAY_TIMEOUT_MS = 15000; // 15s for quick simulation test (300000 for 5 min in prod)

int currentTiltAngle = 0;

// Read distance in centimeters via HC-SR04
float readDistanceCm() {
  digitalWrite(PIN_TRIG, LOW);
  delayMicroseconds(2);
  digitalWrite(PIN_TRIG, HIGH);
  delayMicroseconds(10);
  digitalWrite(PIN_TRIG, LOW);
  long duration = pulseIn(PIN_ECHO, HIGH, 25000);
  if (duration == 0) return 999.0;
  return duration * 0.034 / 2.0;
}

// Read peak-to-peak microphone amplitude from GY-MAX9814
int readMicAmplitude(int samples = 50) {
  int minVal = 4095;
  int maxVal = 0;
  for (int i = 0; i < samples; i++) {
    int v = analogRead(PIN_MIC_OUT);
    if (v < minVal) minVal = v;
    if (v > maxVal) maxVal = v;
    delayMicroseconds(100);
  }
  return (maxVal - minVal);
}

void updateDisplay(const String& line1, const String& line2 = "") {
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);

  display.setCursor(0, 0);
  display.print("= Ronda de Mate =");

  display.setCursor(0, 16);
  display.setTextSize(2);
  display.print((totalParticipants > 0) ? participants[currentTurn] : "Nadie");

  display.setTextSize(1);
  display.setCursor(0, 40);
  display.print(line1);

  if (line2.length() > 0) {
    display.setCursor(0, 52);
    display.print(line2);
  }

  display.display();
}

void nextTurn() {
  if (totalParticipants > 0) {
    currentTurn = (currentTurn + 1) % totalParticipants;
    Serial.printf("[MatePlatform] Proximo turno: %s\n", participants[currentTurn].c_str());
    updateDisplay("Turno de:", participants[currentTurn]);
  }
}

void removeParticipant(const String& name) {
  int idx = -1;
  for (int i = 0; i < totalParticipants; i++) {
    if (participants[i].equalsIgnoreCase(name)) {
      idx = i;
      break;
    }
  }

  if (idx != -1) {
    Serial.printf("[MatePlatform] '%s' dijo gracias! Queda afuera de la ronda.\n", participants[idx].c_str());
    for (int i = idx; i < totalParticipants - 1; i++) {
      participants[i] = participants[i + 1];
    }
    totalParticipants--;
    if (currentTurn >= totalParticipants) currentTurn = 0;
    updateDisplay("Dijo gracias!", "Chau " + name);
  }
}

// Servo tilt angle helper
void setTiltAngle(int targetAngle) {
  currentTiltAngle = constrain(targetAngle, 0, 90);
  sg90.write(currentTiltAngle);
  Serial.printf("[SG90] Inclinacion ajustada a: %d grados\n", currentTiltAngle);
}

// --- HTTP ENDPOINTS (100% IN ENGLISH) ---
void handleStatus() {
  JsonDocument doc;
  doc["turn"] = (totalParticipants > 0) ? participants[currentTurn] : "None";
  doc["isDocked"] = mateOnDock;
  doc["delayAlarm"] = delayAlarmActive;
  doc["distance_cm"] = readDistanceCm();
  doc["mic_amplitude"] = readMicAmplitude(20);
  doc["tilt_angle"] = currentTiltAngle;

  if (mpuAvailable) {
    sensors_event_t a, g, temp;
    mpu.getEvent(&a, &g, &temp);
    doc["accel_x"] = a.acceleration.x;
    doc["accel_y"] = a.acceleration.y;
    doc["accel_z"] = a.acceleration.z;
  }

  JsonArray arr = doc["participants"].to<JsonArray>();
  for (int i = 0; i < totalParticipants; i++) {
    arr.add(participants[i]);
  }

  String res;
  serializeJson(doc, res);
  server.send(200, "application/json", res);
}

// POST /round/config -> {"names": ["Nahuel", "Santi"]}
void handleConfigRound() {
  if (!server.hasArg("plain")) {
    server.send(400, "text/plain", "Missing JSON body");
    return;
  }
  JsonDocument doc;
  DeserializationError err = deserializeJson(doc, server.arg("plain"));
  if (err) {
    server.send(400, "text/plain", "Invalid JSON");
    return;
  }

  JsonArray names = doc["names"];
  totalParticipants = 0;
  for (JsonVariant v : names) {
    if (totalParticipants < MAX_PARTICIPANTS) {
      participants[totalParticipants++] = v.as<String>();
    }
  }
  currentTurn = 0;
  updateDisplay("Ronda lista!", participants[currentTurn]);
  server.send(200, "application/json", "{\"status\":\"ok\"}");
}

// POST /round/thanks -> ?name=Nahuel or body
void handleThanks() {
  String name = server.arg("name");
  if (name.length() == 0 && totalParticipants > 0) {
    name = participants[currentTurn];
  }
  removeParticipant(name);
  server.send(200, "application/json", "{\"status\":\"removed\",\"name\":\"" + name + "\"}");
}

// POST /round/next
void handleNextTurn() {
  nextTurn();
  server.send(200, "application/json", "{\"status\":\"ok\",\"turn\":\"" + ((totalParticipants > 0) ? participants[currentTurn] : "") + "\"}");
}

// POST /servo/tilt?angle=45
void handleServoTilt() {
  String angleStr = server.arg("angle");
  int ang = angleStr.length() > 0 ? angleStr.toInt() : 45;
  setTiltAngle(ang);
  server.send(200, "application/json", "{\"status\":\"ok\",\"angle\":" + String(ang) + "}");
}

void setup() {
  Serial.begin(115200);

  pinMode(PIN_BTN_BASE, INPUT_PULLUP);
  pinMode(PIN_TRIG, OUTPUT);
  pinMode(PIN_ECHO, INPUT);
  pinMode(PIN_BUZZER, OUTPUT);
  pinMode(PIN_MIC_OUT, INPUT);
  digitalWrite(PIN_BUZZER, LOW);

  // Initialize SG90 servo
  sg90.attach(PIN_SERVO_SG90);
  setTiltAngle(0);

  // Initialize I2C bus (OLED & GY-521)
  Wire.begin(21, 22);

  if (display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {
    updateDisplay("Iniciando...", "Conectando WiFi");
  }

  // Initialize GY-521 accelerometer / gyroscope
  if (mpu.begin()) {
    mpuAvailable = true;
    mpu.setAccelerometerRange(MPU6050_RANGE_8_G);
    Serial.println("[GY-521] MPU6050 initialized.");
  } else {
    Serial.println("[GY-521] MPU6050 not detected.");
  }

  // Connect Wi-Fi
  WiFi.begin("Wokwi-GUEST", "");
  Serial.println("Connecting to Wi-Fi...");
  while (WiFi.status() != WL_CONNECTED) {
    delay(200);
    Serial.print(".");
  }
  Serial.printf("\nWi-Fi Connected! IP: %s\n", WiFi.localIP().toString().c_str());

  // Web server routes (pure English endpoints)
  server.on("/status", HTTP_GET, handleStatus);
  server.on("/round/config", HTTP_POST, handleConfigRound);
  server.on("/round/thanks", HTTP_POST, handleThanks);
  server.on("/round/next", HTTP_POST, handleNextTurn);
  server.on("/servo/tilt", HTTP_POST, handleServoTilt);
  server.on("/servo/tilt", HTTP_GET, handleServoTilt);
  server.begin();

  updateDisplay("Turno de:", participants[currentTurn]);
}

void loop() {
  server.handleClient();

  // 1. Detect dock presence (LOW = docked, HIGH = lifted)
  bool docked = (digitalRead(PIN_BTN_BASE) == LOW);

  if (mateOnDock && !docked) {
    // Mate lifted to drink
    mateOnDock = false;
    liftedTimestamp = millis();
    delayAlarmActive = false;
    Serial.printf("[MatePlatform] %s esta tomando.\n", participants[currentTurn].c_str());
    updateDisplay("Tomando...", participants[currentTurn]);

    // Tilt servo to 45 degrees
    setTiltAngle(45);
  }
  else if (!mateOnDock && docked) {
    // Mate placed back on dock: reset angle and advance turn
    mateOnDock = true;
    delayAlarmActive = false;
    noTone(PIN_BUZZER);
    setTiltAngle(0);
    Serial.println("[MatePlatform] Mate devuelto a la base.");
    nextTurn();
    delay(400); // Debounce
  }

  // 2. Alarm trigger if mate is held past timeout
  if (!mateOnDock && !delayAlarmActive && (millis() - liftedTimestamp > DELAY_TIMEOUT_MS)) {
    delayAlarmActive = true;
    tone(PIN_BUZZER, 1000); // Sound alarm buzzer
    Serial.printf("[MatePlatform] ALARMA: %s se colgo con el mate!\n", participants[currentTurn].c_str());
    updateDisplay("ALARMA!", "Larga el mate!!");
  }

  delay(50);
}
