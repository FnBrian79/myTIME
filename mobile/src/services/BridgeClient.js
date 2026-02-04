/**
 * BridgeClient - WebSocket client for the myTIME Dojo Bridge
 *
 * Connects to the FastAPI bridge service and streams ElevenLabs audio
 * in real-time to the Android client. Supports Barge-In for
 * Master-Student live call takeover (5x XP mode).
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
    this.onBargeInAck = null;
    this.onSessionScored = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this._bargedIn = false;
    this._sessionId = null;
  }

  get isBargedIn() {
    return this._bargedIn;
  }

  get sessionId() {
    return this._sessionId;
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
          } else if (msg.status === 'barge_in_ack') {
            this._bargedIn = true;
            this._sessionId = msg.session_id;
            this.onBargeInAck?.(msg);
          } else if (msg.status === 'barge_out_ack') {
            this._bargedIn = false;
            this.onBargeInAck?.(msg);
          } else if (msg.status === 'session_scored') {
            this.onSessionScored?.(msg);
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
        this._bargedIn = false;
        this._attemptReconnect();
      };
    });
  }

  /**
   * Request direct text-to-speech streaming.
   */
  requestTTS(text, voiceId = null) {
    this._ensureConnected();
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
    this._ensureConnected();
    this.ws.send(
      JSON.stringify({
        action: 'combat',
        caller_number: callerNumber,
        transcript,
        persona,
      })
    );
  }

  /**
   * BARGE-IN: Human takes over the call from the AI persona.
   * Switches the session to "live" mode (5x XP via Steward).
   *
   * The bridge will:
   *  1. Stop the current ElevenLabs audio stream
   *  2. Notify the Steward that mode switched to "live"
   *  3. Route the caller's audio directly to the human's mic/speaker
   *  4. Respond with {"status": "barge_in_ack", "session_id": "..."}
   */
  bargeIn(userId = null) {
    this._ensureConnected();
    console.log('[BridgeClient] BARGE-IN requested');
    this.ws.send(
      JSON.stringify({
        action: 'barge_in',
        ...(userId && { user_id: userId }),
      })
    );
  }

  /**
   * BARGE-OUT: Hand the call back to the AI persona.
   * Resumes auto/handoff mode. The Steward logs the live segment duration.
   */
  bargeOut(persona = null) {
    this._ensureConnected();
    console.log('[BridgeClient] BARGE-OUT requested');
    this._bargedIn = false;
    this.ws.send(
      JSON.stringify({
        action: 'barge_out',
        ...(persona && { persona }),
      })
    );
  }

  /**
   * End the current combat session and trigger Steward scoring.
   */
  endSession() {
    this._ensureConnected();
    this._bargedIn = false;
    this.ws.send(JSON.stringify({ action: 'end_session' }));
  }

  disconnect() {
    this.maxReconnectAttempts = 0;
    this._bargedIn = false;
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

  _ensureConnected() {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      throw new Error('Not connected to Dojo Bridge');
    }
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
