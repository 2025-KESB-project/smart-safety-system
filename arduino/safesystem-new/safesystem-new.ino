// 모터 제어 핀
const int MOTOR_ENA = 9;
const int MOTOR_IN1 = 8;
const int MOTOR_IN2 = 7;

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

  // 모터 제어 핀 초기화 (기존 시스템)
  pinMode(MOTOR_ENA, OUTPUT);
  pinMode(MOTOR_IN1, OUTPUT);
  pinMode(MOTOR_IN2, OUTPUT);
  
  // 모터는 기본적으로 비활성화 상태로 시작
  digitalWrite(MOTOR_ENA, HIGH); // HIGH일 때 비활성화라고 가정

  // PIR 센서 핀 초기화
  pinMode(PIR_PIN, INPUT);

  Serial.println("Arduino is ready.");
}

// --- 메인 루프 ---
void loop() {
  // 1. 기존 모터 제어 로직 (여기에 구현)
  motor();

  // 2. 센서 데이터 처리
  handle_sensors();

  // 3. 주기적으로 데이터 전송
  send_data_periodically();
}

// --- 함수 정의 ---

/*
 * @brief 기존 모터 제어 관련 함수들 (예시)
 */
void motor() {
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    if (cmd.startsWith("s")) {
      int pwmVal = cmd.substring(1).toInt();
      // 속도 값이 0보다 크면 정방향으로 회전
      if (pwmVal > 0) {
        pwmVal = constrain(pwmVal, 0, 255);
        digitalWrite(MOTOR_IN1, HIGH);
        digitalWrite(MOTOR_IN2, LOW);
        analogWrite(MOTOR_ENA, pwmVal);

        Serial.print("Speed set to: ");
        Serial.println(pwmVal);
      }
      else {
        digitalWrite(MOTOR_IN1, LOW);
        digitalWrite(MOTOR_IN2, LOW);
        analogWrite(MOTOR_ENA, 0);

        Serial.println("Motor stopped");
      }
    }
  }
}


/*
 * @brief 모터 제어 시 발생하는 고주파 소음을 제거합니다.
 */
void initFastPWM31k() {
  TCCR1A = _BV(COM1A1) | _BV(WGM10);
  TCCR1B = _BV(WGM12)  | _BV(CS10);
}


/*
 * @brief 모든 센서의 현재 상태를 읽고 처리합니다.
 */
void handle_sensors() {
  // PIR 센서 상태 읽기
  pir_state = digitalRead(PIR_PIN);

  // 상태 변화가 있을 때만 시리얼로 즉시 전송 (디버깅용)
  if (pir_state != last_pir_state) {
    Serial.print("PIR state changed to: ");
    Serial.println(pir_state);
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
    
    // PIR 센서 데이터 전송
    send_pir_data();
    
    // 여기에 다른 센서 데이터 전송 함수 추가 가능
    // send_ultrasonic_data();
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

/*
 * @brief (확장용) 초음파 센서 데이터를 JSON 형식으로 출력하는 함수 예시
 */
/*
void send_ultrasonic_data() {
  // 여기에 초음파 센서 거리 측정 로직 추가
  int distance = 100; // 예시 값
  Serial.print("{\"type\": \"ULTRASONIC\", \"value\": ");
  Serial.print(distance);
  Serial.println("}");
}
*/
