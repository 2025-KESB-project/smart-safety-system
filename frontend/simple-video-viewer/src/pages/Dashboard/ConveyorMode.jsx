// src/pages/Dashboard/ControlBoard.jsx
// 우측 하단의 컨트롤 보드 컴포넌트
import React from 'react';
import './ConveyorMode.css';

export default function ControlBoard({
  isOperating,
  onStart,
  onStop,
  onDangerMode,
}) {
  return (
    <div className="control-board">
      <h3>🛠️ 컨트롤 보드</h3>
      <button onClick={onStart} disabled={isOperating === true}>
        ▶️ 컨베이어 작동 시작
      </button>
      <button onClick={onStop} disabled={isOperating === false}>
        ⏸️ 컨베이어 작동 정지
      </button>
      <button onClick={onDangerMode}>
        ⚠️ 위험 구역 설정
      </button>
      <div className="status-line">
        현재 상태:{' '}
        {isOperating == null
          ? '불러오는 중...'
          : isOperating
          ? '🟢 작동 중'
          : '🔴 정지 상태'}
      </div>
    </div>
  );
}
