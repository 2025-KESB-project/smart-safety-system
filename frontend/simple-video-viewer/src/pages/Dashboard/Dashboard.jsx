// src/pages/Dashboard/Dashboard.jsx
import React, { useState, useEffect, useCallback, useRef } from 'react';

import { useNavigate } from 'react-router-dom';
import { LogOut } from 'lucide-react';
import LiveStreamContent from './LiveStreamContent';
import VideoLogTable from './VideoLogTable';
import DangerZoneSelector from './DangerZoneSelector';
import ConveyorMode       from './ConveyorMode';
import ZoneConfigPanel    from './ZoneConfigPanel';

// ⭐️ WebSocket 훅 임포트
import { useWebSocket } from '../../hooks/useWebSocket';

import './Dashboard.css';
import './DangerZoneSelector.css';
// ⚙️ WebSocket 서버 URL 정의
const WS_URL = 'ws://localhost:8000/ws/logs/';


export default function Dashboard() {

  // ─── 공통 상태 관리 ─────────────────────────────────
  // (로그아웃 모달, 완료 메시지, 안내 메시지, 현재 시간, 이벤트 로그, 컨베이어 상태 등)
  // — 상태
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
  const [imageSize,       setImageSize]       = useState(null);  // 이미지 크기 정보

  // 비디오 스트림 크기 참조 (영역 좌표 계산에 사용)
  const liveStreamRef = useRef(null);


      // ─── WebSocket 메시지 처리 콜백 ─────────────────────
  const handleWsMessage = useCallback((msg) => {
    if (msg && msg.id) {
      setLogs(prev => [...prev, msg]);
    }
  }, []);

  // ─── WebSocket 구독 및 상태 관리 ─────────────────────
  const { status: wsStatus, error: wsError } = useWebSocket(
    WS_URL,
    handleWsMessage,
    null,
    5000,
    3
  );


  // ─── 위험구역 설정 후 안내 메시지 자동 숨김 (3초 후) ─────────────────────
  useEffect(() => {
    if (!showInstruction) return;
    const t = setTimeout(() => setShowInstruction(false), 3000);
    return () => clearTimeout(t);
  }, [showInstruction]);

  // 1) 현재 시간 표시
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
      const res = await fetch('http://localhost:8000/api/logs?limit=50');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      console.log('API logs:', data); //디테일 내용
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


  const handleStartAutomatic = async () => {
    // 위험 이벤트(구역 침입 or 낙상) 확인
    if (logs.some(l => l.event_type === 'zone_intrusion' || l.event_type === 'fall')) {
      setPopupError(
        '⚠️ 위험 구역에 인원 감지 또는 낙상이 감지되어\n운전 모드로 전환할 수 없습니다.'
      );
      setTimeout(() => setPopupError(null), 3000);
      return;
    }
    await fetchLogs(false);
    await handleControl('http://localhost:8000/api/control/start_automatic');
  };

  const handleStartMaintenance = async () => {
    await handleControl('http://localhost:8000/api/control/start_maintenance');
  };
  const handleStop = async () => {
    await handleControl('http://localhost:8000/api/control/stop');
  };

  // 6-1) 위험 구역 목록 조회
  const fetchZones = useCallback(async () => {
    try {
      const res  = await fetch('http://localhost:8000/api/zones/');
      if (!res.ok) throw new Error(res.status);
      const data = await res.json();
      setZones(data);
    } catch (e) {
      console.error('구역 조회 실패', e);
    }
  }, []);
  useEffect(() => {
    if (!isDangerMode) fetchZones();
  }, [isDangerMode, fetchZones]);

  // 6-2) 위험 구역 생성 (사용자 입력 이름 우선 반영)
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
    const name = newZoneName.trim() || autoName;  // 사용자 입력값 우선 사용

    // selectedZone은 비율 좌표이므로 실제 이미지 좌표로 변환
    const pts = selectedZone.map(r => ({
      x: Math.round(r.xRatio * (imageSize?.naturalWidth || 800)),
      y: Math.round(r.yRatio * (imageSize?.naturalHeight || 600)),
    }));

    const payload = { id, zone_data: { name, points: pts } };
    const res = await fetch('http://localhost:8000/api/zones/', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify(payload),
    });
    if (!res.ok) {
      alert('위험 구역 생성 실패');
      return;
    }
    alert('✅ 새로운 위험 구역이 생성되었습니다!');
    await fetchZones();
    setShowComplete(true);
    setNewZoneName('');  // 입력창 초기화
  };

  // 6-3) 위험 구역 수정 (기존 이름 재조회 후 PUT)
  const handleUpdateZone = async () => {
    if (!selectedZoneId) return;
    let existingName = '';
    try {
      const resList = await fetch('http://localhost:8000/api/zones/');
      if (!resList.ok) throw new Error(resList.status);
      const list = await resList.json();
      existingName = list.find(z => z.id === selectedZoneId)?.name || '';
    } catch {
      existingName = zones.find(z => z.id === selectedZoneId)?.name || '';
    }

    // selectedZone은 비율 좌표이므로 실제 이미지 좌표로 변환
    const pts = selectedZone.map(r => ({
      x: Math.round(r.xRatio * (imageSize?.naturalWidth || 800)),
      y: Math.round(r.yRatio * (imageSize?.naturalHeight || 600)),
    }));

    const payload = { name: existingName, points: pts };
    const res = await fetch(`http://localhost:8000/api/zones/${selectedZoneId}`, {
      method:  'PUT',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify(payload),
    });
    if (!res.ok) {
      alert('위험 구역 업데이트 실패');
      return;
    }
    await fetchZones();
    setShowComplete(true);
  };

  // 6-4) 위험 구역 삭제 (확인 다이얼로그에 zone 이름 표시)
  const handleDeleteZone = async () => {
    if (!selectedZoneId) return;
    let targetName = '';
    try {
      const resList = await fetch('http://localhost:8000/api/zones/');
      if (!resList.ok) throw new Error(resList.status);
      const list = await resList.json();
      targetName = list.find(z => z.id === selectedZoneId)?.name || '';
    } catch {
      console.warn('삭제 전 서버 재조회 실패');
    }
    const displayName = targetName || '선택된 구역';
    if (!window.confirm(`${displayName}을 삭제하시겠습니까?`)) return;
    const res = await fetch(`http://localhost:8000/api/zones/${selectedZoneId}`, { method: 'DELETE' });
    if (!res.ok) {
      alert('위험 구역 삭제 실패');
      return;
    }
    setSelectedZoneId(null);
    await fetchZones();
    setShowComplete(true);
  };

  // 7) 위험 구역 설정 모드 진입
  const startDangerMode = () => {
    setIsDangerMode(true);
    setConfigAction(null);
    setShowInstruction(false);
  };

  // 8) DangerZoneSelector에서 비율 좌표를 받아서 저장
  const handleDangerComplete = ratioPoints => {
    // DangerZoneSelector에서 이미 비율로 변환된 좌표를 받음
    setSelectedZone(ratioPoints);
    setShowInstruction(configAction === 'create');
  };

  // 8-1) 이미지 크기 정보 저장
  const handleImageLoad = (sizeInfo) => {
    setImageSize(sizeInfo);
  };

  // 9) ZoneConfigPanel 액션(조회/생성/수정/삭제) 선택
  const handleActionSelect = action => {
    setConfigAction(action);
    if (action === 'create') setNewZoneName('');  // 생성 모드 시 이름 초기화
    if (action !== 'view') setZones([]);
    setShowInstruction(action === 'create');
  };

  // 10) 생성/수정/삭제 확정
  const handleConfirm = async () => {
    if (configAction === 'create') await handleCreateZone();
    if (configAction === 'update') await handleUpdateZone();
    if (configAction === 'delete') await handleDeleteZone();
    setConfigAction(null);
    setSelectedZone([]);
    setSelectedZoneId(null);
    setIsDangerMode(false);
  };

  // 10) 완료 메시지 자동 숨김(3초후)
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
          <div
            className="live-stream-wrapper dz-wrapper"
            style={{ position: 'relative' }}
          >
            {isDangerMode && (configAction==='create'||configAction==='update')
              ? (
                <DangerZoneSelector
                  eventId={activeId}
                  onComplete={handleDangerComplete}
                  onImageLoad={handleImageLoad}
                />
              ) : (
                <LiveStreamContent eventId={activeId} onImageLoad={handleImageLoad} />
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
                <div className="zone-input-container">
                  <input
                    type="text"
                    placeholder="구역 이름을 입력하세요"
                    value={newZoneName}
                    onChange={e => setNewZoneName(e.target.value)}
                    className="zone-name-input"
                  />
                  <button className="confirm-btn" onClick={handleConfirm}>생성 완료</button>
                </div>
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
              <span>⚠️ 작업 실패 ⚠️</span>
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

// ZoneOverlay: 캔버스에 위험 구역 폴리곤을 그리는 컴포넌트
function ZoneOverlay({ ratios }) {
  const ref = useRef(null);
  useEffect(() => {
    const canvas = ref.current;
    const ctx    = canvas.getContext('2d');
    const rect   = canvas.getBoundingClientRect();
    const dpr    = window.devicePixelRatio || 1;
    canvas.width  = rect.width  * dpr;
    canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);
    ctx.clearRect(0,0,rect.width,rect.height);
    if (!ratios || ratios.length < 3) return;
    const pts = ratios.map(p => ({
      x: p.xRatio * rect.width,
      y: p.yRatio * rect.height
    }));
    ctx.fillStyle   = 'rgba(0,255,0,0.2)';
    ctx.strokeStyle = 'rgba(0,255,0,0.8)';
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