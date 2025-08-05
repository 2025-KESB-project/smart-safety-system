// src/pages/Dashboard/Dashboard.jsx
import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { LogOut } from 'lucide-react';

// --- 컴포넌트 임포트 ---
import LiveStreamContent from '../../components/dashboard/LiveStreamContent';
import VideoLogTable from '../../components/dashboard/VideoLogTable';
import DangerZoneSelector from '../../components/dashboard/DangerZoneSelector';
import ConveyorMode from '../../components/dashboard/ConveyorMode';
import ZoneConfigPanel from '../../components/dashboard/ZoneConfigPanel';
import ZoneOverlay from '../../components/dashboard/ZoneOverlay';

// --- 훅 및 스토어 임포트 ---
// import { useWebSocket } from '../../hooks/useWebSocket'; // 더 이상 사용하지 않음
import useDashboardStore from '../../store/useDashboardStore';

import './Dashboard.css';

// WebSocket 서버 URL 정의
const WS_URL = 'ws://localhost:8000/ws/logs';

// --- 재사용 가능한 모달 컴포넌트들 ---
const ErrorPopup = ({ message, onClose }) => {
  if (!message) return null;
  return (
    <div className="error-popup-overlay">
      <div className="error-popup">
        <div className="error-popup-header">
          <span>⚠️ 작업 실패 ⚠️</span>
          <button onClick={onClose}>&times;</button>
        </div>
        <div className="error-popup-content">{message}</div>
      </div>
    </div>
  );
};

const LogoutModal = ({ onConfirm, onCancel }) => (
  <div className="logout-overlay">
    <div className="logout-modal">
      <div className="logout-title">로그아웃 하시겠습니까?</div>
      <div className="logout-buttons">
        <button className="logout-yes" onClick={onConfirm}>네</button>
        <button className="logout-no" onClick={onCancel}>아니요</button>
      </div>
    </div>
  </div>
);

