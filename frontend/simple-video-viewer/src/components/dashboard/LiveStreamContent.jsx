import React, { useRef } from 'react';
import '../../pages/Dashboard/Dashboard.css';  

export default function LiveStreamContent({ onImageLoad }) {
  
  const videoStreamUrl = "http://localhost:8000/api/streaming/video_feed";
  const imgRef = useRef(null);

  const handleImageLoad = () => {
    if (imgRef.current && onImageLoad) {
      const { naturalWidth, naturalHeight, clientWidth, clientHeight } = imgRef.current;
      onImageLoad({
        naturalWidth,
        naturalHeight,
        clientWidth,
        clientHeight
      });
    }
  };

  return (
    <div className="live-stream-container">
      <img
        ref={imgRef}
        src={videoStreamUrl}
        alt="실시간 영상 스트리밍"
        style={{ width: '100%', height: '100%', objectFit: 'cover' }}
        onLoad={handleImageLoad}
        onError={e => {
          e.target.alt = "스트림 연결 실패. 서버·CORS 설정을 확인하세요.";
        }}
      />
    </div>
  );
}
