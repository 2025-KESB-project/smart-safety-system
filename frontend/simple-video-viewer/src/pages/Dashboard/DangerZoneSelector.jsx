// src/pages/Dashboard/DangerZoneSelector.jsx
import React, { useRef, useState, useEffect } from 'react'
import LiveStreamContent from './LiveStreamContent'
import './DangerZoneSelector.css'
// src/pages/Dashboard/DangerZoneSelector.jsx
import React, { useRef, useState, useEffect } from 'react';
import LiveStreamContent from './LiveStreamContent';
import './DangerZoneSelector.css';

export default function DangerZoneSelector({ eventId, onComplete }) {
  const canvasRef = useRef(null)
  const [points, setPoints] = useState([]) // [{ x, y }, …] 픽셀 좌표

  // ① 캔버스에 점·폴리곤 렌더링
  useEffect(() => {
    const canvas = canvasRef.current
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
    const next = [...points, { x, y }]
    setPoints(next)
    onComplete(next) // 부모로 픽셀 좌표 그대로 전달
  }

  return (
    <div className="dz-wrapper">
      {/* 1) 실시간 영상은 LiveStreamContent 로 */}
      <LiveStreamContent eventId={eventId} />

      {/* 2) 클릭만 받는 완전 투명 캔버스 */}
      <canvas
        ref={canvasRef}
        className="dz-canvas"
        onClick={handleClick}
      />
    </div>
  )
}
