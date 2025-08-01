import React, { useRef, useState, useEffect } from 'react';
import './DangerZoneSelector.css';

export default function DangerZoneSelector({ onComplete }) {
  const canvasRef = useRef(null);
  const [points,  setPoints ] = useState([]);
  const streamUrl = 'http://localhost:8000/api/video_feed';

  // ① 캔버스 렌더
  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx    = canvas.getContext('2d');
    const rect   = canvas.getBoundingClientRect();
    const dpr    = window.devicePixelRatio || 1;
    canvas.width  = rect.width * dpr;
    canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);
    ctx.clearRect(0, 0, rect.width, rect.height);

    // 점 그리기
    ctx.fillStyle = 'rgba(255,0,0,0.7)';
    points.forEach(p => {
      ctx.beginPath();
      ctx.arc(p.x, p.y, 6, 0, Math.PI * 2);
      ctx.fill();
    });

    // 폴리곤 그리기
    if (points.length >= 3) {
      ctx.strokeStyle = 'rgba(255,0,0,0.9)';
      ctx.lineWidth   = 2;
      ctx.beginPath();
      ctx.moveTo(points[0].x, points[0].y);
      points.slice(1).forEach(p => ctx.lineTo(p.x, p.y));
      ctx.closePath();
      ctx.stroke();
      ctx.fillStyle = 'rgba(255,0,0,0.2)';
      ctx.fill();
    }
  }, [points]);

  // ② 캔버스 클릭 → 부모에 정규화된 좌표 즉시 전달
  const handleClick = e => {
    const rect = canvasRef.current.getBoundingClientRect();
    const newPt = { x: e.clientX - rect.left, y: e.clientY - rect.top };
    const next = [...points, newPt];
    setPoints(next);
    const normalized = next.map(p => ({
      xRatio: p.x / rect.width,
      yRatio: p.y / rect.height
    }));
    onComplete(normalized);
  };

  return (
    <div className="dz-wrapper">
      <img src={streamUrl} alt="실시간 영상" className="dz-img" />
      <canvas
        ref={canvasRef}
        className="dz-canvas"
        onClick={handleClick}
      />
    </div>
  );
}
