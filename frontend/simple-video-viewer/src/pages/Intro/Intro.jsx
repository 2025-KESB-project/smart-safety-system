import './Intro.css';
import { useNavigate, Link } from 'react-router-dom';
import bannerVideo from '../../assets/belt.mp4';
import streamVideo from '../../assets/Live.mp4';
import safetyimg from '../../assets/working zone.jpg';
import sampleCctv from '../../assets/example1.png'; // CCTV 썸네일
import serviceImg from '../../assets/description.png'; // 원하는 이미지 경로

export default function Intro() {
  const navigate = useNavigate();

  return (
    <div className="intro-page">
      {/* ===== 상단 헤더 ===== */}
      <header className="intro-header">
        <div className="intro-header-inner">
          <div className="logo">
            <Link to="/" style={{ textDecoration: 'none', color: 'inherit' }}>
              Safe Guard-4
            </Link>
          </div>

          <nav className="intro-nav">
            <a href="#streaming">실시간 영상 스트리밍</a>
            <a href="#safety">안전관리 시스템</a>
            <a href="#data">자료 관리 시스템</a>
            <a href="#service">고객 맞춤 서비스</a>
          </nav>

          <button className="login-btn" onClick={() => navigate('/login')}>
            login / sign up
          </button>
        </div>
      </header>

      {/* ===== 배경 영상 ===== */}
      <div className="intro-hero">
        <video className="hero-video" autoPlay muted loop playsInline>
          <source src={bannerVideo} type="video/mp4" />
          브라우저가 video 태그를 지원하지 않습니다.
        </video>
        <div className="hero-text">
          <h2>더욱 쉽고 빠르고 편리해지는 공장관리와 안전관리</h2>
          <p>SafeGuard-4로 체계적이고 효율적인 공장 관리와 안전 프로세스를 개선해 보세요</p>
          <div className="hero-buttons">
            <button className="hero-btn outline" onClick={() => navigate('/login')}>
              로그인 / 회원가입
            </button>
          </div>
        </div>
      </div>

      {/* ===== 실시간 영상 스트리밍 ===== */}
      <section id="streaming" className="intro-streaming">
        <div className="streaming-text">
          <h2>실시간 영상 스트리밍</h2>
          <p>CCTV로 현장을 실시간 확인할 수 있는 스트리밍 기능을 제공합니다.</p>
        </div>
        <div className="streaming-video">
          <div className="live-badge">
            <span className="dot"></span>
            Live
          </div>
          <video controls autoPlay muted loop playsInline>
            <source src={streamVideo} type="video/mp4" />
            브라우저가 video 태그를 지원하지 않습니다.
          </video>
        </div>
      </section>

      {/* ===== 안전관리 시스템 ===== */}
      <section id="safety" className="safety-section">
        <div className="safety-image">
          <img src={safetyimg} alt="Safety Management" />
          <div className="label-box worker" style={{ top: '20%', left: '5%' }}>worker</div>
          <div className="label-box danger" style={{ top: '42%', right: '45%' }}>Danger Zone</div>
        </div>
        <div className="safety-text">
          <h2>안전관리 시스템</h2>
          <p>
            Ai 기술을 통해서 작업자를 인식해 위험 구역 접근을 감지하고
            <br /> 관리자에게 경고 및 기록을 남겨 작업자의 안전을 강화합니다.
          </p>
        </div>
      </section>

      {/* ===== 자료관리 시스템 ===== */}
      <section id="data" className="data-section reverse">
        {/* 👉 왼쪽: CCTV + 로그카드 */}
        <div className="data-log">
          <h3>• 이상 기록 로그</h3>
          <div className="log-cards">
            <div className="log-card horizontal">
              <div className="log-video">
                <img src={sampleCctv} alt="CCTV snapshot" />
              </div>
              <div className="log-list">
                <div className="log-title">🚫 위험 구역 내 인원 감지</div>
                <div className="log-item">
                  <span className="icon">⚠️</span> 2025-07-16(수) / 15:09
                </div>
                <div className="log-item">
                  <span className="icon">⚠️</span> 2025-07-14(월) / 10:28
                </div>
                <div className="log-item">
                  <span className="icon">⚠️</span> 2025-07-09(수) / 17:02
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* 👉 오른쪽: 설명 */}
        <div className="data-text">
          <h2>자료관리 시스템</h2>
          <p>이상 징후 발생시 즉시 영상 로그 저장 및 확인 가능</p>
        </div>
      </section>

      {/* ===== 고객 맞춤 서비스 ===== */}
      <section id="service" className="service-section">
        {/* 왼쪽 이미지 */}
        <div className="service-image">
          <img src={serviceImg} alt="고객 맞춤 서비스" />
          </div>
          
          {/* 오른쪽 설명 */}
          <div className="service-text">
            <h2>고객 맞춤 서비스</h2>
            <p>
              현장 작업자와 관리자의 의견에 맞게 반영하여<br />
              관리자가 공장의 운영 환경에 맞는 맞춤형 기능과 서비스를 사용할 수 있게 합니다.
            </p>
          </div>
      </section>
    </div>
  );
}
