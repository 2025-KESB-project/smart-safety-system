// src/pages/Dashboard/Dashboard.jsx
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { LogOut } from 'lucide-react';

// --- 컴포넌트 임포트 ---
import LiveStreamContent from '../../components/dashboard/LiveStreamContent';
import VideoLogTable from '../../components/dashboard/VideoLogTable';
import DangerZoneSelector from '../../components/dashboard/DangerZoneSelector';
import ConveyorMode from '../../components/dashboard/ConveyorMode';
import ZoneConfigPanel from '../../components/dashboard/ZoneConfigPanel';
import ZoneOverlay from '../../components/dashboard/ZoneOverlay'; // 분리된 ZoneOverlay 임포트

// --- 훅 및 스토어 임포트 ---
import useDashboardStore from '../../store/useDashboardStore';

import './Dashboard.css';



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
    logs, zones, operationMode, loading, error, popupError, globalAlert,
    activeId, isDangerMode, configAction, newZoneName, selectedZoneId,
    wsStatus, currentTime,
    initialize, setActiveId, handleControl, 
    enterDangerMode, exitDangerMode, setConfigAction, setSelectedZoneId,
    setNewZoneName, setImageSize, handleCreateZone, handleUpdateZone, handleDeleteZone,
    setPopupError
  } = useDashboardStore();

  const [showLogoutModal, setShowLogoutModal] = useState(false);
  const navigate = useNavigate();

  // 2. 초기 데이터 로딩 및 시간 표시
  useEffect(() => {
    initialize(); // 스토어의 초기화 함수 호출
  }, [initialize]);

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
