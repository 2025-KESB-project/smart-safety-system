import React from 'react';
import './Dashboard.css';  

export default function LiveStreamContent() {
  
  const videoStreamUrl = "http://localhost:8000/api/video_feed";

  return (
    <div className="live-stream-container">
      <img
        src={videoStreamUrl}
        alt="실시간 영상 스트리밍"
        width="800"
        onError={e => {
          e.target.alt = "스트림 연결 실패. 서버·CORS 설정을 확인하세요.";
        }}
      />
    </div>
  );
}
