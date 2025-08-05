const { createProxyMiddleware } = require('http-proxy-middleware');

module.exports = function(app) {
  // /api 로 시작하는 요청만 모두 http://localhost:8000 으로 전달
  app.use(
    '/api',
    createProxyMiddleware({
      target: 'http://localhost:8000', // 백엔드 주소
      changeOrigin: true,               // Host 헤더를 타겟 URL에 맞추기
      pathRewrite: {
        '^/api': '',                    // /api 접두사를 제거하고 백엔드에 전달
      },
      logLevel: 'debug'                 // (선택) 콘솔에 디버그 로그 남기기
    })
  );
};
