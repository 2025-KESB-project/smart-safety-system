export default function ControlBoard({
  isOperating, loading, onStart, onStop, onDangerMode,
}) {
  return (
    <div className="control-board">
      <h3>🛠️ 컨트롤 보드</h3>
      <button
        onClick={onStart}
        disabled={loading || isOperating === true}
      >
        {loading && !isOperating ? '⏳ 시작 중...' : '▶️ 컨베이어 작동 시작'}
      </button>
      <button
        onClick={onStop}
        disabled={loading || isOperating === false}
      >
        {loading && isOperating ? '⏳ 정지 중...' : '⏸️ 컨베이어 작동 정지'}
      </button>
      <button onClick={onDangerMode} disabled={loading}>
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
