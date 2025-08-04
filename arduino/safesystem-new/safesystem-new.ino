// 모터 드라이버 제어 핀 (SpeedController용)
const int MOTOR_ENA = 9;
const int MOTOR_IN1 = 8;
const int MOTOR_IN2 = 7;

// 릴레이 모듈 제어 핀 (PowerController용)
const int RELAY_PIN = 10;

// PIR 센서 핀
const int PIR_PIN = 2;

// --- 상태 변수 ---
int pir_state = LOW;
int last_pir_state = LOW;

void setup() {
  Serial.begin(9600);

  pinMode(MOTOR_ENA, OUTPUT);
  pinMode(MOTOR_IN1, OUTPUT);
  pinMode(MOTOR_IN2, OUTPUT);
  digitalWrite(MOTOR_ENA, LOW);

  pinMode(RELAY_PIN, OUTPUT);
  digitalWrite(RELAY_PIN, LOW);

  pinMode(PIR_PIN, INPUT);

  Serial.println("Arduino is ready.");
}

void loop() {
  handle_serial_commands();
  handle_sensors();
}

void handle_serial_commands() {
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    
    // PowerController를 위한 전원 제어 명령어 (p0, p1)
    if (cmd.startsWith("p")) {
      int state = cmd.substring(1).toInt();
      if (state == 1) {
        digitalWrite(RELAY_PIN, HIGH); // 릴레이 ON (작동불가)
        digitalWrite(MOTOR_IN1, LOW);
        digitalWrite(MOTOR_IN2, LOW);
        analogWrite(MOTOR_ENA, 0); // 모터도 같이 OFF
        Serial.println("Command: p1 -> Power ON (Relay HIGH)");
      } else {
        digitalWrite(RELAY_PIN, LOW);  // 릴레이 OFF (작동가능)
        Serial.println("Command: p0 -> Power OFF");
      }
    }
    // SpeedController를 위한 모터 속도 제어 명령어 (s0 ~ s255)
    else if (cmd.startsWith("s")) {
      int pwmVal = cmd.substring(1).toInt();
      if (pwmVal > 0) {
        pwmVal = constrain(pwmVal, 0, 255);
        digitalWrite(MOTOR_IN1, HIGH);
        digitalWrite(MOTOR_IN2, LOW);
        analogWrite(MOTOR_ENA, pwmVal);
        Serial.print("Command: s -> Speed set to: ");
        Serial.println(pwmVal);
      } else {
        digitalWrite(MOTOR_IN1, LOW);
        digitalWrite(MOTOR_IN2, LOW);
        analogWrite(MOTOR_ENA, 0);
        Serial.println("Command: s -> Motor stopped");
      }
    }
  }
}

/*
 * @brief 모든 센서의 현재 상태를 읽고, 상태에 변화가 있을 때만 데이터를 전송합니다.
 */
void handle_sensors() {
  // 1. PIR 센서 상태 읽기
  pir_state = digitalRead(PIR_PIN);

  // 상태 변화가 있을 때만 시리얼로 즉시 전송
  if (pir_state != last_pir_state) {
    send_pir_data();
    last_pir_state = pir_state;
  }
}

void send_pir_data() {
  Serial.print("{\"type\": \"PIR\", \"value\": ");
  Serial.print(pir_state);
  Serial.println("}");
}