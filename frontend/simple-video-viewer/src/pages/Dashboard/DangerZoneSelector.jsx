// src/pages/Dashboard/DangerZoneSelector.jsx
import React, { useRef, useState, useEffect } from 'react'
import LiveStreamContent from './LiveStreamContent'
import './DangerZoneSelector.css'
// src/pages/Dashboard/DangerZoneSelector.jsx
import React, { useRef, useState, useEffect } from 'react';
import LiveStreamContent from './LiveStreamContent';
import './DangerZoneSelector.css';

export default function DangerZoneSelector({ eventId, onComplete, onImageLoad }) {
  const canvasRef = useRef(null)
  const [points, setPoints] = useState([]) // [{ x, y }, …] 픽셀 좌표
  const [imageSize, setImageSize] = useState(null)

  // 이미지 크기 정보 저장
  const handleImageLoad = (sizeInfo) => {
    setImageSize(sizeInfo);
    if (onImageLoad) {
      onImageLoad(sizeInfo);
    }
  };

  // ① 캔버스에 점·폴리곤 렌더링
  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return;
    
    const ctx    = canvas.getContext('2d')
    const rect   = canvas.getBoundingClientRect()
    const dpr    = window.devicePixelRatio || 1

    canvas.width  = rect.width  * dpr
    canvas.height = rect.height * dpr
    ctx.scale(dpr, dpr)
    ctx.clearRect(0, 0, rect.width, rect.height)

    // ● 찍힌 점
    ctx.fillStyle = 'rgba(255,0,0,0.7)'
    points.forEach(p => {
      ctx.beginPath()
      ctx.arc(p.x, p.y, 6, 0, Math.PI * 2)
      ctx.fill()
    })

    // ▶️ 폴리곤 (3개 이상일 때)
    if (points.length >= 3) {
      ctx.strokeStyle = 'rgba(255,0,0,0.9)'
      ctx.lineWidth   = 2
      ctx.beginPath()
      ctx.moveTo(points[0].x, points[0].y)
      points.slice(1).forEach(p => ctx.lineTo(p.x, p.y))
      ctx.closePath()
      ctx.fillStyle = 'rgba(255,0,0,0.2)'
      ctx.fill()
      ctx.stroke()
    }
  }, [points])

  // ② 클릭 → 좌표 추가 & 부모 콜백
  const handleClick = e => {
    const rect = canvasRef.current.getBoundingClientRect()
    const x    = e.clientX - rect.left
    const y    = e.clientY - rect.top
    
    // 캔버스 좌표를 비율로 변환
    const xRatio = x / rect.width
    const yRatio = y / rect.height
    
    const next = [...points, { x, y }]
    setPoints(next)
    
    // 부모에게 비율 좌표 전달
    const ratioPoints = next.map(p => ({
      xRatio: p.x / rect.width,
      yRatio: p.y / rect.height
    }))
    onComplete(ratioPoints)
  }

  return (
    <div className="dz-wrapper">
      {/* 1) 실시간 영상은 LiveStreamContent 로 */}
      <LiveStreamContent eventId={eventId} onImageLoad={handleImageLoad} />

      {/* 2) 클릭만 받는 완전 투명 캔버스 */}
      <canvas
        ref={canvasRef}
        className="dz-canvas"
        onClick={handleClick}
      />
    </div>
  )
}
