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
    isLocked, // isLocked 상태 추가
    activeId, isDangerMode, configAction, newZoneName, selectedZoneId,
    wsStatus, currentTime,
    initialize, setActiveId, handleControl, 
    resetSystem, // resetSystem 액션 추가
    enterDangerMode, exitDangerMode, setConfigAction, setSelectedZoneId,
    setNewZoneName, setImageSize, handleCreateZone, handleUpdateZone, handleDeleteZone,
    setPopupError, testLotoCondition // 디버깅용 액션 가져오기
  } = useDashboardStore();

  const [showLogoutModal, setShowLogoutModal] = useState(false);
  const navigate = useNavigate();

  // 2. 초기 데이터 로딩 및 WebSocket 연결, 그리고 정리
  useEffect(() => {
    // 컴포넌트가 마운트될 때 초기화 함수를 호출합니다.
    initialize();

    // 컴포넌트가 언마운트될 때 실행될 클린업 함수를 반환합니다.
    // 이것은 StrictMode에서의 이중 호출 및 페이지 이동 시 메모리 누수를 방지합니다.
    return () => {
      useDashboardStore.getState().disconnect();
    };
  }, []); // 의존성 배열을 비워서 마운트/언마운트 시에만 실행되도록 보장

  // 3. 유저의 이름을 로컬 스토리지에서 가져옵니다.
  const [username, setUsername] = useState('');
  useEffect(() => {
  const savedUsername = localStorage.getItem('username') || 'admin';
  setUsername(savedUsername);
  }, []);

  return (
    <div className="dashboard">
      {/* 헤더 */}
      <div className="header-bar">
        <div className="header-left">
          <div className="logo">Conveyor Guard</div>
          <div className="factory-label">경기대 가상 공장</div>
        </div>
        <div className="right-info">
          <div className="date-time">{currentTime}</div>
          <div className="user-label">🧑‍💻 {username}(admin)</div>
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
        {/* 스트림 패널 (좌측) */}
        <div className="stream-panel">
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

        {/* 제어 및 로그 패널 (우측) */}
        <div className="control-panel">
          {isLocked ? (
            <div className="system-locked-panel">
              <div className="system-locked-title">SYSTEM LOCKED</div>
              <p className="system-locked-message">치명적인 위험이 감지되어 시스템이 비상 정지되었습니다. 관리자의 확인 후 시스템을 리셋하세요.</p>
              <button 
                className="system-reset-btn"
                onClick={resetSystem}
                disabled={loading}
              >
                {loading ? '리셋 중...' : '🚨 시스템 리셋'}
              </button>
            </div>
          ) : loading ? (
            <div className="loading">로딩 중…</div>
          ) : error ? (
            <div className="error">{error}</div>
          ) : !isDangerMode ? (
            <>
              {/* 긴급 대응 영역 */}
              <div className="emergency-response-panel">
                <button 
                  className="emergency-stop-btn"
                  onClick={() => handleControl('stop')} 
                  disabled={loading} /* 로딩 중이 아닐 때는 항상 활성화 */
                >
                  🚨 긴급 정지
                </button>
              </div>

              {/* 일반 제어 영역 */}
              <ConveyorMode
                className="control-board"
                operationMode={operationMode}
                loading={loading}
                onStartAutomatic={() => handleControl('start_automatic')}
                onStartMaintenance={() => handleControl('start_maintenance')}
                onStop={() => handleControl('stop')}
                onDangerMode={enterDangerMode}
              />
              {/* LOTO 테스트 버튼 임시 추가 */}
              <button onClick={testLotoCondition} style={{marginTop: '10px', background: '#777', color: 'white', border: 'none', padding: '10px', borderRadius: '6px', cursor: 'pointer'}}>
                [DEBUG] LOTO 테스트 상태 만들기
              </button>
              <VideoLogTable 
                className="log-board"
                logs={logs} 
                activeId={activeId} 
                onSelect={setActiveId} 
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
          onConfirm={() => {
            localStorage.clear();
            navigate('/login');
          }}
          onCancel={() => setShowLogoutModal(false)}
        />
      )}
    </div>
  );
}
