import './Intro.css';
import { useNavigate, Link, useLocation } from 'react-router-dom';
import bannerVideo from '../../assets/belt.mp4';
import streamVideo from '../../assets/Live.mp4';
import safetyimg from '../../assets/working zone.jpg';
import dangerzoneworker from '../../assets/Dangerzoneworker.jpg';
import select from '../../assets/select.jpg';


export default function Intro() {
  const navigate = useNavigate();
  const currentLocation = useLocation(); // 이름 변경

  return (
    <div className="intro-page">
      {/* ===== 상단 헤더 ===== */}
      <header className="intro-header">
        <div className="intro-header-inner">
          <div className="logo">
            <Link to="/" style={{ textDecoration: 'none', color: 'inherit' }}>
              Conveyor Guard
            </Link>
          </div>

          <nav className="intro-nav">
            <a href="#streaming" className={currentLocation.hash === '#streaming' ? 'active' : ''}>
              실시간 영상 스트리밍
            </a>
            <a href="#safety" className={currentLocation.hash === '#safety' ? 'active' : ''}>
              위험 구역 설정
            </a>
            <a href="#service" className={currentLocation.hash === '#service' ? 'active' : ''}>
              디지털 로토
            </a>
            <a href="#AI" className={currentLocation.hash === '#AI' ? 'active' : ''}>
              AI
            </a>
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
          <h2>경기대학교 SmartFactory-Project</h2>
          <p>28일 후 팀의 스마트공장 안전 시스템</p>
          <div className="hero-buttons">
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

      {/* ===== 위험구역 설정 ===== */}
      <section id="safety" className="safety-section">
        <div className="safety-image">
          <img src={safetyimg} alt="Safety Management" />
          <div className="label-box worker" style={{ top: '20%', left: '5%' }}>worker</div>
          <div className="label-box danger" style={{ top: '42%', right: '45%' }}>Danger Zone</div>
        </div>
        <div className="safety-text">
          <h2>위험 구역 설정</h2>
          <p>
            Ai 기술을 통해서 작업자를 인식해 위험 구역 접근을 감지하고
            <br /> 관리자에게 경고 및 기록을 남겨 작업자의 안전을 강화합니다.
          </p>
        </div>
      </section>

        {/* ===== 디지털 로토 설정 ===== */}
        <section id="service" className="danger-zone-section">
          <div className="streaming-text">
            <h2>디지털 로토</h2>
            <p>위험구역에서 정비중 일때 다른 작업자가 임의로 가동하지 못하게 막습니다.
            </p>
          </div>
          <div className="safety-image danger-zone">
            <img src={dangerzoneworker} alt="Danger Zone Worker" />
            <div className="label-box danger" style={{ top: '42%', right: '45%' }}>Danger Zone</div>
            <div className="alert-overlay">
              <div className="title">경고 알림</div>
              <div className="desc">위험구역 내
                <br />정비중인 작업자가 있습니다!
                <br />컨베이어 가동 불가능
              </div>
            </div>
          </div>
          </section>

            {/* ===== AI 기능 ===== */}
              <section id="select" className="ai-section">
                <div className="ai-visual">
                <div className="ai-card">AI 인식 시각화 영역</div>
              </div>

            <div className="streaming-text">
            <h2>AI 기능</h2>
            <p>AI를 통해 작업자를 놓치지 않고 인식합니다.</p>
           </div>
          </section>
      </div>
  );
}
