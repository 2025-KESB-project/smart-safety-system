const WS_URL = `ws://${window.location.host}/ws`;

class WebSocketService {
  constructor() {
    this.logSocket = null;
    this.alertSocket = null;
    this.logListeners = new Set();
    this.alertListeners = new Set();
  }

  connectLogs(onOpen = () => {}, onError = () => {}) {
    if (this.logSocket && this.logSocket.readyState === WebSocket.OPEN) {
      return;
    }
    this.logSocket = new WebSocket(`${WS_URL}/logs`);

    this.logSocket.onopen = () => {
      console.log('Log WebSocket connected');
      onOpen();
    };

    this.logSocket.onmessage = (event) => {
      const message = JSON.parse(event.data);
      this.logListeners.forEach(listener => listener(message));
    };

    this.logSocket.onerror = (error) => {
      console.error('Log WebSocket error:', error);
      onError(error);
    };

    this.logSocket.onclose = () => {
      console.log('Log WebSocket disconnected');
      // Optional: implement reconnection logic here
    };
  }

  connectAlerts(onOpen = () => {}, onError = () => {}) {
    if (this.alertSocket && this.alertSocket.readyState === WebSocket.OPEN) {
      return;
    }
    this.alertSocket = new WebSocket(`${WS_URL}/alerts`);

    this.alertSocket.onopen = () => {
      console.log('Alert WebSocket connected');
      onOpen();
    };

    this.alertSocket.onmessage = (event) => {
      const message = JSON.parse(event.data);
      this.alertListeners.forEach(listener => listener(message));
    };

    this.alertSocket.onerror = (error) => {
      console.error('Alert WebSocket error:', error);
      onError(error);
    };

    this.alertSocket.onclose = () => {
      console.log('Alert WebSocket disconnected');
      // Optional: implement reconnection logic here
    };
  }

  addLogListener(listener) {
    this.logListeners.add(listener);
  }

  removeLogListener(listener) {
    this.logListeners.delete(listener);
  }

  addAlertListener(listener) {
    this.alertListeners.add(listener);
  }

  removeAlertListener(listener) {
    this.alertListeners.delete(listener);
  }

  disconnectLogs() {
    if (this.logSocket) {
      this.logSocket.close();
    }
  }

  disconnectAlerts() {
    if (this.alertSocket) {
      this.alertSocket.close();
    }
  }
}

// Export a singleton instance
const webSocketService = new WebSocketService();
export default webSocketService;
