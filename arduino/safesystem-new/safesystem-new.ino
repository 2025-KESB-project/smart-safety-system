// 모터 드라이버 제어 핀 (SpeedController용)
const int MOTOR_ENA = 9;
const int MOTOR_IN1 = 8;
const int MOTOR_IN2 = 7;

// 릴레이 모듈 제어 핀 (PowerController용)
const int RELAY_PIN = 10;

// PIR 센서 핀
const int PIR_PIN = 2;

// PIR 센서 상태
int pir_state = LOW;
int last_pir_state = LOW;

// 타이머 변수 (주기적인 데이터 전송용)
unsigned long last_send_time = 0;
const long send_interval = 1000; // 1초마다 데이터 전송


void setup() {
  // 시리얼 통신 시작 (Python과 통신용)
  Serial.begin(9600);

  // 모터 드라이버 핀 초기화
  pinMode(MOTOR_ENA, OUTPUT);
  pinMode(MOTOR_IN1, OUTPUT);
  pinMode(MOTOR_IN2, OUTPUT);
  digitalWrite(MOTOR_ENA, LOW); // 모터는 기본 비활성화

  // 릴레이 핀 초기화
  pinMode(RELAY_PIN, OUTPUT);
  digitalWrite(RELAY_PIN, LOW); // 릴레이는 기본 OFF 상태

  // PIR 센서 핀 초기화
  pinMode(PIR_PIN, INPUT);

  Serial.println("Arduino is ready. Relay and Motor control enabled.");
}

// --- 메인 루프 ---
void loop() {
  // 1. Python으로부터 오는 시리얼 명령어 처리
  handle_serial_commands();

  // 2. 센서 데이터 처리
  handle_sensors();

  // 3. 주기적으로 데이터 전송
  send_data_periodically();
}

// --- 함수 정의 ---

/*
 * @brief Python으로부터 받은 시리얼 명령어를 처리합니다.
 *        - 속도 제어(s), 전원 제어(p) 명령어를 모두 처리합니다.
 */
void handle_serial_commands() {
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim(); // 혹시 모를 공백 제거

    // PowerController를 위한 전원 제어 명령어 (p0, p1)
    if (cmd.startsWith("p")) {
      int state = cmd.substring(1).toInt();
      if (state == 1) {
        digitalWrite(RELAY_PIN, HIGH); // 릴레이 ON
        Serial.println("Command: p1 -> Power ON (Relay HIGH)");
      } else {
        digitalWrite(RELAY_PIN, LOW);  // 릴레이 OFF
        Serial.println("Command: p0 -> Power OFF (Relay LOW)");
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
 * @brief 모든 센서의 현재 상태를 읽고 처리합니다.
 */
void handle_sensors() {
  // PIR 센서 상태 읽기
  pir_state = digitalRead(PIR_PIN);

  // 상태 변화가 있을 때만 시리얼로 즉시 전송 (디버깅용)
  if (pir_state != last_pir_state) {
    // Serial.print("PIR state changed to: ");
    // Serial.println(pir_state);
    send_pir_data(); // 상태 변경 시 즉시 데이터 전송
    last_pir_state = pir_state;
  }
}

/*
 * @brief 주기적으로 통합된 센서 데이터를 JSON 형식으로 전송합니다.
 */
void send_data_periodically() {
  unsigned long current_time = millis();
  if (current_time - last_send_time >= send_interval) {
    last_send_time = current_time;
    send_pir_data();
  }
} 

/*
 * @brief PIR 센서 데이터를 JSON 형식으로 시리얼 포트에 출력합니다.
 */
void send_pir_data() {
  // JSON 형식: {"type": "PIR", "value": 0 또는 1}
  Serial.print("{\"type\": \"PIR\", \"value\": ");
  Serial.print(pir_state);
  Serial.println("}");
}

