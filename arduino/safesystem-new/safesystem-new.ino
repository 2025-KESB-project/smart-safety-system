// 모터 제어 핀
const int MOTOR_ENA = 9;
const int MOTOR_IN1 = 8;
const int MOTOR_IN2 = 7;

// 전원 릴레이 제어 핀
const int RELAY_PIN = 6;

// 피에조 부저 핀
const int BUZZER_PIN = 11;

// 초음파 센서 (거리 측정)
const int TRIG = 5;
const int ECHO = 4;

// 주기적 데이터 전송을 위한 타이머 변수
unsigned long last_send_time = 0;
const long send_interval = 200; // 0.2초마다 데이터 전송

void setup() {
  Serial.begin(9600);

  pinMode(MOTOR_ENA, OUTPUT);
  pinMode(MOTOR_IN1, OUTPUT);
  pinMode(MOTOR_IN2, OUTPUT);
  digitalWrite(MOTOR_IN1, LOW);
  digitalWrite(MOTOR_IN2, LOW);
  analogWrite(MOTOR_ENA, 0);

  pinMode(RELAY_PIN, OUTPUT);
  digitalWrite(RELAY_PIN, HIGH); // 기본적으로 전원 ON

  pinMode(BUZZER_PIN, OUTPUT);
  noTone(BUZZER_PIN);

  while (!Serial) {
    ;
  }
  Serial.println("Arduino is ready. Waiting for commands.");
}

void loop() {
  // 1. 시리얼 명령을 받아 모터, 릴레이, 부저 제어
  handle_serial_commands();

  // 2. 주기적으로 센서 데이터 전송
  send_data_periodically();
}

/**
 * @brief 시리얼 명령을 처리합니다.
 * s<0-255>: 모터 속도 제어
 * p<0-1>: 릴레이 전원 제어
 * b<0-1>: 부저 제어
 */
void handle_serial_commands() {
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();

    if (cmd.startsWith("s")) {
      int pwmVal = cmd.substring(1).toInt();
      pwmVal = constrain(pwmVal, 0, 255);
      if (pwmVal > 0) {
        digitalWrite(MOTOR_IN1, HIGH);
        digitalWrite(MOTOR_IN2, LOW);
      } else {
        digitalWrite(MOTOR_IN1, LOW);
        digitalWrite(MOTOR_IN2, LOW);
      }
      analogWrite(MOTOR_ENA, pwmVal);
      // Serial.print("Log: Motor speed set to ");
      // Serial.println(pwmVal);
    } 
    else if (cmd.startsWith("p")) {
      int power_state = cmd.substring(1).toInt();
      if (power_state == 0) {
        digitalWrite(RELAY_PIN, LOW);
        // Serial.println("Log: Power Relay OFF");
      } else {
        digitalWrite(RELAY_PIN, HIGH);
        // Serial.println("Log: Power Relay ON");
      }
    }
    else if (cmd.startsWith("b")) {
      int buzzer_state = cmd.substring(1).toInt();
      if (buzzer_state == 1) {
        tone(BUZZER_PIN, 1000);
        // Serial.println("Log: Buzzer ON");
      } else {
        noTone(BUZZER_PIN);
        // Serial.println("Log: Buzzer OFF");
      }
    }
  }
}

/**
 * @brief 초음파 센서 거리를 측정합니다.
 */
long readUltrasonicSensor() {
  digitalWrite(TRIG, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG, LOW);
  long duration = pulseIn(ECHO, HIGH, 25000);
  long dist = duration * 0.034 / 2;
  return dist > 0 ? dist : 999; // 0이면 오류로 간주하고 큰 값 반환 (오류를 일으키는 것으로 예상됨)
}

/**
 * @brief 주기적으로 센서 데이터를 JSON 형식으로 전송합니다.
 */
void send_data_periodically() {
  unsigned long current_time = millis();
  if (current_time - last_send_time >= send_interval) {
    last_send_time = current_time;
    
    long distance = readUltrasonicSensor();

    // JSON 형식: {"ultrasonic": <dist>}
    Serial.print("{\"ultrasonic\": ");
    Serial.print(distance);
    Serial.println("}");
  }
}