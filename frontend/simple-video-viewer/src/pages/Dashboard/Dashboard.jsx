// src/pages/Dashboard/Dashboard.jsx
import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { LogOut } from 'lucide-react';

// --- 컴포넌트 임포트 ---
import LiveStreamContent from './LiveStreamContent';
import VideoLogTable from './VideoLogTable';
import DangerZoneSelector from './DangerZoneSelector';
import ConveyorMode from './ConveyorMode';
import ZoneConfigPanel from './ZoneConfigPanel';

// --- 훅 및 스토어 임포트 ---
import { useWebSocket } from '../../hooks/useWebSocket';
import useDashboardStore from '../../store/useDashboardStore';
import { zoneAPI } from '../../services/api'; // zoneAPI 임포트

import './Dashboard.css';

const WS_URL = 'ws://localhost:8000/ws/logs';

export default function Dashboard() {
  // 1. Zustand 스토어에서 상태와 액션을 가져옵니다.
  const {
    logs, zones, loading, error, popupError, operationMode,
    fetchLogs, fetchZones, addLog, handleControl, setPopupError
  } = useDashboardStore();

  // 2. Dashboard 컴포넌트 자체에서 관리해야 하는 UI 상태들
  const [showLogoutModal, setShowLogoutModal] = useState(false);
  const [currentTime, setCurrentTime] = useState('');
  const [activeId, setActiveId] = useState(null);

  // --- 위험 구역 설정 관련 상태 ---
  const [isDangerMode, setIsDangerMode] = useState(false);
  const [configAction, setConfigAction] = useState(null);
  const [selectedZoneId, setSelectedZoneId] = useState(null);
  const [selectedZone, setSelectedZone] = useState([]);
  const [newZoneName, setNewZoneName] = useState('');
  const [showInstruction, setShowInstruction] = useState(false);
  const [showComplete, setShowComplete] = useState(false);
  const [imageSize, setImageSize] = useState(null);

  const navigate = useNavigate();
  const liveStreamRef = useRef(null);

  // 3. 웹소켓 설정: 메시지를 받으면 스토어의 addLog 액션을 호출합니다.
  const handleWsMessage = useCallback((msg) => {
    if (msg && msg.event_type) {
      addLog(msg);
    }
  }, [addLog]);

  const { status: wsStatus, error: wsError } = useWebSocket(WS_URL, handleWsMessage);

  // 4. 초기 데이터 로딩 (useEffect)
  useEffect(() => {
    fetchLogs(true); // 최초 로딩 시 로딩 인디케이터 표시
    fetchZones();
  }, [fetchLogs, fetchZones]);

  // 현재 시간 업데이트
  useEffect(() => {
    const timer = setInterval(() => {
      const now = new Date();
      const year = now.getFullYear();
      const month = String(now.getMonth() + 1).padStart(2, '0');
      const date = String(now.getDate()).padStart(2, '0');
      const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
      const day = dayNames[now.getDay()];
      let h = now.getHours();
      const m = String(now.getMinutes()).padStart(2, '0');
      const ampm = h >= 12 ? 'PM' : 'AM';
      if (h > 12) h -= 12;
      if (h === 0) h = 12;
      setCurrentTime(`${year}-${month}-${date} (${day}) / ${ampm}-${h}:${m}`);
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  // --- 위험 구역 관련 핸들러 함수들 (추후 별도 훅으로 분리 가능) ---

  const handleCreateZone = async () => {
    try {
      const id = `zone_${Date.now()}`;
      const name = newZoneName.trim() || `Zone ${zones.length + 1}`;
      const pts = selectedZone.map(r => ({
        x: Math.round(r.xRatio * (imageSize?.naturalWidth || 800)),
        y: Math.round(r.yRatio * (imageSize?.naturalHeight || 600)),
      }));
      const payload = { id, zone_data: { name, points: pts } };
      await zoneAPI.saveZones(payload); // zoneAPI 사용
      await fetchZones();
      setShowComplete(true);
      setNewZoneName('');
    } catch (err) {
      setPopupError('위험 구역 생성 실패: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleUpdateZone = async () => {
    if (!selectedZoneId) return;
    try {
      const existingZone = zones.find(z => z.id === selectedZoneId);
      const pts = selectedZone.map(r => ({
        x: Math.round(r.xRatio * (imageSize?.naturalWidth || 800)),
        y: Math.round(r.yRatio * (imageSize?.naturalHeight || 600)),
      }));
      const payload = { name: existingZone?.name || '', points: pts };
      await zoneAPI.updateZone(selectedZoneId, payload); // zoneAPI 사용 (updateZone은 아직 미구현)
      await fetchZones();
      setShowComplete(true);
    } catch (err) {
      setPopupError('위험 구역 업데이트 실패: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleDeleteZone = async () => {
    if (!selectedZoneId) return;
    const targetName = zones.find(z => z.id === selectedZoneId)?.name || '선택된 구역';
    if (!window.confirm(`${targetName}을 삭제하시겠습니까?`)) return;
    try {
      await zoneAPI.deleteZone(selectedZoneId); // zoneAPI 사용 (deleteZone은 아직 미구현)
      setSelectedZoneId(null);
      await fetchZones();
      setShowComplete(true);
    } catch (err) {
      setPopupError('위험 구역 삭제 실패: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleDangerComplete = (ratioPoints) => {
    setSelectedZone(ratioPoints);
    setShowInstruction(configAction === 'create');
  };

  const handleConfirm = async () => {
    if (configAction === 'create') await handleCreateZone();
    if (configAction === 'update') await handleUpdateZone();
    if (configAction === 'delete') await handleDeleteZone();
    setConfigAction(null);
    setSelectedZone([]);
    setSelectedZoneId(null);
    setIsDangerMode(false);
  };

  useEffect(() => {
    if (!showComplete) return;
    const t = setTimeout(() => setShowComplete(false), 3000);
    return () => clearTimeout(t);
  }, [showComplete]);

  // 5. 렌더링
  return (
    <div className="dashboard">
      <div className="header-bar">
        <div className="logo">GUARD-4</div>
        <div className="right-info">
          <div className="date-time">{currentTime}</div>
          <button className="logout-btn" onClick={() => setShowLogoutModal(true)}>
            <LogOut size={18} /> Logout
          </button>
        </div>
      </div>

      <div className="ws-status">
        {wsStatus === 'connecting' && '🔄 연결 중...'}
        {wsStatus === 'open' && '✅ 연결됨'}
        {wsStatus === 'closed' && '⛔ 연결 끊김'}
        {wsError && `❌ 오류 발생: ${wsError?.message}`}
      </div>

      <div className="main-layout">
        <div className="left-panel">
          <div className="live-stream-wrapper dz-wrapper" style={{ position: 'relative' }}>
            {isDangerMode && (configAction === 'create' || configAction === 'update') ? (
              <DangerZoneSelector
                onComplete={handleDangerComplete}
                onImageLoad={setImageSize}
              />
            ) : (
              <LiveStreamContent eventId={activeId} onImageLoad={setImageSize} />
            )}
            {showComplete && <div className="center-message">✅ 작업이 완료되었습니다!</div>}
          </div>
        </div>

        <div className="right-panel">
          {!isDangerMode ? (
            <>
              {loading && !logs.length ? (
                <div className="loading">로그를 불러오는 중…</div>
              ) : error ? (
                <div className="error">{error}</div>
              ) : (
                <VideoLogTable logs={logs} activeId={activeId} onSelect={setActiveId} />
              )}
              <ConveyorMode
                operationMode={operationMode}
                loading={loading}
                onStartAutomatic={() => handleControl('start_automatic')}
                onStartMaintenance={() => handleControl('start_maintenance')}
                onStop={() => handleControl('stop')}
                onDangerMode={() => setIsDangerMode(true)}
              />
            </>
          ) : (
            <>
              <ZoneConfigPanel
                zones={zones}
                selected={selectedZoneId}
                onSelect={setSelectedZoneId}
                currentAction={configAction}
                onActionSelect={setConfigAction}
                onDelete={handleDeleteZone}
                onCancel={() => setIsDangerMode(false)}
              />
              {(configAction === 'create' || configAction === 'update' || configAction === 'delete') && (
                 <button className="confirm-btn" onClick={handleConfirm}>
                  {configAction === 'create' && '생성 완료'}
                  {configAction === 'update' && '업데이트 완료'}
                  {configAction === 'delete' && '삭제 완료'}
                </button>
              )}
              {configAction === 'create' && (
                <input
                  type="text"
                  placeholder="구역 이름을 입력하세요"
                  value={newZoneName}
                  onChange={e => setNewZoneName(e.target.value)}
                  className="zone-name-input"
                />
              )}
            </>
          )}
        </div>
      </div>

      {popupError && (
        <div className="error-popup-overlay">
          <div className="error-popup">
            <div className="error-popup-header">
              <span>⚠️ 작업 실패</span>
              <button onClick={() => setPopupError(null, true)}>&times;</button>
            </div>
            <div className="error-popup-content">{popupError}</div>
          </div>
        </div>
      )}

      {showLogoutModal && (
        <div className="logout-overlay">
          <div className="logout-modal">
            <div className="logout-title">로그아웃 하시겠습니까?</div>
            <div className="logout-buttons">
              <button className="logout-yes" onClick={() => navigate('/login')}>네</button>
              <button className="logout-no" onClick={() => setShowLogoutModal(false)}>아니요</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
