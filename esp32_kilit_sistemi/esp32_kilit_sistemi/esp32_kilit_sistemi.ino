#include <SPI.h>
#include <MFRC522.h>
#include <ESP32Servo.h>

#define RFID_SDA 5
#define RFID_RST 22

#define LED_MAVI 26
#define LED_YESIL 27
#define LED_KIRMIZI 14

#define SERVO_PIN 4

MFRC522 rfid(RFID_SDA, RFID_RST);
Servo kapiServo;

bool kameraModu = false;
unsigned long sonMaviZaman = 0;
bool maviDurum = false;

unsigned long sonKartZamani = 0;
const unsigned long kartBeklemeSuresi = 3000;

void ledleriKapat() {
  digitalWrite(LED_MAVI, LOW);
  digitalWrite(LED_YESIL, LOW);
  digitalWrite(LED_KIRMIZI, LOW);
}

void servoKapiAc() {
  Serial.println("Servo kapi aciyor");
  kapiServo.write(90);
  delay(1500);
  kapiServo.write(0);
  Serial.println("Servo kapi kapandi");
}

void komutIsle(String komut) {
  komut.trim();

  Serial.print("Python komutu geldi: ");
  Serial.println(komut);

  if (komut == "BAGLANTI_OK") {
    kameraModu = false;
    ledleriKapat();
    digitalWrite(LED_MAVI, HIGH);
  }

  else if (komut == "KAMERA_ACIK") {
    kameraModu = true;
    digitalWrite(LED_YESIL, LOW);
    digitalWrite(LED_KIRMIZI, LOW);
  }

  else if (komut == "ONAY_OK") {
    kameraModu = false;
    digitalWrite(LED_MAVI, LOW);
    digitalWrite(LED_KIRMIZI, LOW);
    digitalWrite(LED_YESIL, HIGH);
    delay(2000);
    digitalWrite(LED_YESIL, LOW);
    digitalWrite(LED_MAVI, HIGH);
  }

  else if (komut == "ONAY_RED") {
    kameraModu = false;
    digitalWrite(LED_MAVI, LOW);
    digitalWrite(LED_YESIL, LOW);
    digitalWrite(LED_KIRMIZI, HIGH);
    delay(2000);
    digitalWrite(LED_KIRMIZI, LOW);
    digitalWrite(LED_MAVI, HIGH);
  }

  else if (komut == "KAPI_AC") {
    servoKapiAc();
  }
}

void setup() {
  Serial.begin(115200);
  delay(1000);

  Serial.println("ESP32 basladi");

  SPI.begin(18, 19, 23, RFID_SDA);
  rfid.PCD_Init();
  rfid.PCD_SetAntennaGain(MFRC522::RxGain_max);

  Serial.println("RFID baslatildi");
  rfid.PCD_DumpVersionToSerial();

  pinMode(LED_MAVI, OUTPUT);
  pinMode(LED_YESIL, OUTPUT);
  pinMode(LED_KIRMIZI, OUTPUT);

  ledleriKapat();

  kapiServo.attach(SERVO_PIN);
  kapiServo.write(0);

  Serial.println("ESP32_HAZIR");
  Serial.println("Kart bekleniyor...");
}

void loop() {
  if (kameraModu) {
    if (millis() - sonMaviZaman > 300) {
      sonMaviZaman = millis();
      maviDurum = !maviDurum;
      digitalWrite(LED_MAVI, maviDurum);
    }
  }

  if (Serial.available()) {
    String komut = Serial.readStringUntil('\n');
    komutIsle(komut);
  }

  if (!rfid.PICC_IsNewCardPresent()) {
    return;
  }

  Serial.println("Kart algilandi.");

  if (!rfid.PICC_ReadCardSerial()) {
    Serial.println("Kart okunamadi.");
    return;
  }

  unsigned long simdi = millis();

  if (simdi - sonKartZamani > kartBeklemeSuresi) {
    sonKartZamani = simdi;

    Serial.println("KART_OKUNDU");

    Serial.print("Kart UID: ");
    for (byte i = 0; i < rfid.uid.size; i++) {
      Serial.print(rfid.uid.uidByte[i], HEX);
      Serial.print(" ");
    }
    Serial.println();
  }

  rfid.PICC_HaltA();
  rfid.PCD_StopCrypto1();
}