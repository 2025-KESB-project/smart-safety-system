import React, { useRef, useState, useEffect } from 'react';
import LiveStreamContent from './LiveStreamContent';
import './DangerZoneSelector.css';

export default function DangerZoneSelector({ eventId, onComplete, onImageLoad }) {
  const canvasRef = useRef(null);
  const [points, setPoints] = useState([]); // [{ x, y }, ...] 픽셀 좌표

  // ① 캔버스에 점·폴리곤 렌더링
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const rect = canvas.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;

    // HiDPI 디스플레이를 위한 캔버스 해상도 조정
    if (canvas.width !== rect.width * dpr || canvas.height !== rect.height * dpr) {
        canvas.width = rect.width * dpr;
        canvas.height = rect.height * dpr;
        ctx.scale(dpr, dpr);
    }

    ctx.clearRect(0, 0, rect.width, rect.height);

    // ● 찍힌 점
    ctx.fillStyle = 'rgba(255, 0, 0, 0.7)';
    points.forEach(p => {
      ctx.beginPath();
      ctx.arc(p.x, p.y, 5, 0, Math.PI * 2);
      ctx.fill();
    });

    // ▶️ 폴리곤 (2개 이상일 때 선, 3개 이상일 때 면)
    if (points.length >= 2) {
        ctx.strokeStyle = 'rgba(255, 0, 0, 0.9)';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(points[0].x, points[0].y);
        points.slice(1).forEach(p => ctx.lineTo(p.x, p.y));
        if (points.length >= 3) {
            ctx.closePath();
            ctx.fillStyle = 'rgba(255, 0, 0, 0.2)';
            ctx.fill();
        }
        ctx.stroke();
    }
  }, [points]);

  // ② 클릭 -> 좌표만 추가
  const handleCanvasClick = e => {
    const rect = canvasRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    setPoints(prevPoints => [...prevPoints, { x, y }]);
  };

  // ③ 완료 버튼 -> 부모 콜백 호출
  const handleComplete = () => {
    if (points.length < 3) {
      alert('위험 구역을 설정하려면 최소 3개 이상의 점을 찍어야 합니다.');
      return;
    }
    // 부모 컴포넌트에는 픽셀 좌표가 아닌 비율 좌표를 전달합니다.
    const rect = canvasRef.current.getBoundingClientRect();
    const ratioPoints = points.map(p => ({
      x: p.x / rect.width,
      y: p.y / rect.height,
    }));
    onComplete(ratioPoints);
  };

  // ④ 초기화 버튼 -> 모든 점 삭제
  const handleClear = () => {
    setPoints([]);
  };

  return (
    <div className="dz-wrapper">
      <LiveStreamContent eventId={eventId} onImageLoad={onImageLoad} />

      <canvas
        ref={canvasRef}
        className="dz-canvas"
        onClick={handleCanvasClick}
      />

      <div className="dz-controls">
        <p className="dz-info-text">영역을 클릭하여 점을 추가하세요.</p>
        <button onClick={handleComplete} className="dz-btn dz-btn-complete">완료</button>
        <button onClick={handleClear} className="dz-btn dz-btn-clear">초기화</button>
      </div>
    </div>
  );
}
