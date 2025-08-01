import React from 'react';
import './VideoLogTable.css';

const RISK_MAP = {
  safe: {
    label: '✔️ 안전',
    className: 'status-safe'
  },
  medium: {
    label: '⚠️ 중간 위험',
    className: 'status-medium'
  },
  high: {
    label: '⚠️🛑 고위험',
    className: 'status-high'
  },
  critical: {
    label: '🚨 치명적 위험',
    className: 'status-critical'
  }
};

// 이벤트 타입 코드 → 라벨 및 아이콘 매핑
const EVENT_TYPE_MAP = {
  LOG_SAFE:      { label: '안전 이벤트',        icon: '✔️' },
  LOG_MEDIUM:    { label: '중간 위험 이벤트',    icon: '⚠️' },
  LOG_HIGH_RISK: { label: '고위험 이벤트',     icon: '⚠️🛑' },
  LOG_CRITICAL:  { label: '치명적 위험 이벤트', icon: '🚨' },
  // 필요시 추가...
};

// reason 코드 → 한글 라벨 매핑
const REASON_MAP = {
  person_in_danger_zone: '위험 구역 진입',
  equipment_failure:     '장비 고장',
  unauthorized_access:   '무단 접근',
  // 필요시 추가...
};

export default function VideoLogTable({ logs, activeId, onSelect }) {
  return (
    <div className="log-board">
      <h3>🎞️ 영상 로그</h3>
      <div className="table-wrapper">
        <table>
          <thead>
            <tr>
              <th>날짜</th>
              <th>시간</th>
              <th>상태</th>
              <th>이벤트 유형</th>
              <th>감지 인원</th>
              <th>이유</th>
            </tr>
          </thead>
          <tbody>
            {logs.map(log => {
              const dt = new Date(log.timestamp);
              const date = dt.toLocaleDateString('ko-KR');
              const time = dt.toLocaleTimeString('en-US', {
                hour12: false,
                hour: '2-digit',
                minute: '2-digit'
              });

              // risk_level 키를 소문자로 정규화
              const riskKey = String(log.risk_level || '').toLowerCase();
              const { label, className } =
                RISK_MAP[riskKey] || RISK_MAP.safe;

              // 이벤트 타입 매핑
              const evt = EVENT_TYPE_MAP[log.event_type] || { label: log.event_type, icon: '' };

              // 리즌 매핑
              const reasonLabel = REASON_MAP[log.details?.reason] || log.details?.reason || '-';

              const isActive = log.id === activeId;

              return (
                <tr
                  key={log.id}
                  className={[className, isActive ? 'active' : '']
                    .filter(Boolean)
                    .join(' ')}
                  onClick={() => onSelect(log.id)}
                >
                  <td>{date}</td>
                  <td>{time}</td>
                  <td>{label}</td>
                  <td>{evt.icon} {evt.label}</td>
                  <td>{log.details?.detected_persons ?? '-'}</td>
                  <td>{reasonLabel}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}