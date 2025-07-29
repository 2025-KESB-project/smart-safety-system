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

export default function VideoLogTable({ logs, activeId, onSelect }) {
  return (
    <div className="log-board">
      <h3>🎞️ 영상 로그</h3>
      <table>
        <thead>
          <tr>
            <th>날짜</th><th>시간</th><th>상태</th>
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

            const { label, className } =
              RISK_MAP[log.risk_level] || RISK_MAP.safe;
            const isActive = log.id === activeId;

            return (
              <tr
                key={log.id}
                className={[
                  className,
                  isActive ? 'active' : ''
                ].filter(Boolean).join(' ')}
                onClick={() => onSelect(log.id)}
              >
                <td>{date}</td>
                <td>{time}</td>
                <td>{label}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
