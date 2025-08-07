import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';   // ✅ 추가
import '../../assets/style.css';
import cctvImg from '../../assets/cctv.jpg';
import conveyorImg from '../../assets/conveyor.jpg';
import mainBg from '../../assets/main.jpg';

function Main() {
  const [showIntro, setShowIntro] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => {
      setShowIntro(false);
    }, 2500);
    return () => clearTimeout(timer);
  }, []);

  return (
    <>
      {showIntro ? (
        <div className="intro">
          <h1 className="intro-title">Conveyor Guard</h1>
          <div className="line"></div>
          <p className="intro-subtitle">Welcome to Conveyor Guard</p>
        </div>
      ) : (
        <div
          className="main-content"
          style={{
            backgroundImage: `url(${mainBg})`,
            backgroundSize: 'cover',
            backgroundPosition: 'center',
            backgroundRepeat: 'no-repeat',
          }}
        >
          <h1 className="main-title">Conveyor Guard</h1>
          <p className="main-subtitle">28일 후가 당신의 안전을 지켜드립니다.</p>
          <div className="card-container">
            
            {/* ✅ 첫 번째 카드 → 설명 페이지로 이동 */}
            <Link to="/intro" style={{ textDecoration: 'none' }}>
              <div className="card left-card">
                <img src={cctvImg} alt="시시티비 이미지" />
                <div className="card-overlay">
                  <div className="card-overlay-inner">
                    <h2 className="card-overlay-title">실시간 감지 시스템</h2>
                    <p className="card-overlay-subtext">
                      작업자의 위치를 실시간으로 인식해, 상황에 따라 자동 감속 또는 정지하는 안전 제어 시스템입니다.
                      현장 안전을 위한 지능형 감지 및 제어 기술을 손쉽게 경험해보세요.
                    </p>
                  </div>
                </div>
              </div>
            </Link>

            {/* ✅ 두 번째 카드 → 로그인 페이지로 이동 */}
            <Link to="/login" style={{ textDecoration: 'none' }}>
              <div className="card right-card">
                <img src={conveyorImg} alt="컨베이어 이미지" />
                <div className="card-overlay">
                  <div className="card-overlay-inner">
                    <h2 className="card-overlay-title">로그인/회원가입</h2>
                  </div>
                </div>
              </div>
            </Link>

          </div>
        </div>
      )}
    </>
  );
}

export default Main;
