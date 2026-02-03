/**
 * BridgeClient - WebSocket client for the myTIME Dojo Bridge
 *
 * Connects to the FastAPI bridge service and streams ElevenLabs audio
 * in real-time to the Android client.
 */

const BRIDGE_WS_URL =
  process.env.BRIDGE_WS_URL || 'ws://10.0.2.2:8000/ws/stream';
const BRIDGE_HTTP_URL =
  process.env.BRIDGE_HTTP_URL || 'http://10.0.2.2:8000';

class BridgeClient {
  constructor() {
    this.ws = null;
    this.onAudioChunk = null;
    this.onStatusUpdate = null;
    this.onError = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
  }

  connect() {
    return new Promise((resolve, reject) => {
      this.ws = new WebSocket(BRIDGE_WS_URL);

      this.ws.onopen = () => {
        console.log('[BridgeClient] Connected to Dojo Bridge');
        this.reconnectAttempts = 0;
        resolve();
      };

      this.ws.onmessage = (event) => {
        if (typeof event.data === 'string') {
          const msg = JSON.parse(event.data);
          if (msg.error) {
            this.onError?.(msg.error);
          } else {
            this.onStatusUpdate?.(msg);
          }
        } else {
          // Binary audio chunk
          this.onAudioChunk?.(event.data);
        }
      };

      this.ws.onerror = (err) => {
        console.error('[BridgeClient] WebSocket error:', err);
        this.onError?.(err.message || 'WebSocket connection error');
        reject(err);
      };

      this.ws.onclose = () => {
        console.log('[BridgeClient] Disconnected');
        this._attemptReconnect();
      };
    });
  }

  /**
   * Request direct text-to-speech streaming.
   */
  requestTTS(text, voiceId = null) {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      throw new Error('Not connected to Dojo Bridge');
    }
    this.ws.send(
      JSON.stringify({
        action: 'tts',
        text,
        ...(voiceId && { voice_id: voiceId }),
      })
    );
  }

  /**
   * Trigger a full Combat Ring cycle:
   * Triage -> Actor persona response -> ElevenLabs TTS stream
   */
  requestCombat(callerNumber, transcript, persona = 'hazel') {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      throw new Error('Not connected to Dojo Bridge');
    }
    this.ws.send(
      JSON.stringify({
        action: 'combat',
        caller_number: callerNumber,
        transcript,
        persona,
      })
    );
  }

  disconnect() {
    this.maxReconnectAttempts = 0; // Prevent auto-reconnect
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  /**
   * Check bridge health via REST.
   */
  static async checkHealth() {
    const resp = await fetch(`${BRIDGE_HTTP_URL}/health`);
    return resp.json();
  }

  _attemptReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.log('[BridgeClient] Max reconnect attempts reached');
      return;
    }
    this.reconnectAttempts++;
    const delay = Math.pow(2, this.reconnectAttempts) * 1000;
    console.log(
      `[BridgeClient] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`
    );
    setTimeout(() => this.connect().catch(() => {}), delay);
  }
}

export default BridgeClient;
