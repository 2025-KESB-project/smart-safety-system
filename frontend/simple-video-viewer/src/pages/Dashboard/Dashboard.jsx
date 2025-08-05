// src/pages/Dashboard/Dashboard.jsx
import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { LogOut } from 'lucide-react';

import LiveStreamContent from './LiveStreamContent';
import VideoLogTable from './VideoLogTable';
import DangerZoneSelector from './DangerZoneSelector';
import ConveyorMode from './ConveyorMode';
import ZoneConfigPanel from './ZoneConfigPanel';

import { useWebSocket } from '../../hooks/useWebSocket';
import useDashboardStore from '../../store/useDashboardStore';

import './Dashboard.css';
import './DangerZoneSelector.css';

const WS_URL = 'ws://localhost:8000/ws/logs';

export default function Dashboard() {
  const navigate = useNavigate();

  // Zustand 스토어 상태/액션
  const {
    logs, zones, loading, error, popupError, operationMode,
    fetchLogs, fetchZones, addLog, handleControl, setPopupError,
  } = useDashboardStore();

  // 로컬 UI 상태
  const [showLogoutModal, setShowLogoutModal] = useState(false);
  const [currentTime, setCurrentTime] = useState('');
  const [activeId, setActiveId] = useState(null);

  const [isDangerMode, setIsDangerMode] = useState(false);
  const [configAction, setConfigAction] = useState(null);
  const [selectedZoneId, setSelectedZoneId] = useState(null);
  const [selectedZone, setSelectedZone] = useState([]);
  const [newZoneName, setNewZoneName] = useState('');
  const [showInstruction, setShowInstruction] = useState(false);
  const [showComplete, setShowComplete] = useState(false);
  const [imageSize, setImageSize] = useState(null);

  // WebSocket
  const handleWsMessage = useCallback((msg) => {
    if (msg && msg.event_type) {
      addLog(msg);
    }
  }, [addLog]);

  const { status: wsStatus, error: wsError } = useWebSocket(WS_URL, handleWsMessage);

  // 현재 시간
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

  // 초기 데이터 로드
  useEffect(() => {
    fetchLogs(true);
    fetchZones();
  }, [fetchLogs, fetchZones]);

  // 위험 구역 CRUD 생성
  const handleCreateZone = async () => {
    const id = `zone_${Date.now()}`;
    let autoName;
    try {
      const resCount = await fetch('http://localhost:8000/api/zones/');
      if (!resCount.ok) throw new Error(resCount.status);
      const existing = await resCount.json();
      autoName = `Zone ${existing.length + 1}`;
    } catch {
      autoName = `Zone ${zones.length + 1}`;
    }
    const name = newZoneName.trim() || autoName;

    // selectedZone은 { x, y } 비율 좌표
    const pts = selectedZone.map(r => {
      const ratioX = r.x;
      const ratioY = r.y;
      return {
        x: Math.round(ratioX * (imageSize?.naturalWidth || 800)),
        y: Math.round(ratioY * (imageSize?.naturalHeight || 600)),
      };
    });

    console.log('변환된 pts:', pts);

    if (!pts.length || pts.some(p => isNaN(p.x) || isNaN(p.y))) {
      alert('❌ 유효하지 않은 위험 구역 좌표입니다.');
      return;
    }

    const payload = { id, name, points: pts };
    const res = await fetch('http://localhost:8000/api/zones/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      alert('위험 구역 생성 실패');
      return;
    }
    alert('✅ 새로운 위험 구역이 생성되었습니다!');
    await fetchZones();
    setShowComplete(true);
    setNewZoneName('');
  };

  // 위험 구역 업데이트
  const handleUpdateZone = async () => {
    console.log('🔍 handleUpdateZone — selectedZoneId =', selectedZoneId);
    const safeId = selectedZoneId?.replace(/^:+/, '');
    if (!safeId) return;

    const existingZone = zones.find(z => z.id === safeId);
    const pts = selectedZone.map(r => {
      const ratioX = r.x;
      const ratioY = r.y;
      return {
        x: Math.round(ratioX * (imageSize?.naturalWidth || 800)),
        y: Math.round(ratioY * (imageSize?.naturalHeight || 600)),
      };
    });

    const payload = { name: existingZone?.name || '', points: pts };
    const res = await fetch(`http://localhost:8000/api/zones/${safeId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      setPopupError('위험 구역 업데이트 실패');
      return;
    }
    await fetchZones();
    setShowComplete(true);
  };

  // 위험 구역 삭제
  const handleDeleteZone = async () => {
    console.log('🔍 handleDeleteZone — selectedZoneId =', selectedZoneId);
    const safeId = selectedZoneId?.replace(/^:+/, '');
    if (!safeId) return;

    let targetName = '';
    try {
      const resList = await fetch('http://localhost:8000/api/zones/');
      if (!resList.ok) throw new Error(resList.status);
      const list = await resList.json();
      targetName = list.find(z => z.id === safeId)?.name || '';
    } catch {
      console.warn('삭제 전 서버 재조회 실패');
    }
    if (!window.confirm(`${targetName || '선택된 구역'}을 삭제하시겠습니까?`)) return;
    const res = await fetch(`http://localhost:8000/api/zones/${safeId}`, { method: 'DELETE' });
    if (!res.ok) {
      alert('위험 구역 삭제 실패');
      return;
    }
    setSelectedZoneId(null);
    await fetchZones();
    setShowComplete(true);
  };
  //  DangerZoneSelector에서 비율 좌표를 받아서 저장
  const handleDangerComplete = ratioPoints => {
    // DangerZoneSelector에서 이미 비율로 변환된 좌표를 받음
    setSelectedZone(ratioPoints);
    setShowInstruction(configAction === 'create');
  };


  // 생성/수정/삭제 확정
  const handleConfirm = async () => {
    if (configAction === 'create') await handleCreateZone();
    if (configAction === 'update') await handleUpdateZone();
    if (configAction === 'delete') await handleDeleteZone();
    setConfigAction(null);
    setSelectedZone([]);
    setSelectedZoneId(null);
    setIsDangerMode(false);
  };

  // 완료 메시지 자동 숨김(3초후)
  useEffect(() => {
    if (!showComplete) return;
    const t = setTimeout(() => setShowComplete(false), 3000);
    return () => clearTimeout(t);
  }, [showComplete]);

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
        {wsError && `❌ 오류 발생: ${wsError?.message}`}
      </div>

      <div className="main-layout">
        {/* 왼쪽 */}
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
            {/* 안내 메시지 */}
            {isDangerMode && configAction==='create' && showInstruction && (
              <div className="center-message">
                ⚠️ 클릭하여 점을 찍어 위험 구역을 생성하세요!
              </div>
            )}

            {/* 완료 메시지 */}
            {showComplete && (
              <div className="center-message">
                ✅ 작업이 완료되었습니다!
              </div>
            )}
            {!isDangerMode && selectedZone.length > 0 && (
              <ZoneOverlay key="preview" ratios={selectedZone} />
            )}
          </div>
        </div>

        {/* 오른쪽 */}
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
                  onChange={(e) => setNewZoneName(e.target.value)}
                  className="zone-name-input"
                />
              )}
            </>
          )}
        </div>
      </div>

      {/* 팝업 */}
      {popupError && (
        <div className="error-popup-overlay">
          <div className="error-popup">
            <div className="error-popup-header">
              <span>⚠️ 작업 실패</span>
              <button onClick={() => setPopupError(null)}>&times;</button>
            </div>
            <div className="error-popup-content">{popupError}</div>
          </div>
        </div>
      )}

      {/* 로그아웃 모달 */}
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

// ZoneOverlay
function ZoneOverlay({ ratios }) {
  const ref = useRef(null);
  useEffect(() => {
    const canvas = ref.current;
    const ctx = canvas.getContext('2d');
    const rect = canvas.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);
    ctx.clearRect(0, 0, rect.width, rect.height);
    if (!ratios || ratios.length < 3) return;
    const pts = ratios.map(p => ({
      x: p.xRatio * rect.width,
      y: p.yRatio * rect.height
    }));
    ctx.fillStyle = 'rgba(0,255,0,0.2)';
    ctx.strokeStyle = 'rgba(0,255,0,0.8)';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(pts[0].x, pts[0].y);
    pts.slice(1).forEach(pt => ctx.lineTo(pt.x, pt.y));
    ctx.closePath();
    ctx.fill();
    ctx.stroke();
  }, [ratios]);
  return (
    <canvas
      ref={ref}
      style={{
        position: 'absolute',
        top: 0, left: 0,
        width: '100%', height: '100%',
        pointerEvents: 'none'
      }}
    />
  );
}
