#include <Wire.h>

#define I2C_SLAVE_ADDR 0x42

uint16_t ber = 1;
unsigned long baudrate = 9600;

void setup() {
  Serial.begin(9600);
  Serial.println("Mega I2C-Slave mit Bitfehler-Injektion");

  Serial1.begin(baudrate);   
  Serial2.begin(baudrate);   

  Wire.begin(I2C_SLAVE_ADDR);
  Wire.onReceive(receiveConfig);

  randomSeed(analogRead(0));
}


byte injectBitErrors(byte b) {
  for (int i = 0; i < 8; i++) {
    if (random(65536) < ber) {
      b ^= (1 << i);
    }
  }
  return b;
}

// Empfang der Konfiguration über I2C
void receiveConfig(int numBytes) {
  if (numBytes >= 6) {
    uint8_t low = Wire.read();
    uint8_t high = Wire.read();
    ber = (high << 8) | low;

    uint8_t b0 = Wire.read();
    uint8_t b1 = Wire.read();
    uint8_t b2 = Wire.read();
    uint8_t b3 = Wire.read();
    baudrate = ((unsigned long)b3 << 24) | ((unsigned long)b2 << 16) | ((unsigned long)b1 << 8) | b0;

    Serial.print("Neue BER: ");
    Serial.println(ber);
    Serial.print("Neue Baudrate: ");
    Serial.println(baudrate);


    Serial1.end();
    Serial2.end();
    delay(100);
    Serial1.begin(baudrate);
    Serial2.begin(baudrate);
  }
}

void loop() {
  if (Serial1.available()) {
    Serial2.write(injectBitErrors(Serial1.read()));
  }
  if (Serial2.available()) {
    Serial1.write(injectBitErrors(Serial2.read()));
  }
}