
/*

  Multiple Serial test

  Receives from the main serial port, sends to the others.

  Receives from serial port 1, sends to the main serial (Serial 0).

  This example works only with boards with more than one serial like Arduino Mega, Due, Zero etc.

  The circuit:

  - any serial device attached to Serial port 1

  - Serial Monitor open on Serial port 0

  created 30 Dec 2008

  modified 20 May 2012

  by Tom Igoe & Jed Roach

  modified 27 Nov 2015

  by Arturo Guadalupi

  This example code is in the public domain.

*/
int probs = 1000;

byte maybe_flip_a_bit(byte a)
{
  for(int i = 0; i < 8; i++)
  {
    if(random(65536) < 33) //ceil(65536 * 0,0005) = 33
    {
      // FLIP IT!
      a ^= (1<<i);
    }
  }
  return a;
}



void setup() {

  // initialize both serial ports:

  Serial.begin(9600);

  Serial1.begin(9600);
}

void loop() {

  // read from port 1, send to port 0:

  if (Serial1.available()) {

    int inByte = Serial1.read();

    Serial.write(maybe_flip_a_bit(inByte));

  }

  // read from port 0, send to port 1:

  if (Serial.available()) {

    int inByte = Serial.read();

    Serial1.write(maybe_flip_a_bit(inByte));

  }
}