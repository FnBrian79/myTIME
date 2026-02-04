/**
 * CombatRingScreen - The main battle interface for myTIME
 *
 * Displays active call status, persona selector, audio stream controls,
 * and Barge-In/Barge-Out for Master-Student live mode (5x XP).
 */

import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  StatusBar,
  FlatList,
  Animated,
} from 'react-native';
import BridgeClient from '../services/BridgeClient';

const PERSONAS = [
  { id: 'hazel', label: 'Hazel', desc: 'Hard-of-Hearing Grandma' },
  { id: 'brian', label: 'Brian', desc: 'Tech-Illiterate Rambler' },
  { id: 'winner', label: 'Winner', desc: 'Excited PCH Enthusiast' },
];

const CombatRingScreen = () => {
  const [connected, setConnected] = useState(false);
  const [activePersona, setActivePersona] = useState('hazel');
  const [status, setStatus] = useState('IDLE');
  const [bargedIn, setBargedIn] = useState(false);
  const [sessionScore, setSessionScore] = useState(null);
  const [logs, setLogs] = useState([]);
  const bridge = useRef(new BridgeClient());
  const pulseAnim = useRef(new Animated.Value(1)).current;

  const addLog = useCallback((entry) => {
    setLogs((prev) => [
      { id: Date.now().toString(), text: entry, time: new Date().toLocaleTimeString() },
      ...prev.slice(0, 49),
    ]);
  }, []);

  // Pulse animation for live mode indicator
  useEffect(() => {
    if (bargedIn) {
      const pulse = Animated.loop(
        Animated.sequence([
          Animated.timing(pulseAnim, { toValue: 0.3, duration: 600, useNativeDriver: true }),
          Animated.timing(pulseAnim, { toValue: 1, duration: 600, useNativeDriver: true }),
        ])
      );
      pulse.start();
      return () => pulse.stop();
    } else {
      pulseAnim.setValue(1);
    }
  }, [bargedIn, pulseAnim]);

  useEffect(() => {
    const client = bridge.current;

    client.onStatusUpdate = (msg) => {
      if (msg.status === 'streaming') {
        setStatus('STREAMING');
        addLog(`Actor (${msg.mode || activePersona}): ${msg.actor_text?.substring(0, 80)}...`);
      } else if (msg.status === 'done') {
        setStatus(bargedIn ? 'LIVE' : 'READY');
        addLog('Audio stream complete');
      } else if (msg.status === 'stream_interrupted') {
        addLog('AI audio interrupted - YOU HAVE THE CONN');
      }
    };

    client.onBargeInAck = (msg) => {
      if (msg.status === 'barge_in_ack') {
        setBargedIn(true);
        setStatus('LIVE');
        addLog(`BARGE-IN: ${msg.message} (${msg.xp_multiplier}x XP)`);
      } else if (msg.status === 'barge_out_ack') {
        setBargedIn(false);
        setStatus('READY');
        addLog(`BARGE-OUT: ${msg.message} (${msg.live_seconds}s live)`);
      }
    };

    client.onSessionScored = (msg) => {
      setSessionScore(msg.steward);
      setStatus('SCORED');
      const steward = msg.steward;
      if (steward) {
        addLog(
          `SESSION SCORED: +${steward.credits_earned} credits, ` +
          `Level ${steward.new_level} (${steward.mode} mode, ${msg.total_duration}s)`
        );
      } else {
        addLog(`Session ended: ${msg.total_duration}s (${msg.live_seconds}s live)`);
      }
    };

    client.onAudioChunk = () => {};

    client.onError = (err) => {
      setStatus('ERROR');
      addLog(`Error: ${err}`);
    };

    client
      .connect()
      .then(() => {
        setConnected(true);
        setStatus('READY');
        addLog('Connected to Dojo Bridge');
      })
      .catch((err) => {
        addLog(`Connection failed: ${err.message}`);
      });

    return () => client.disconnect();
  }, [addLog, activePersona, bargedIn]);

  const handleCombat = (callerNumber, transcript) => {
    setStatus('ENGAGING');
    setSessionScore(null);
    addLog(`Combat Ring activated - Persona: ${activePersona}`);
    bridge.current.requestCombat(callerNumber, transcript, activePersona);
  };

  const handleBargeIn = () => {
    addLog('Requesting BARGE-IN...');
    bridge.current.bargeIn('Brian_Sovereign');
  };

  const handleBargeOut = () => {
    addLog('Requesting BARGE-OUT...');
    bridge.current.bargeOut(activePersona);
  };

  const handleEndSession = () => {
    addLog('Ending session...');
    bridge.current.endSession();
    setBargedIn(false);
  };

  const handleTestTTS = () => {
    setStatus('TESTING');
    addLog('Testing TTS connection...');
    bridge.current.requestTTS(
      'Hello, this is a test of the myTIME Combat Ring voice system.'
    );
  };

  const statusColor =
    status === 'LIVE'
      ? '#ff00ff'
      : status === 'READY'
      ? '#39ff14'
      : status === 'STREAMING'
      ? '#00f3ff'
      : status === 'SCORED'
      ? '#ffd700'
      : status === 'ERROR'
      ? '#ff0040'
      : '#888';

  const inCombat = ['STREAMING', 'LIVE', 'ENGAGING'].includes(status);

  return (
    <View style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor="#0d0d0d" />

      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.title}>myTIME</Text>
        <Text style={styles.subtitle}>COMBAT RING</Text>
        <View style={styles.statusRow}>
          <View style={[styles.statusDot, { backgroundColor: statusColor }]} />
          <Text style={[styles.statusText, { color: statusColor }]}>{status}</Text>
          {bargedIn && (
            <Animated.View style={[styles.liveBadge, { opacity: pulseAnim }]}>
              <Text style={styles.liveBadgeText}>5x XP</Text>
            </Animated.View>
          )}
        </View>
      </View>

      {/* Persona Selector */}
      <View style={styles.personaRow}>
        {PERSONAS.map((p) => (
          <TouchableOpacity
            key={p.id}
            style={[
              styles.personaBtn,
              activePersona === p.id && styles.personaBtnActive,
            ]}
            onPress={() => setActivePersona(p.id)}
            disabled={bargedIn}>
            <Text style={styles.personaLabel}>{p.label}</Text>
            <Text style={styles.personaDesc}>{p.desc}</Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Action Buttons */}
      <View style={styles.actions}>
        {!inCombat ? (
          <>
            <TouchableOpacity
              style={[styles.combatBtn, !connected && styles.btnDisabled]}
              onPress={() => handleCombat('+1234567890', 'Hello, I am calling about your account...')}
              disabled={!connected}>
              <Text style={styles.combatBtnText}>ENGAGE COMBAT RING</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={[styles.testBtn, !connected && styles.btnDisabled]}
              onPress={handleTestTTS}
              disabled={!connected}>
              <Text style={styles.testBtnText}>Test Voice</Text>
            </TouchableOpacity>
          </>
        ) : (
          <>
            {/* Barge-In / Barge-Out toggle */}
            {!bargedIn ? (
              <TouchableOpacity
                style={styles.bargeInBtn}
                onPress={handleBargeIn}>
                <Text style={styles.bargeInText}>BARGE IN</Text>
                <Text style={styles.bargeSubtext}>Take the conn (5x XP)</Text>
              </TouchableOpacity>
            ) : (
              <TouchableOpacity
                style={styles.bargeOutBtn}
                onPress={handleBargeOut}>
                <Text style={styles.bargeOutText}>HAND BACK TO AI</Text>
                <Text style={styles.bargeSubtext}>Resume {activePersona}</Text>
              </TouchableOpacity>
            )}

            {/* End Session */}
            <TouchableOpacity
              style={styles.endBtn}
              onPress={handleEndSession}>
              <Text style={styles.endBtnText}>END SESSION</Text>
            </TouchableOpacity>
          </>
        )}
      </View>

      {/* Score Card */}
      {sessionScore && (
        <View style={styles.scoreCard}>
          <Text style={styles.scoreTitle}>SESSION COMPLETE</Text>
          <View style={styles.scoreRow}>
            <Text style={styles.scoreLabel}>Credits</Text>
            <Text style={styles.scoreValue}>+{sessionScore.credits_earned}</Text>
          </View>
          <View style={styles.scoreRow}>
            <Text style={styles.scoreLabel}>Level</Text>
            <Text style={styles.scoreValue}>{sessionScore.new_level}</Text>
          </View>
          <View style={styles.scoreRow}>
            <Text style={styles.scoreLabel}>Mode</Text>
            <Text style={[styles.scoreValue, sessionScore.mode === 'live' && { color: '#ff00ff' }]}>
              {sessionScore.mode?.toUpperCase()} {sessionScore.mode === 'live' ? '(5x)' : '(1x)'}
            </Text>
          </View>
        </View>
      )}

      {/* Activity Log */}
      <View style={styles.logContainer}>
        <Text style={styles.logTitle}>Activity Log</Text>
        <FlatList
          data={logs}
          keyExtractor={(item) => item.id}
          renderItem={({ item }) => (
            <View style={styles.logEntry}>
              <Text style={styles.logTime}>{item.time}</Text>
              <Text style={styles.logText}>{item.text}</Text>
            </View>
          )}
        />
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0d0d0d',
    padding: 16,
  },
  header: {
    alignItems: 'center',
    paddingVertical: 16,
  },
  title: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#39ff14',
    letterSpacing: 4,
  },
  subtitle: {
    fontSize: 14,
    color: '#00f3ff',
    letterSpacing: 6,
    marginTop: 4,
  },
  statusRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 12,
    gap: 8,
  },
  statusDot: {
    width: 12,
    height: 12,
    borderRadius: 6,
  },
  statusText: {
    fontSize: 12,
    letterSpacing: 2,
  },
  liveBadge: {
    backgroundColor: '#ff00ff',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 4,
    marginLeft: 4,
  },
  liveBadgeText: {
    color: '#fff',
    fontSize: 11,
    fontWeight: 'bold',
    letterSpacing: 1,
  },
  personaRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginVertical: 12,
  },
  personaBtn: {
    flex: 1,
    marginHorizontal: 4,
    paddingVertical: 12,
    paddingHorizontal: 8,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#333',
    alignItems: 'center',
  },
  personaBtnActive: {
    borderColor: '#39ff14',
    backgroundColor: 'rgba(57, 255, 20, 0.1)',
  },
  personaLabel: {
    color: '#fff',
    fontWeight: 'bold',
    fontSize: 14,
  },
  personaDesc: {
    color: '#888',
    fontSize: 10,
    marginTop: 2,
    textAlign: 'center',
  },
  actions: {
    gap: 10,
    marginVertical: 12,
  },
  combatBtn: {
    backgroundColor: '#ff0040',
    paddingVertical: 16,
    borderRadius: 8,
    alignItems: 'center',
  },
  combatBtnText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: 'bold',
    letterSpacing: 2,
  },
  testBtn: {
    borderWidth: 1,
    borderColor: '#00f3ff',
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: 'center',
  },
  testBtnText: {
    color: '#00f3ff',
    fontSize: 14,
  },
  bargeInBtn: {
    backgroundColor: '#ff00ff',
    paddingVertical: 16,
    borderRadius: 8,
    alignItems: 'center',
  },
  bargeInText: {
    color: '#fff',
    fontSize: 20,
    fontWeight: 'bold',
    letterSpacing: 3,
  },
  bargeOutBtn: {
    backgroundColor: 'transparent',
    borderWidth: 2,
    borderColor: '#39ff14',
    paddingVertical: 16,
    borderRadius: 8,
    alignItems: 'center',
  },
  bargeOutText: {
    color: '#39ff14',
    fontSize: 16,
    fontWeight: 'bold',
    letterSpacing: 2,
  },
  bargeSubtext: {
    color: '#888',
    fontSize: 11,
    marginTop: 2,
  },
  endBtn: {
    borderWidth: 1,
    borderColor: '#ff0040',
    paddingVertical: 10,
    borderRadius: 8,
    alignItems: 'center',
  },
  endBtnText: {
    color: '#ff0040',
    fontSize: 13,
    letterSpacing: 1,
  },
  btnDisabled: {
    opacity: 0.4,
  },
  scoreCard: {
    backgroundColor: '#1a1a1a',
    borderWidth: 1,
    borderColor: '#ffd700',
    borderRadius: 8,
    padding: 12,
    marginBottom: 8,
  },
  scoreTitle: {
    color: '#ffd700',
    fontSize: 14,
    fontWeight: 'bold',
    letterSpacing: 2,
    textAlign: 'center',
    marginBottom: 8,
  },
  scoreRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 4,
  },
  scoreLabel: {
    color: '#888',
    fontSize: 13,
  },
  scoreValue: {
    color: '#39ff14',
    fontSize: 13,
    fontWeight: 'bold',
  },
  logContainer: {
    flex: 1,
    marginTop: 4,
  },
  logTitle: {
    color: '#666',
    fontSize: 12,
    letterSpacing: 2,
    marginBottom: 8,
  },
  logEntry: {
    flexDirection: 'row',
    paddingVertical: 4,
    borderBottomWidth: 1,
    borderBottomColor: '#1a1a1a',
  },
  logTime: {
    color: '#555',
    fontSize: 10,
    width: 70,
  },
  logText: {
    color: '#aaa',
    fontSize: 12,
    flex: 1,
  },
});

export default CombatRingScreen;
