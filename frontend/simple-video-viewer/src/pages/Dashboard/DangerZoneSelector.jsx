// src/pages/Dashboard/DangerZoneSelector.jsx
import React, { useRef, useState, useEffect } from 'react';
import LiveStreamContent from './LiveStreamContent';
import './DangerZoneSelector.css';

export default function DangerZoneSelector({ eventId, onComplete, onImageLoad }) {
  const canvasRef = useRef(null);
  const [points, setPoints] = useState([]); // [{ x, y, xRatio, yRatio }]

  // ① 캔버스에 점·폴리곤 렌더링
  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    const rect = canvas.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;

    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);
    ctx.clearRect(0, 0, rect.width, rect.height);

    // ● 찍힌 점
    ctx.fillStyle = 'rgba(255,0,0,0.7)';
    points.forEach(p => {
      ctx.beginPath();
      ctx.arc(p.x, p.y, 6, 0, Math.PI * 2);
      ctx.fill();
    });

    // ▶️ 폴리곤 (3개 이상일 때)
    if (points.length >= 3) {
      ctx.strokeStyle = 'rgba(255,0,0,0.9)';
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(points[0].x, points[0].y);
      points.slice(1).forEach(p => ctx.lineTo(p.x, p.y));
      ctx.closePath();
      ctx.fillStyle = 'rgba(255,0,0,0.2)';
      ctx.fill();
      ctx.stroke();
    }
  }, [points]);

  // ② 클릭 → 좌표 추가 & 부모 콜백
  const handleClick = e => {
    const rect = canvasRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    const next = [...points, { x, y }];
    setPoints(next);

    // 부모에는 비율 좌표만 전달
    onComplete(next);
  };

  return (
    <div className="dz-wrapper">
      {/* 실시간 영상 */}
      <LiveStreamContent
        eventId={eventId}
        onImageLoad={onImageLoad} // 이미지 크기 정보 부모로 전달
      />

      {/* 클릭만 받는 투명 캔버스 */}
      <canvas
        ref={canvasRef}
        className="dz-canvas"
        onClick={handleClick}
      />
    </div>
  );
}
