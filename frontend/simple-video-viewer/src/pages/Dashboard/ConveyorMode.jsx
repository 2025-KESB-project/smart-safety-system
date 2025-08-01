export default function ConveyorMode({
  operationMode,
  loading,
  onStartAutomatic,
  onStartMaintenance,
  onStop,
  onDangerMode,
}) {

  const getStatusText = () => {
    if (operationMode === 'AUTOMATIC') return '🟢 운전 모드';
    if (operationMode === 'MAINTENANCE') return '🟠 정비 모드';
    if (operationMode === null) return '불러오는 중...';
    return '🔴 정지 상태';
  };

  return (
    <div className="control-board">
      <h3>🛠️ 컨트롤 보드</h3>
      <button onClick={onStartAutomatic} disabled={loading || operationMode === 'AUTOMATIC'}>
        {loading && operationMode !== 'AUTOMATIC' ? "⏳ 전환 중..." : "▶️ 운전 모드 시작"}
      </button>
      <button onClick={onStartMaintenance} disabled={loading || operationMode === 'MAINTENANCE'}>
        {loading && operationMode !== 'MAINTENANCE' ? "⏳ 전환 중..." : "🛠️ 정비 모드 시작"}
      </button>
      <button onClick={onStop} disabled={loading || !operationMode}>
        {loading && operationMode ? "⏳ 정지 중..." : "⏸️ 시스템 전체 정지"}
      </button>
      <button onClick={onDangerMode} disabled={loading}>
        ⚠️ 위험 구역 설정
      </button>
      <div className="status-line">
        현재 상태: {getStatusText()}
      </div>
    </div>
  );
}

