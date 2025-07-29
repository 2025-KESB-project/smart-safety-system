import React, { useRef, useState, useEffect } from 'react';
import './DangerZoneSelector.css';

export default function DangerZoneSelector({ onComplete }) {
  const canvasRef = useRef(null);
  const [points, setPoints] = useState([]);

  const streamUrl = "http://localhost:8000/api/video_feed";

  // points 배열이 바뀔 때마다 그리기
  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx    = canvas.getContext('2d');
    const rect   = canvas.getBoundingClientRect();
    const dpr    = window.devicePixelRatio || 1;

    // 내부 버퍼 크기 설정
    canvas.width  = rect.width  * dpr;
    canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);

    // 실제 CSS 크기 기준으로 초기화
    ctx.clearRect(0, 0, rect.width, rect.height);

    // 점 그리기
    ctx.fillStyle = 'rgba(255,0,0,0.7)';
    points.forEach(({ x, y }) => {
      ctx.beginPath();
      ctx.arc(x, y, 6, 0, Math.PI * 2);
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

  // 클릭 좌표 저장
  const handleClick = e => {
    const rect = canvasRef.current.getBoundingClientRect();
    setPoints(ps => [
      ...ps,
      { x: e.clientX - rect.left, y: e.clientY - rect.top }
    ]);
  };

  return (
    <div className="dz-wrapper">
      <img
        src={streamUrl}
        alt="실시간 영상"
        className="dz-img"
      />
      <canvas
        ref={canvasRef}
        className="dz-canvas"
        onClick={handleClick}
      />
      <button
        className="dz-complete-btn"
        onClick={() => onComplete(points)}
      >
        설정 완료
      </button>
    </div>
  );
}
