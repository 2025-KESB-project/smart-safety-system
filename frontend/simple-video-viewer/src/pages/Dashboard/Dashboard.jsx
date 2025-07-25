import './Dashboard.css';
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { LogOut } from 'lucide-react';
import LiveStreamContent from './LiveStreamContent';

export default function Dashboard() {
  const [showLogoutModal, setShowLogoutModal] = useState(false);
  const [currentTime, setCurrentTime] = useState('');
  const navigate = useNavigate();

  // ⏰ 시간 갱신
  useEffect(() => {
    const timer = setInterval(() => {
      const now = new Date();
      const year = now.getFullYear();
      const month = String(now.getMonth() + 1).padStart(2, '0');
      const date = String(now.getDate()).padStart(2, '0');
      const dayNames = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'];
      const day = dayNames[now.getDay()];
      let hours = now.getHours();
      const minutes = String(now.getMinutes()).padStart(2, '0');
      const ampm = hours >= 12 ? 'PM' : 'AM';
      if (hours > 12) hours = hours - 12;
      if (hours === 0) hours = 12;
      setCurrentTime(`${year}-${month}-${date} (${day}) / ${ampm}-${hours}:${minutes}`);
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const handleLogoutConfirm = () => {
    setShowLogoutModal(false);
    navigate('/login');
  };

  const handleLogoutCancel = () => {
    setShowLogoutModal(false);
  };

  return (
    <div className="dashboard">
      {/* 현재 시간 - 우측 상단 */}
      <div className="date-time top-right">{currentTime}</div>

      {/* 로그아웃 버튼 - 우측 하단 */}
      <div className="logout-button bottom-right">
        <button onClick={() => setShowLogoutModal(true)}>
          <LogOut size={20} /> Logout
        </button>
      </div>

      {/* 실시간 영상 스트림 */}
      <div className="live-stream-wrapper">
        <LiveStreamContent />
      </div>

      {/* 로그아웃 모달 */}
      {showLogoutModal && (
        <div className="logout-overlay">
          <div className="logout-modal">
            <div className="logout-title">로그아웃 하시겠습니까?</div>
            <div className="logout-buttons">
              <button className="logout-yes" onClick={handleLogoutConfirm}>네</button>
              <button className="logout-no" onClick={handleLogoutCancel}>아니요</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
