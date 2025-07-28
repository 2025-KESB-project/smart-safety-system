// import logo from './logo.svg';
import './App.css';

function App() {
   // FastAPI 서버가 제공하는 실시간 영상 스트리밍 주소입니다.
  const videoStreamUrl = "http://localhost:8000/api/video_feed";

  return (
    <div className="App">
      {/*<header className="App-header">*/}
      {/*  /!*<img src={logo} className="App-logo" alt="logo" />*!/*/}
      {/*  /!*<p>*!/*/}
      {/*  /!*  Edit <code>src/App.js</code> and save to reload.*!/*/}
      {/*  /!*</p>*!/*/}
      {/*  /!*<a*!/*/}
      {/*  /!*  className="App-link"*!/*/}
      {/*  /!*  href="https://reactjs.org"*!/*/}
      {/*  /!*  target="_blank"*!/*/}
      {/*  /!*  rel="noopener noreferrer"*!/*/}
      {/*  /!*>*!/*/}
      {/*  /!*  Learn React*!/*/}
      {/*  /!*</a>*!/*/}
      {/*</header>*/}
      <main className="video-container">
        <img
            src={videoStreamUrl}
            alt="실시간 영상 스트리밍"
            width="800"
            onError={(e) => {
             // 만약 서버에 연결할 수 없으면, 이 메시지가 대신 보입니다.
            e.target.alt = "영상 스트림에 연결할 수 없습니다. FastAPI 서버가 켜져 있는지, CORS설정이 올바른지 확인하세요.";
        }}
/>
      </main>
    </div>
  );
}

export default App;
