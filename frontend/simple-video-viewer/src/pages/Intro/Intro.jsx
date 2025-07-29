import './Intro.css';
import { useNavigate, Link } from 'react-router-dom'; // ✅ Link 추가
import bannerVideo from '../../assets/belt.mp4';

export default function Intro() {
  const navigate = useNavigate();

  return (
    <div className="intro-page">
      {/* ===== 상단 헤더 ===== */}
      <header className="intro-header">
        <div className="intro-header-inner">

          {/* ✅ 로고를 Link로 감싸기 */}
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

      {/* ===== 배경 영상 + 오버레이 ===== */}
      <div className="intro-hero">
        <video className="hero-video" autoPlay muted loop playsInline>
          <source src={bannerVideo} type="video/mp4" />
          브라우저가 video 태그를 지원하지 않습니다.
        </video>

        <div className="hero-text">
          <h2>더욱 쉽고 빠르고 편리해지는 공장관리와 안전관리</h2>
          <p>
            SafeGuard-4로 체계적이고 효율적인 공장 관리와 안전 프로세스를 개선해 보세요
          </p>

          {/* ✅ CTA 버튼 추가 */}
          <div className="hero-buttons">
            <button
              className="hero-btn outline"
              onClick={() => navigate('/login')}
            >
              로그인 / 회원가입
            </button>
          </div>
        </div>
      </div>

      {/* ===== 실제 섹션 영역 ===== */}
      <section id="streaming" className="intro-section">
        <h2>실시간 영상 스트리밍</h2>
        <p>CCTV로 현장을 실시간 확인할 수 있는 스트리밍 기능을 제공합니다.</p>
      </section>

      <section id="safety" className="intro-section">
        <h2>안전관리 시스템</h2>
        <p>이상 징후를 감지하면 경고와 기록을 남겨 안전을 강화합니다.</p>
      </section>

      <section id="data" className="intro-section">
        <h2>자료 관리 시스템</h2>
        <p>수집된 데이터를 효율적으로 분석하고 관리할 수 있습니다.</p>
      </section>

      <section id="service" className="intro-section">
        <h2>고객 맞춤 서비스</h2>
        <p>공장별 맞춤 설정과 서비스 제공으로 더욱 편리합니다.</p>
      </section>
    </div>
  );
}
