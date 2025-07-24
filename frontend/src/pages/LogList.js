
import React, { useState, useEffect } from 'react';

// 이 컴포넌트는 오직 "과거 로그를 불러와서 목록으로 보여주는" 역할만 합니다.
function LogList() {
  // 1. "기억 장치" 만들기
  // logs: 서버에서 불러온 과거 로그들을 저장할 배열
  // error: 통신 중 에러가 발생하면 에러 메시지를 저장
  const [logs, setLogs] = useState([]);
  const [error, setError] = useState(null);

  // 2. "자동 실행 로봇" 설정
  // 이 컴포넌트가 화면에 처음 나타날 때, 딱 한 번만 실행됩니다.
  useEffect(() => {
    // 데이터를 불러오는 함수를 정의합니다.
    const fetchPastLogs = async () => {
      try {
        // FastAPI 서버의 /api/events 엔드포인트에 데이터를 요청합니다.
        const response = await fetch('http://localhost:8000/api/events?limit=50');
        
        // 응답이 성공적이지 않으면 에러를 발생시킵니다.
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        // 응답받은 JSON 데이터를 JavaScript 객체 배열로 변환합니다.
        const data = await response.json();
        
        // 성공적으로 받아온 데이터로 logs 상태를 업데이트합니다.
        setLogs(data);

      } catch (e) {
        // 에러가 발생하면 error 상태에 에러 메시지를 저장합니다.
        console.error("과거 로그를 불러오는 중 에러 발생:", e);
        setError(e.message);
      }
    };

    // 위에서 정의한 데이터 불러오기 함수를 실행합니다.
    fetchPastLogs();

  }, []); // [] : 처음 한 번만 실행

  // 3. 화면에 보여줄 내용 그리기
  
  // 에러가 발생했을 경우, 에러 메시지를 보여줍니다.
  if (error) {
    return <div style={{ color: 'red' }}>에러: {error}</div>;
  }

  // 정상적인 경우, 로그 목록을 보여줍니다.
  return (
    <div className="log-list-container">
      <h2>과거 이벤트 로그 (최신 50개)</h2>
      <div className="log-list">
        {logs.length > 0 ? (
          logs.map((log) => (
            <p key={log.id} className={`log-message log-${log.risk_level}`}>
              {/* ISO 형식의 timestamp를 보기 좋은 형식으로 변환 */}
              <strong>[{new Date(log.timestamp).toLocaleString()}]</strong>
              <span> - {log.event_type} (위험도: {log.risk_level})</span>
              <span style={{ display: 'block', fontSize: '0.8em', opacity: 0.8 }}>
                &nbsp;&nbsp;상세: {log.details.reason || JSON.stringify(log.details)}
              </span>
            </p>
          ))
        ) : (
          <p>표시할 과거 로그가 없습니다.</p>
        )}
      </div>
    </div>
  );
}

export default LogList;
