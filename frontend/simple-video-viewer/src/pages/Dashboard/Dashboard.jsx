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

// ⚙️ WebSocket 서버 URL 정의
const WS_URL = 'ws://localhost:8000/ws/logs';


export default function Dashboard() {
  // 1. Zustand 스토어에서 상태와 액션을 가져옵니다.
  const {
    logs, zones, loading, error, popupError, operationMode,
    fetchLogs, fetchZones, addLog, handleControl, setPopupError
  } = useDashboardStore();

  // 2. Dashboard 컴포넌트 자체에서 관리해야 하는 UI 상태들
  const [showLogoutModal, setShowLogoutModal] = useState(false);
  const [currentTime,    setCurrentTime]    = useState('');
  const [logs,           setLogs]           = useState([]);
  const [activeId,       setActiveId]       = useState(null);
  const [loading,        setLoading]        = useState(false);
  const [error,          setError]          = useState(null);
  const [popupError,     setPopupError]     = useState(null);
  const [operationMode,  setOperationMode]  = useState(null);
  const [isOperating,     setIsOperating]     = useState(null);
  const [controlLoading,  setControlLoading]  = useState(false);

  // ─── 위험 구역 설정 모드 상태 ────────────────────────────────
  // (위험 구역 생성/수정/삭제를 위한 모드 전환 플래그)
  const [configAction,    setConfigAction]    = useState(null);
  // 위험 모드 토글 & 메시지
  const [isDangerMode,   setIsDangerMode]   = useState(false);
  const [showInstruction, setShowInstruction] = useState(false);
  const [showComplete,    setShowComplete]    = useState(false);

  const navigate = useNavigate();

  // 전체 zones 리스트, 편집/삭제 대상 ID, 그리고 미리보기 좌표(ratio)
  const [zones,           setZones]           = useState([]);
  const [selectedZoneId,  setSelectedZoneId]  = useState(null);
  const [selectedZone,    setSelectedZone]    = useState([]);
  const [newZoneName,     setNewZoneName]     = useState('');  // 사용자 입력 구역 이름 상태

  // 비디오 스트림 크기 참조 (영역 좌표 계산에 사용)
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

  // 1) 현재 시간 표시
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
  },[]);

  // 2) Firestore 이벤트 로그 가져오기 (showLoading 플래그)
  const fetchLogs = useCallback(async (showLoading=false) => {
    if (showLoading) setLoading(true);
    setError(null);
    try {
      const res = await fetch('http://localhost:8000/api/logs?limit=50');
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

  const handleControl = async (url, options = {}) => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(url, { method: 'POST', ...options });

      // 202 Accepted: 2차 확인이 필요한 경우
      if (res.status === 202) {
        const data = await res.json();
        if (data.confirmation_required && window.confirm(data.message)) {
          // 사용자가 확인하면, confirmed=true 파라미터와 함께 다시 요청
          const confirmedUrl = new URL(url);
          confirmedUrl.searchParams.append('confirmed', 'true');
          await handleControl(confirmedUrl.toString(), options);
        }
        return; // 2차 확인 흐름이 끝나면 여기서 함수 종료
      }

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || `HTTP ${res.status}`);
      }

      const data = await res.json();
      setOperationMode(data.operation_mode);

    } catch (e) {
      console.error(e);
      // 기존 setError 대신 새로운 popupError 상태를 사용합니다.
      const errorMessage = e.message || '명령을 실행하는 중 오류가 발생했습니다.';
      setPopupError(errorMessage);
      // 5초 후에 자동으로 팝업을 닫습니다.
      setTimeout(() => setPopupError(null), 5000);
    } finally {
      setLoading(false);
    }
  };

  const handleStartAutomatic = () => handleControl('http://localhost:8000/api/control/start_automatic');
  const handleStartMaintenance = () => handleControl('http://localhost:8000/api/control/start_maintenance');
  const handleStop = async () => {
    setControlLoading(true);
    try {
      const res = await fetch('http://localhost:8000/api/control/stop', { method: 'POST' });
      if (!res.ok) throw new Error(res.status);
      await fetchConveyorStatus();
    } catch {
      alert('컨베이어 정지 실패');
    } finally {
      setControlLoading(false);
    }
  };

  // ─── 6) 위험 구역 CRUD API ────────────────────────────────────────────────
  // 6-1) 조회 (GET /api/zones/)
  const fetchZones = useCallback(async () => {
    try {
      const res  = await fetch('http://localhost:8000/api/zones/', { method: 'GET' });
      if (!res.ok) throw new Error(res.status);
      const data = await res.json(); // [{ id, name, points:[{x,y},…] }, …]
      setZones(data);
    } catch (e) {
      console.error('구역 조회 실패', e);
    }
  }, []);
  useEffect(() => {
    if (!isDangerMode) fetchZones();
  }, [isDangerMode, fetchZones]);

  // 6-2) 생성 (POST /api/zones/)
  const handleCreateZone = async () => {
    // ① 새 ID/이름 생성
    const id   = `zone_${Date.now()}`;
    const name = `Zone ${zones.length + 1}`;

    // ② live-stream-wrapper 사이즈 측정
    const rect = liveStreamRef.current.getBoundingClientRect();

    // ③ normalized → pixel, 정수로 변환
    const intPoints = selectedZone.map(p => ({
      x: Math.round(p.xRatio * rect.width),
      y: Math.round(p.yRatio * rect.height)
    }));

    // ④ API 스펙에 맞춘 payload
    const payload = {
      id,
      zone_data: {
        name,
        points: intPoints
      }
    };

    console.log('▶️ POST payload:', payload);
    const res = await fetch('http://localhost:8000/api/zones/', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify(payload)
    });
    if (!res.ok) {
      console.error('❌ 생성 실패:', await res.text());
      alert('위험 구역 생성에 실패했습니다.');
      return;
    }
    alert('✅ 새로운 위험 구역이 생성되었습니다!');
    await fetchZones();
  };

  // 6-3) 업데이트 (PUT /api/zones/{zone_id})
  const handleUpdateZone = async () => {
    if (!selectedZoneId) return;
    // 기존 이름 꺼내오기
    const existing = zones.find(z => z.id === selectedZoneId) || {};

    // live-stream-wrapper 사이즈 재측정
    const rect = liveStreamRef.current.getBoundingClientRect();
    const intPoints = selectedZone.map(p => ({
      x: Math.round(p.xRatio * rect.width),
      y: Math.round(p.yRatio * rect.height)
    }));

    const payload = {
      zone_data: {
        name:   existing.name,
        points: intPoints
      }
    };

    console.log(`▶️ PUT payload:`, payload);
    const res = await fetch(
      `http://localhost:8000/api/zones/${selectedZoneId}`,
      {
        method:  'PUT',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify(payload)
      }
    );
    if (!res.ok) {
      console.error('❌ 업데이트 실패:', await res.text());
      alert('위험 구역 업데이트에 실패했습니다.');
      return;
    }
    alert('✅ 위험 구역이 업데이트되었습니다!');
    await fetchZones();
  };

  // 6-4) 삭제 (DELETE /api/zones/{zone_id})
  const handleDeleteZone = async () => {
    if (!selectedZoneId) return;
    if (!window.confirm('선택된 위험 구역을 삭제하시겠습니까?')) return;

    console.log(`▶️ DELETE zone ${selectedZoneId}`);
    const res = await fetch(
      `http://localhost:8000/api/zones/${selectedZoneId}`,
      { method: 'DELETE' }
    );
    if (!res.ok) {
      console.error('❌ 삭제 실패:', await res.text());
      alert('위험 구역 삭제에 실패했습니다.');
      return;
    }
    alert('✅ 위험 구역이 삭제되었습니다!');
    setSelectedZoneId(null);
    await fetchZones();
  };

  // 7) 위험 모드 진입
  const startDangerMode = () => {
    setIsDangerMode(true);
    setConfigAction(null);
    setShowInstruction(false);
  };

  // 8) DangerZoneSelector 완료
  const handleDangerComplete = ratios => {
    setSelectedZone(ratios);
  };

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
  // 9) 생성/업데이트 확정
  const handleConfirm = async () => {
    if (configAction === 'create') await handleCreateZone();
    if (configAction === 'update') await handleUpdateZone();
    if (configAction === 'delete') await handleDeleteZone();
    setConfigAction(null);
    setSelectedZone([]);
    setSelectedZoneId(null);
    setIsDangerMode(false);
  };

  // 11) 완료 메시지 자동 숨김 (3초 후)
  useEffect(() => {
    if (!showComplete) return;
    const t = setTimeout(() => setShowComplete(false), 3000);
    return () => clearTimeout(t);
  }, [showComplete]);

  // 로그아웃 처리
  const handleLogoutConfirm = () => {
    setShowLogoutModal(false);
    navigate('/login');
  };


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

      {/* WebSocket 연결 상태 표시 */}
      {/*<div className="ws-status">
        {wsStatus === 'connecting' && '🔄 연결 중...'}
        {wsStatus === 'open'       && '✅ 연결됨'}
        {wsStatus === 'closed'     && '⛔ 연결 끊김'}
        {wsStatus === 'error'      && `❌ 오류 발생: ${wsError?.message}`}
      </div>*/}

      {/* Main */}
      <div className="main-layout">
        {/* 왼쪽: 비디오 스트림 + 선택도구 + 오버레이 */}
        <div className="left-panel">
          <div className="live-stream-wrapper" ref={liveStreamRef}>
            {isDangerMode && (configAction==='create'||configAction==='update')
              ? (
                <DangerZoneSelector
                  eventId={activeId}
                  onComplete={handleDangerComplete}
                />
              ) : (
                <LiveStreamContent eventId={activeId} />
              )
            }

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

            {/* 저장된 zones 오버레이 */}
            {!isDangerMode && zones.map(z => (
              <ZoneOverlay
                key={z.id} ratios={z.points.map(p => ({ xRatio:p.x, yRatio:p.y }))}
              />
            ))}

            {/* 미리보기 오버레이 */}
            {!isDangerMode && selectedZone.length>0 && (
              <ZoneOverlay key="preview" ratios={selectedZone} />
            )}
          </div>
        </div>

        {/* 오른쪽: 로그 테이블 또는 설정 패널 */}
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
            onStartAutomatic={handleStartAutomatic}
            onStartMaintenance={handleStartMaintenance}
            onStop={handleStop}
            onDangerMode={startDangerMode}
          />
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
                onActionSelect={handleActionSelect}
                onDelete={handleDeleteZone}
                onCancel={() => setIsDangerMode(false)}
              />
              {configAction==='create' && (
                <>  {/* 생성 모드에만 입력창 및 버튼 */}
                  <input
                    type="text"
                    placeholder="구역 이름을 입력하세요"
                    value={newZoneName}
                    onChange={e => setNewZoneName(e.target.value)}
                    className="zone-name-input"
                  />
                  <button className="confirm-btn" onClick={handleConfirm}>생성 완료</button>
                </>
              )}
              {configAction==='update' && (
                <button className="confirm-btn" onClick={handleConfirm}>업데이트 완료</button>
              )}
              {configAction==='delete' && (
                <button className="confirm-btn" onClick={handleConfirm}>삭제 완료</button>
              )}
            </>
          )}
        </div>
      </div>


      {/* 에러 팝업 모달 */}
      {popupError && (
        <div className="error-popup-overlay">
          <div className="error-popup">
            <div className="error-popup-header">
              <span>⚠️ 작업 실패</span>
              <button onClick={() => setPopupError(null)}>&times;</button>
            </div>
            <div className="error-popup-content">
              {popupError}
            </div>
          </div>
        </div>
      )}

      {/* 로그아웃 확인 모달 */}
      {showLogoutModal && (
        <div className="logout-overlay">
          <div className="logout-modal">
            <div className="logout-title">로그아웃 하시겠습니까?</div>
            <div className="logout-buttons">
              <button className="logout-yes" onClick={() => navigate('/login')}>네</button>
              <button className="logout-no"  onClick={() => setShowLogoutModal(false)}>아니요</button>
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
// ZoneOverlay: 비율 좌표 → 픽셀 오버레이
function ZoneOverlay({ ratios }) {
  const ref = useRef(null);
  useEffect(() => {
    const canvas = ref.current;
    const ctx    = canvas.getContext('2d');
    const rect   = canvas.getBoundingClientRect();
    const dpr    = window.devicePixelRatio || 1;

    canvas.width  = rect.width  * dpr;
    canvas.width  = rect.width  * dpr;
    canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);

    ctx.clearRect(0, 0, rect.width, rect.height);
    if (coords.length < 3) return;

    if (!ratios || ratios.length < 3) return;
    const pts = ratios.map(p => ({
      x: p.xRatio * rect.width,
      y: p.yRatio * rect.height
    }));
    ctx.fillStyle   = 'rgba(255,0,0,0.2)';
    ctx.strokeStyle = 'rgba(255,0,0,0.8)';
    ctx.lineWidth   = 2;
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