import React from 'react';
import './VideoLogTable.css';

// event_type → 한글 라벨 매핑 (후비용)
const EVENT_LABEL = {
  LOG_CRITICAL_FALLING:   '넘어짐 감지',
  LOG_CRITICAL_SENSOR:    '센서 경고',
  LOG_INTRUSION_SLOWDOWN: '위험 구역 침입',
  LOG_CROUCHING_WARN:     '웅크린 자세 감지',
  LOG_LOTO_ACTIVE:        'LOTO ACTIVE',
  LOG_MAINTENANCE_SAFE:   '정비 모드 안전',
  LOG_NORMAL_OPERATION:   '안전',
};

// operation_mode → 한글 라벨 매핑 (신규)
const MODE_LABEL = {
  AUTOMATIC: '운전 모드',
  MAINTENANCE: '정비 모드',
  INACTIVE: '시스템 정지',
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

export default function VideoLogTable({ className, logs, activeId, onSelect }) {
  return (
    <div className={className}> {/* 받은 className을 적용 */}
      <h3>🎞️ 영상 로그</h3>
      <div className="table-wrapper">
        <table>
          <thead>
            <tr>
              <th>일시</th>
              <th>동작 모드</th>
              <th>상세 내용</th>
            </tr>
          </thead>
          <tbody>
            {logs.map((log, idx) => {
              // 1) 일시 포맷
              const dt = new Date(log.timestamp);
              const month = String(dt.getMonth() + 1).padStart(2, '0');
              const day = String(dt.getDate()).padStart(2, '0');
              const hours = String(dt.getHours()).padStart(2, '0');
              const minutes = String(dt.getMinutes()).padStart(2, '0');
              const seconds = String(dt.getSeconds()).padStart(2, '0');
              const dateTime = `${month}-${day} ${hours}:${minutes}:${seconds}`;

              // 2) 동작 모드 텍스트 및 클래스 결정
              const modeText = MODE_LABEL[log.operation_mode] || log.operation_mode || '알 수 없음';
              const modeClassName = `mode-${(log.operation_mode || 'unknown').toLowerCase()}`;

              // 3) 상세 내용
              const description = EVENT_LABEL[log.event_type] || log.details?.description || '-';

              // 4) 아이콘 및 행 전체에 적용할 클래스
              const getRiskInfo = (eventType) => {
                switch (eventType) {
                  case 'LOG_CRITICAL_FALLING':
                  case 'LOG_CRITICAL_SENSOR':
                    return { icon: '🔥', className: 'status-critical' };
                  case 'LOG_INTRUSION_SLOWDOWN':
                  case 'LOG_LOTO_ACTIVE':
                    return { icon: '⚠️', className: 'status-high' };
                  case 'LOG_CROUCHING_WARN':
                    return { icon: '❗', className: 'status-medium' };
                  case 'LOG_MAINTENANCE_SAFE':
                  case 'LOG_NORMAL_OPERATION':
                    return { icon: 'ℹ️', className: 'status-safe' };
                  default:
                    return { icon: 'ℹ️', className: 'status-safe' };
                }
              };
              const { icon, className: rowClassName } = getRiskInfo(log.event_type);

              // 5) key
              const key = log.id ?? `${log.timestamp}-${idx}`;

              return (
                <tr
                  key={key}
                  className={[rowClassName, log.id === activeId && 'active']
                              .filter(Boolean)
                              .join(' ')}
                  onClick={() => onSelect(log.id)}
                >
                  <td className="date-cell">{dateTime}</td>
                  <td className={`mode-cell ${modeClassName}`}>{modeText}</td>
                  <td className="description-cell">{icon} {description}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
