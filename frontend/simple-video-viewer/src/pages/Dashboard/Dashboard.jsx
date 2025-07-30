// src/pages/Dashboard/Dashboard.jsx

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { LogOut } from 'lucide-react';

import LiveStreamContent  from './LiveStreamContent';
import VideoLogTable      from './VideoLogTable';
import DangerZoneSelector from './DangerZoneSelector';
import ConveyorMode       from './ConveyorMode';
import ZoneConfigPanel    from './ZoneConfigPanel';

import './Dashboard.css';

export default function Dashboard() {
  const navigate = useNavigate();

  // ─── 공통 상태 ─────────────────────────────────
  const [showLogoutModal, setShowLogoutModal] = useState(false);
  const [currentTime,    setCurrentTime]     = useState('');
  const [logs,           setLogs]            = useState([]);
  const [activeId,       setActiveId]        = useState(null);
  const [loading,        setLoading]         = useState(false);
  const [error,          setError]           = useState(null);
  const [isOperating,    setIsOperating]     = useState(null);
  const [controlLoading, setControlLoading]  = useState(false);

  // ─── 위험 구역 모드 상태 ─────────────────────────
  const [isDangerMode,    setIsDangerMode]    = useState(false);
  const [configAction,    setConfigAction]    = useState(null);
  const [showInstruction, setShowInstruction] = useState(false);
  const [showComplete,    setShowComplete]    = useState(false);
  const [selectedZone,    setSelectedZone]    = useState([]);   // 점 찍은 좌표
  const [zones,           setZones]           = useState([]);   // API에서 받아온 전체 목록
  const [selectedZoneId,  setSelectedZoneId]  = useState(null); // 목록 클릭한 ID

  // ─── 1) 현재 시간 표시 ───────────────────────────
  useEffect(() => {
    const timer = setInterval(() => {
      const now = new Date();
      let   h   = now.getHours();
      const ap  = h >= 12 ? 'PM' : 'AM';
      if (h > 12) h -= 12;
      if (h === 0) h = 12;
      setCurrentTime(
        `${now.getFullYear()}-${String(now.getMonth()+1).padStart(2,'0')}-${String(now.getDate()).padStart(2,'0')}` +
        ` (${['Sun','Mon','Tue','Wed','Thu','Fri','Sat'][now.getDay()]}) / ${ap}-${h}:${String(now.getMinutes()).padStart(2,'0')}`
      );
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  // ─── showInstruction 3초 뒤 자동 숨김 ────────────────
  useEffect(() => {
    if (!showInstruction) return;
    const t = setTimeout(() => setShowInstruction(false), 3000);
    return () => clearTimeout(t);
  }, [showInstruction]);

  // ─── 2) 로그 페치 & 폴링 ───────────────────────────
  const fetchLogs = useCallback(async (showLoad) => {
    if (showLoad) setLoading(true);
    setError(null);
    try {
      const res  = await fetch('http://localhost:8000/api/logs?limit=50');
      if (!res.ok) throw new Error(res.status);
      const data = await res.json();
      setLogs(data);
      if (data.length) setActiveId(data[0].id);
    } catch (e) {
      console.error(e);
      setError('로그 로드 중 오류가 발생했습니다.');
    } finally {
      if (showLoad) setLoading(false);
    }
  }, []);
  useEffect(() => { fetchLogs(true); }, [fetchLogs]);
  useEffect(() => {
    const iv = setInterval(() => fetchLogs(false), 5000);
    return () => clearInterval(iv);
  }, [fetchLogs]);

  // ─── 3) 컨베이어 상태 ───────────────────────────────
  const fetchConveyorStatus = useCallback(async () => {
    try {
      const res = await fetch('http://localhost:8000/api/control/status');
      if (!res.ok) throw new Error(res.status);
      const { is_operating } = await res.json();
      setIsOperating(is_operating);
    } catch (e) {
      console.error('컨베이어 상태 조회 실패', e);
    }
  }, []);
  useEffect(() => { fetchConveyorStatus(); }, [fetchConveyorStatus]);

  // ─── 4) 컨베이어 제어 ───────────────────────────────
  const handleStart = async () => {
    setControlLoading(true);
    try {
      const res = await fetch('http://localhost:8000/api/control/start', { method: 'POST' });
      if (!res.ok) throw new Error(res.status);
      await fetchConveyorStatus();
    } catch (e) {
      console.error(e);
      alert('⚠️ 컨베이어 시작 중 오류가 발생했습니다.');
    } finally {
      setControlLoading(false);
    }
  };
  const handleStop = async () => {
    setControlLoading(true);
    try {
      const res = await fetch('http://localhost:8000/api/control/stop', { method: 'POST' });
      if (!res.ok) throw new Error(res.status);
      await fetchConveyorStatus();
    } catch (e) {
      console.error(e);
      alert('⚠️ 컨베이어 정지 중 오류가 발생했습니다.');
    } finally {
      setControlLoading(false);
    }
  };

  // ─── 5) 위험 구역 CRUD API ─────────────────────────
  const fetchZones = useCallback(async () => {
    try {
      const res = await fetch('http://localhost:8000/api/zones/');
      if (!res.ok) throw new Error(res.status);
      setZones(await res.json());
    } catch (e) {
      console.error('구역 조회 실패', e);
    }
  }, []);

  const handleCreateZone = async () => {
    await fetch('http://localhost:8000/api/zones/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ coords: selectedZone })
    });
    await fetchZones();
  };

  const handleUpdateZone = async (id) => {
    await fetch(`http://localhost:8000/api/zones/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ coords: selectedZone })
    });
    await fetchZones();
  };

  const handleDeleteZone = async (id) => {
    await fetch(`http://localhost:8000/api/zones/${id}`, { method: 'DELETE' });
    setSelectedZoneId(null);
    await fetchZones();
  };

  // ─── 6) 위험 모드 진입 ─────────────────────────────
  const startDangerMode = () => {
    setIsDangerMode(true);
    setConfigAction(null);
    fetchZones();
    setShowInstruction(false);
  };

  // ─── 7) 점 찍기 완료 콜백 ───────────────────────────
  const handleDangerComplete = (coords) => {
    setSelectedZone(coords);
  };

  // ─── 8) 로그아웃 ───────────────────────────────────
  const handleLogoutConfirm = () => {
    setShowLogoutModal(false);
    navigate('/login');
  };

  // ─── 9) 생성/업데이트 확인 핸들러 ──────────────────
  const handleConfirm = async () => {
    setShowComplete(true);

    if (configAction === 'create') {
      await handleCreateZone();
    } else {
      await handleUpdateZone(selectedZoneId);
    }

    setConfigAction(null);
    setSelectedZoneId(null);
    setSelectedZone([]);
    setShowInstruction(false);

    // **여기서** 대시보드 메인으로 돌아갑니다
    setIsDangerMode(false);
  };

  // ─── ✅ 생성 완료 메시지 자동 숨김 ─────────────────────
  useEffect(() => {
    if (!showComplete) return;
    const timer = setTimeout(() => setShowComplete(false), 3000);
    return () => clearTimeout(timer);
  }, [showComplete]);

  return (
    <div className="dashboard">
      {/* 상단 헤더 */}
      <div className="header-bar">
        <div className="logo">GUARD-4</div>
        <div className="right-info">
          <div className="date-time">{currentTime}</div>
          <button className="logout-btn" onClick={() => setShowLogoutModal(true)}>
            <LogOut size={18} /> Logout
          </button>
        </div>
      </div>

      {/* 위험 구역 생성 안내 */}
      {isDangerMode && configAction === 'create' && showInstruction && (
        <div className="center-message">
          ⚠️ 화면을 클릭하여 점을 찍고 위험 구역을 생성하세요!
        </div>
      )}

      {/* 생성 완료 메시지 */}
      {showComplete && (
        <div className="center-message">
          ✅ 위험 구역이 생성되었습니다!
        </div>
      )}

      {/* 메인 레이아웃 */}
      <div className="main-layout">
        {/* 좌측 비디오 */}
        <div className="left-panel">
          <div className="live-stream-wrapper">
            {isDangerMode && (configAction === 'create' || configAction === 'update') ? (
              <DangerZoneSelector onComplete={handleDangerComplete} />
            ) : (
              <>
                <LiveStreamContent eventId={activeId} />
                {!isDangerMode && selectedZone.length > 0 && (
                  <ZoneOverlay coords={selectedZone} />
                )}
              </>
            )}
          </div>
        </div>

        {/* 우측 패널 */}
        <div className="right-panel">
          {!isDangerMode ? (
            <>
              {loading && !logs.length ? (
                <div className="loading">로그 불러오는 중...</div>
              ) : error ? (
                <div className="error">{error}</div>
              ) : (
                <VideoLogTable logs={logs} activeId={activeId} onSelect={setActiveId} />
              )}
              <ConveyorMode
                isOperating={isOperating}
                loading={controlLoading}
                onStart={handleStart}
                onStop={handleStop}
                onDangerMode={startDangerMode}
              />
            </>
          ) : (
            <>
              <ZoneConfigPanel
                zones={zones}
                selected={selectedZoneId}
                onSelect={setSelectedZoneId}
                currentAction={configAction}
                onActionSelect={a => {
                  setConfigAction(a);
                  setShowInstruction(a === 'create');
                }}
                onDelete={handleDeleteZone}
                onCancel={() => setIsDangerMode(false)}
              />
              {(configAction === 'create' || configAction === 'update') && (
                <button className="confirm-btn" onClick={handleConfirm}>
                  {configAction === 'create' ? '생성 완료' : '업데이트 완료'}
                </button>
              )}
            </>
          )}
        </div>
      </div>

      {/* 로그아웃 모달 */}
      {showLogoutModal && (
        <div className="logout-overlay">
          <div className="logout-modal">
            <div className="logout-title">로그아웃 하시겠습니까?</div>
            <div className="logout-buttons">
              <button className="logout-yes" onClick={handleLogoutConfirm}>네</button>
              <button className="logout-no" onClick={() => setShowLogoutModal(false)}>아니요</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// 설정된 영역 오버레이
function ZoneOverlay({ coords }) {
  const ref = useRef(null);

  useEffect(() => {
    const canvas = ref.current;
    const ctx    = canvas.getContext('2d');
    const rect   = canvas.getBoundingClientRect();
    const dpr    = window.devicePixelRatio || 1;
    canvas.width  = rect.width * dpr;
    canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);
    ctx.clearRect(0, 0, rect.width, rect.height);
    if (coords.length < 3) return;
    ctx.fillStyle   = 'rgba(255,0,0,0.2)';
    ctx.strokeStyle = 'rgba(255,0,0,0.8)';
    ctx.lineWidth   = 2;
    ctx.beginPath();
    ctx.moveTo(coords[0].x, coords[0].y);
    coords.slice(1).forEach(p => ctx.lineTo(p.x, p.y));
    ctx.closePath();
    ctx.fill();
    ctx.stroke();
  }, [coords]);

  return (
    <canvas
      ref={ref}
      style={{
        position: 'absolute',
        top: 0, left: 0,
        width: '100%', height: '100%',
        pointerEvents: 'none',
      }}
    />
  );
}
