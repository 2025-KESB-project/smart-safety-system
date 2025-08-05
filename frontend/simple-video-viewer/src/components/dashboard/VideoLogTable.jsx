// src/pages/Dashboard/VideoLogTable.jsx
import React from 'react';
import './VideoLogTable.css';

// event_type → 한글 라벨 매핑
const EVENT_LABEL = {
  LOG_CRITICAL_FALLING:   '넘어짐 감지',
  LOG_CRITICAL_SENSOR:    '센서 경고',
  LOG_INTRUSION_SLOWDOWN: '위험 구역 침입',
  LOG_CROUCHING_WARN:     '웅크린 자세 감지',
  LOG_LOTO_ACTIVE:        '위험구역 침입',
  LOG_MAINTENANCE_SAFE:   '정비 모드 안전',
  LOG_NORMAL_OPERATION:   '안전',
  // 필요하면 여기 더 추가...
};

// event_type → 위험도 클래스 매핑
const RISK_MAP = {
  LOG_CRITICAL_FALLING:   'status-critical',
  LOG_CRITICAL_SENSOR:    'status-critical',
  LOG_INTRUSION_SLOWDOWN: 'status-high',
  LOG_CROUCHING_WARN:     'status-medium',
  LOG_LOTO_ACTIVE:        'status-high',
  LOG_MAINTENANCE_SAFE:   'status-safe',
  LOG_NORMAL_OPERATION:   'status-safe',
};

export default function VideoLogTable({ logs, activeId, onSelect }) {
  return (
    <div className="log-board">
      <h3>🎞️ 영상 로그</h3>
      <div className="table-wrapper">
        <table>
          <thead>
            <tr>
              <th>일시</th>
              <th>감지 인원</th>
              <th>이유</th>
            </tr>
          </thead>
          <tbody>
            {logs.map((log, idx) => {
              // 1) 일시 포맷
              const dt = new Date(log.timestamp);
              const dateTime = dt.toLocaleString('ko-KR', {
                year: 'numeric', month: '2-digit', day: '2-digit',
                hour: '2-digit', minute: '2-digit',
              });

              // 2) 감지 인원 계산
              //    - Zone Intrusion 데이터가 details.zone_count 등에 담겨 왔다고 가정
              const detected = log.details?.zone_count != null
                ? log.details.zone_count
                : log.event_type === 'LOG_CRITICAL_FALLING'
                  ? 1
                  : '-';

              // 3) 이유 텍스트
              const reason = EVENT_LABEL[log.event_type] 
                || log.details?.reason 
                || '-';

              // 4) 클래스 결정
              const className = RISK_MAP[log.event_type] || 'status-safe';

              // 5) key
              const key = log.id ?? `${log.timestamp}-${idx}`;

              return (
                <tr
                  key={key}
                  className={[className, log.id === activeId && 'active']
                              .filter(Boolean)
                              .join(' ')}
                  onClick={() => onSelect(log.id)}
                >
                  <td className="date-cell">{dateTime}</td>
                  <td>{detected}</td>
                  <td>{reason}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
