export default function ConveyorMode({
  isOperating,
  loading,
  onStartAutomatic,
  onStartMaintenance,
  onStop,
  onDangerMode,
}) {
  return (
    <div className="control-board">
      <h3>🛠️ 컨트롤 보드</h3>
      <button onClick={onStartAutomatic} disabled={loading || isOperating === true}>
        {loading && !isOperating ? "⏳ 시작 중..." : "▶️ 운전 모드 시작"}
      </button>
      <button onClick={onStartMaintenance} disabled={loading || isOperating === true}>
        {loading && !isOperating ? "⏳ 시작 중..." : "🛠️ 정비 모드 시작"}
      </button>
      <button onClick={onStop} disabled={loading || isOperating === false}>
        {loading && isOperating ? "⏳ 정지 중..." : "⏸️ 시스템 전체 정지"}
      </button>
      <button onClick={onDangerMode} disabled={loading}>
        ⚠️ 위험 구역 설정
      </button>
      <div className="status-line">
        현재 상태:{" "}
        {isOperating == null
          ? "불러오는 중..."
          : isOperating
          ? "🟢 작동 중"
          : "🔴 정지 상태"}
      </div>
    </div>
  );
}

