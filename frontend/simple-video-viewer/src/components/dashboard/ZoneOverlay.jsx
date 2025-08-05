import React, { useRef, useEffect } from 'react';

// ZoneOverlay: 캔버스에 위험 구역 폴리곤을 그리는 컴포넌트
export default function ZoneOverlay({ zones, selectedZoneId }) {
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

    if (!zones || zones.length === 0) return;

    zones.forEach(zone => {
      if (!zone.points || zone.points.length < 3) return;

      const isSelected = zone.id === selectedZoneId;

      const pts = zone.points.map(p => ({
        x: p.xRatio * rect.width,
        y: p.yRatio * rect.height
      }));

      ctx.fillStyle = isSelected ? 'rgba(255, 165, 0, 0.3)' : 'rgba(0, 255, 0, 0.2)';
      ctx.strokeStyle = isSelected ? 'rgba(255, 165, 0, 1)' : 'rgba(0, 255, 0, 0.8)';
      ctx.lineWidth = isSelected ? 3 : 2;

      ctx.beginPath();
      ctx.moveTo(pts[0].x, pts[0].y);
      pts.slice(1).forEach(pt => ctx.lineTo(pt.x, pt.y));
      ctx.closePath();
      ctx.fill();
      ctx.stroke();
    });
  }, [zones, selectedZoneId]);

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