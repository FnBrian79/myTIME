/**
 * CallKeepService - Native Android ConnectionService integration
 *
 * Uses react-native-callkeep to register myTIME as a calling account
 * on Android. When the Combat Ring is active, incoming SIP calls are
 * intercepted and routed through the Dojo Bridge instead of the
 * default dialer.
 */

import RNCallKeep from 'react-native-callkeep';
import { Platform } from 'react-native';

const CALLKEEP_OPTIONS = {
  ios: {
    appName: 'myTIME',
  },
  android: {
    alertTitle: 'myTIME Combat Ring',
    alertDescription: 'Allow myTIME to manage calls for scam interception',
    cancelButton: 'Cancel',
    okButton: 'Activate',
    additionalPermissions: [],
    selfManaged: true,
    foregroundService: {
      channelId: 'com.mytime.dojo.combat',
      channelName: 'Combat Ring Active',
      notificationTitle: 'myTIME Combat Ring',
      notificationIcon: 'ic_launcher',
    },
  },
};

class CallKeepService {
  constructor(bridgeClient) {
    this.bridge = bridgeClient;
    this.activeCallId = null;
    this.initialized = false;
  }

  async setup() {
    if (Platform.OS !== 'android') {
      console.warn('[CallKeep] Only Android is supported for myTIME');
      return;
    }

    try {
      await RNCallKeep.setup(CALLKEEP_OPTIONS);
      this.initialized = true;
      this._registerListeners();
      console.log('[CallKeep] Initialized successfully');
    } catch (err) {
      console.error('[CallKeep] Setup failed:', err);
    }
  }

  _registerListeners() {
    // Incoming call detected by Android telecom
    RNCallKeep.addEventListener('didReceiveStartCallAction', ({ handle, callUUID }) => {
      this.activeCallId = callUUID;
      console.log(`[CallKeep] Outgoing call started: ${handle}`);
    });

    RNCallKeep.addEventListener('answerCall', ({ callUUID }) => {
      this.activeCallId = callUUID;
      console.log(`[CallKeep] Call answered: ${callUUID}`);
      // The combat ring is now active - audio routes through the bridge
    });

    RNCallKeep.addEventListener('endCall', ({ callUUID }) => {
      console.log(`[CallKeep] Call ended: ${callUUID}`);
      if (this.activeCallId === callUUID) {
        this.bridge.endSession();
        this.activeCallId = null;
      }
    });

    // Android-specific: call state changes
    RNCallKeep.addEventListener('didChangeAudioRoute', ({ output }) => {
      console.log(`[CallKeep] Audio route changed: ${output}`);
    });
  }

  /**
   * Display the incoming call UI via Android's native call screen.
   * Called when the Foreman triage detects a COMBAT_RING number.
   */
  displayIncomingCall(callerId, callerName = 'Scam Detected') {
    if (!this.initialized) {
      console.warn('[CallKeep] Not initialized');
      return null;
    }

    const callUUID = this._generateUUID();
    this.activeCallId = callUUID;

    RNCallKeep.displayIncomingCall(
      callUUID,
      callerId,
      callerName,
      'generic',
      true // hasVideo = true shows the full-screen UI
    );

    return callUUID;
  }

  /**
   * Report to Android that myTIME is actively on a call.
   * Keeps the foreground service alive and prevents the OS from killing the app.
   */
  reportConnected(callUUID = null) {
    const uuid = callUUID || this.activeCallId;
    if (uuid) {
      RNCallKeep.setCurrentCallActive(uuid);
    }
  }

  /**
   * End the current call via Android telecom.
   */
  endCall(callUUID = null) {
    const uuid = callUUID || this.activeCallId;
    if (uuid) {
      RNCallKeep.endCall(uuid);
      this.activeCallId = null;
    }
  }

  teardown() {
    RNCallKeep.removeEventListener('didReceiveStartCallAction');
    RNCallKeep.removeEventListener('answerCall');
    RNCallKeep.removeEventListener('endCall');
    RNCallKeep.removeEventListener('didChangeAudioRoute');
    this.initialized = false;
  }

  _generateUUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
      const r = (Math.random() * 16) | 0;
      const v = c === 'x' ? r : (r & 0x3) | 0x8;
      return v.toString(16);
    });
  }
}

export default CallKeepService;
