const byte ENA   = 9;    // PWM
const byte IN1   = 8;
const byte IN2   = 7;

void initFastPWM31k() {
  TCCR1A = _BV(COM1A1) | _BV(WGM10);
  TCCR1B = _BV(WGM12)  | _BV(CS10);
}

void setup() {
  Serial.begin(9600);

  pinMode(ENA, OUTPUT);
  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);

  digitalWrite(IN1, HIGH);
  digitalWrite(IN2, LOW);

  analogWrite(ENA, 0);

  Serial.println("준비완료. speed command를 기다리는 중...");
}

void loop() {
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    if (cmd.startsWith("s")) {
      int pwmVal = constrain(cmd.substring(1).toInt(), 0, 255);
      analogWrite(ENA, pwmVal);
      Serial.print("Speed set to: ");
      Serial.println(pwmVal);
    }
  }
}
