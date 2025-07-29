// src/pages/Dashboard/Dashboard.jsx

import React, { useState, useEffect, useCallback } from 'react';
import './Dashboard.css';
import { useNavigate } from 'react-router-dom';
import { LogOut } from 'lucide-react';
import LiveStreamContent from './LiveStreamContent';
import VideoLogTable from './VideoLogTable';
import DangerZoneSelector from './DangerZoneSelector';

export default function Dashboard() {
  // — 상태
  const [showLogoutModal, setShowLogoutModal] = useState(false);
  const [currentTime,    setCurrentTime]    = useState('');
  const [logs,           setLogs]           = useState([]);
  const [activeId,       setActiveId]       = useState(null);
  const [loading,        setLoading]        = useState(false);
  const [error,          setError]          = useState(null);

  // 위험 모드 토글 & 메시지
  const [isDangerMode,   setIsDangerMode]   = useState(false);
  const [showInstruction, setShowInstruction] = useState(false);
  const [showComplete,    setShowComplete]    = useState(false);
  const [selectedZone,    setSelectedZone]    = useState([]);

  const navigate = useNavigate();

  // — 1) 현재 시간 갱신
  useEffect(() => {
    const timer = setInterval(() => {
      const now      = new Date();
      const year     = now.getFullYear();
      const month    = String(now.getMonth()+1).padStart(2,'0');
      const date     = String(now.getDate()).padStart(2,'0');
      const dayNames = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'];
      const day      = dayNames[now.getDay()];
      let   h        = now.getHours();
      const m        = String(now.getMinutes()).padStart(2,'0');
      const ampm     = h>=12?'PM':'AM';
      if (h>12) h -= 12;
      if (h===0) h = 12;
      setCurrentTime(`${year}-${month}-${date} (${day}) / ${ampm}-${h}:${m}`);
    },1000);
    return () => clearInterval(timer);
  },[]);

  // 2) Firestore 이벤트 로그 가져오기 (showLoading 플래그)
  const fetchLogs = useCallback(async (showLoading=false) => {
    if (showLoading) setLoading(true);
    setError(null);
    try {
      const res = await fetch('http://localhost:8000/api/events?limit=50');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setLogs(data);
      if (data.length) setActiveId(data[0].id);
    } catch(e) {
      console.error(e);
      setError('로그를 불러오는 중 오류가 발생했습니다.');
    } finally {
      if (showLoading) setLoading(false);
    }
  },[]);
// 3) 최초 마운트 시에만 로딩 표시
  useEffect(() => { fetchLogs(true); }, [fetchLogs]);// 최초 로드 때만 showLoading=true
 // 4) 폴링: 5초마다 quietly 데이터 갱신 
  useEffect(() => {
    const interval = setInterval(() => fetchLogs(false), 5000);
    return () => clearInterval(iv);
  }, [fetchLogs]);

  // — 3) 로그아웃 처리
  const handleLogoutConfirm = () => {
    setShowLogoutModal(false);
    navigate('/login');
  };

  // — 4) 위험 구역 설정 시작
  const startDangerMode = () => {
    setIsDangerMode(true);
    setShowInstruction(true);
    setTimeout(() => setShowInstruction(false), 3000);
  };

  // — 5) 위험 구역 설정 완료
  const handleDangerComplete = coords => {
    setSelectedZone(coords);
    setShowComplete(true);
    setTimeout(() => setShowComplete(false), 2000);
    setIsDangerMode(false);
    // TODO: POST API 호출 주석 해제 후 실제 저장
    // fetch('http://localhost:8000/api/danger-zones', { … })
  };

  return (
    <div className="dashboard">
      {/* 상단 헤더 */}
      <div className="header-bar">
        <div className="logo">GUARD-4</div>
        <div className="right-info">
          <div className="date-time">{currentTime}</div>
          <button className="logout-btn" onClick={()=>setShowLogoutModal(true)}>
            <LogOut size={18}/> Logout
          </button>
        </div>
      </div>

      {/* 안내 메시지 */}
      {showInstruction && (
        <div className="center-message">
          ⚠️ 화면을 클릭하여 점을 찍고 위험 구역을 설정하세요!
        </div>
      )}
      {showComplete && (
        <div className="center-message">
          ✅ 위험 구역이 설정되었습니다!
        </div>
      )}

      {/* 메인 레이아웃 */}
      <div className="main-layout">
        {/* 좌측 패널 */}
        <div className="left-panel">
          <div className="live-stream-wrapper">
            {isDangerMode ? (
              <DangerZoneSelector onComplete={handleDangerComplete}/>
            ) : (
              <>
                <LiveStreamContent/>
                {selectedZone.length > 0 && (
                  <ZoneOverlay coords={selectedZone}/>
                )}
              </>
            )}
          </div>
        </div>

        {/* 우측: 로그 테이블 + 컨트롤 */}
        <div className="right-panel">
          {loading && logs.length===0 ? (
            <div className="loading">로그 불러오는 중...</div>
          ) : error ? (
            <div className="error">{error}</div>
          ) : (
            <VideoLogTable
              logs={logs}
              activeId={activeId}
              onSelect={setActiveId}
            />
          )}

          <div className="control-board">
            <h3>🛠️ 컨트롤 보드</h3>
            <button>정형 작업 모드</button>
            <button>비정형 작업 모드</button>
            <button onClick={startDangerMode}>
              위험 구역 설정
            </button>
          </div>
        </div>
      </div>

      {/* 로그아웃 모달 */}
      {showLogoutModal && (
        <div className="logout-overlay">
          <div className="logout-modal">
            <div className="logout-title">로그아웃 하시겠습니까?</div>
            <div className="logout-buttons">
              <button className="logout-yes" onClick={handleLogoutConfirm}>
                네
              </button>
              <button className="logout-no" onClick={()=>setShowLogoutModal(false)}>
                아니요
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// 설정된 위험 구역을 계속 표시하는 오버레이
function ZoneOverlay({ coords }) {
  const ref = React.useRef(null);

  React.useEffect(() => {
    const canvas = ref.current;
    const ctx    = canvas.getContext('2d');
    const rect   = canvas.getBoundingClientRect();
    const dpr    = window.devicePixelRatio || 1;

    canvas.width  = rect.width  * dpr;
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
        pointerEvents: 'none'
      }}
    />
  );
}