// --- 메인 대시보드 컴포넌트 ---
export default function Dashboard() {
  // 1. 스토어에서 모든 상태와 액션을 가져옵니다.
  const {
    logs, zones, operationMode, loading, error, popupError, globalAlert, // globalAlert 추가
    activeId, isDangerMode, configAction, newZoneName, selectedZoneId,
    initialize, addLog, setActiveId, handleControl, 
    enterDangerMode, exitDangerMode, setConfigAction, setSelectedZoneId,
    setNewZoneName, setImageSize, handleCreateZone, handleUpdateZone, handleDeleteZone,
    setPopupError
  } = useDashboardStore();

  const [showLogoutModal, setShowLogoutModal] = useState(false);
  const [currentTime, setCurrentTime] = useState('');
  const navigate = useNavigate();

  // --- WebSocket 상태 직접 관리 ---
  const ws = useRef(null);
  const [wsStatus, setWsStatus] = useState('connecting');

  // 2. 초기 데이터 로딩 및 시간 표시
  useEffect(() => {
    initialize();
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
  }, [initialize]);

  // 3. WebSocket 연결 로직 (React StrictMode 호환)
  useEffect(() => {
    console.log("WebSocket 연결 시도...");
    setWsStatus('connecting');
    const socket = new WebSocket(WS_URL);

    socket.onopen = () => {
      console.log("✅ WebSocket 연결 성공!");
      setWsStatus('open');
    };

    socket.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        if (message && message.event_type) {
          addLog(message);
        }
      } catch (e) {
        console.error("WebSocket 메시지 처리 오류:", e);
      }
    };

    socket.onerror = (error) => {
      console.error("❌ WebSocket 오류 발생:", error);
      setWsStatus('error');
    };

    socket.onclose = () => {
      console.log("⛔️ WebSocket 연결 닫힘");
      setWsStatus('closed');
    };

    ws.current = socket;

    // 컴포넌트가 언마운트될 때 WebSocket 연결을 정리하는 cleanup 함수입니다.
    // React.StrictMode에서는 이 cleanup 함수가 조기에 호출될 수 있으며,
    // 이로 인해 'WebSocket is closed before the connection is established'
    // 라는 경고가 개발 중에 표시될 수 있습니다. 이는 StrictMode의 정상적인 동작이며,
    // 프로덕션 빌드에서는 발생하지 않습니다.
    return () => {
      console.log("WebSocket 연결 정리...");
      // 이벤트 핸들러를 먼저 null로 설정하여, close() 이후에
      // 예기치 않은 이벤트가 발생하는 것을 방지합니다.
      socket.onopen = null;
      socket.onmessage = null;
      socket.onerror = null;
      socket.onclose = null;
      socket.close();
    };
  }, []); // 의존성 배열을 비워 최초 1회만 실행되도록 수정

  return (
    <div className="dashboard">
      {/* 헤더 */}
      <div className="header-bar">
        <div className="logo">GUARD-4</div>
        <div className="right-info">
          <div className="date-time">{currentTime}</div>
          <button className="logout-btn" onClick={() => setShowLogoutModal(true)}>
            <LogOut size={18} /> Logout
          </button>
        </div>
      </div>

      {/* WebSocket 상태 */}
      <div className="ws-status">
        {wsStatus === 'connecting' && '🔄 연결 중...'}
        {wsStatus === 'open' && '✅ 연결됨'}
        {wsStatus === 'closed' && '⛔ 연결 끊김'}
        {wsStatus === 'error' && '❌ 오류 발생'}
      </div>

      {/* 메인 레이아웃 */}
      <div className="main-layout">
        {/* 왼쪽 패널 */}
        <div className="left-panel">
          <div className="live-stream-wrapper">
            {isDangerMode && (configAction === 'create' || configAction === 'update') ? (
              <DangerZoneSelector
                onComplete={
                  configAction === 'create' 
                    ? handleCreateZone 
                    : handleUpdateZone
                }
                onImageLoad={setImageSize}
              />
            ) : (
              <div style={{ position: 'relative', width: '100%', height: '100%' }}>
                <LiveStreamContent
                  eventId={activeId}
                  onImageLoad={setImageSize}
                />
                <ZoneOverlay 
                  zones={zones} 
                  selectedZoneId={selectedZoneId} 
                />
              </div>
            )}
          </div>
        </div>

        {/* 오른쪽 패널 */}
        <div className="right-panel">
          {loading ? <div className="loading">로딩 중…</div> :
           error ? <div className="error">{error}</div> :
           !isDangerMode ? (
            <>
              <VideoLogTable logs={logs} activeId={activeId} onSelect={setActiveId} />
              <ConveyorMode
                operationMode={operationMode}
                loading={loading}
                onStartAutomatic={() => handleControl('start_automatic')}
                onStartMaintenance={() => handleControl('start_maintenance')}
                onStop={() => handleControl('stop')}
                onDangerMode={enterDangerMode}
              />
            </>
          ) : (
            <ZoneConfigPanel
              zones={zones}
              selected={selectedZoneId}
              onSelect={setSelectedZoneId}
              currentAction={configAction}
              onActionSelect={setConfigAction}
              newZoneName={newZoneName}
              onNameChange={setNewZoneName}
              onDelete={handleDeleteZone}
              onCancel={exitDangerMode}
            />
          )}
        </div>
      </div>

      {/* 모달 및 긴급 알림 */} 
      {globalAlert && (
        <div className={`global-alert ${globalAlert.log_risk_level?.toLowerCase()}`}>
          <div className="global-alert-content">
            <h2>{globalAlert.log_risk_level}</h2>
            <p>{globalAlert.details?.description || '긴급 상황 발생!'}</p>
            <span>({new Date(globalAlert.timestamp).toLocaleTimeString()})</span>
          </div>
        </div>
      )}
      <ErrorPopup message={popupError} onClose={() => setPopupError(null)} />
      {showLogoutModal && (
        <LogoutModal
          onConfirm={() => navigate('/login')}
          onCancel={() => setShowLogoutModal(false)}
        />
      )}
    </div>
  );
}