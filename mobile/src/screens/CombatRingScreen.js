/**
 * CombatRingScreen - The main battle interface for myTIME
 *
 * Displays active call status, persona selector, and audio stream controls.
 * Bridges the Android SIP client to the Dojo Bridge for real-time
 * ElevenLabs voice synthesis.
 */

import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  StatusBar,
  FlatList,
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
  const [logs, setLogs] = useState([]);
  const bridge = useRef(new BridgeClient());

  const addLog = useCallback((entry) => {
    setLogs((prev) => [
      { id: Date.now().toString(), text: entry, time: new Date().toLocaleTimeString() },
      ...prev.slice(0, 49), // Keep last 50 entries
    ]);
  }, []);

  useEffect(() => {
    const client = bridge.current;

    client.onStatusUpdate = (msg) => {
      if (msg.status === 'streaming') {
        setStatus('STREAMING');
        addLog(`Actor (${activePersona}): ${msg.actor_text?.substring(0, 80)}...`);
      } else if (msg.status === 'done') {
        setStatus('READY');
        addLog('Audio stream complete');
      }
    };

    client.onAudioChunk = () => {
      // Audio chunks are handled by the native audio player module
      // This callback is for UI state tracking
    };

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
  }, [addLog, activePersona]);

  const handleCombat = (callerNumber, transcript) => {
    setStatus('ENGAGING');
    addLog(`Combat Ring activated - Persona: ${activePersona}`);
    bridge.current.requestCombat(callerNumber, transcript, activePersona);
  };

  const handleTestTTS = () => {
    setStatus('TESTING');
    addLog('Testing TTS connection...');
    bridge.current.requestTTS(
      'Hello, this is a test of the myTIME Combat Ring voice system.'
    );
  };

  const statusColor =
    status === 'READY'
      ? '#39ff14'
      : status === 'STREAMING'
      ? '#00f3ff'
      : status === 'ERROR'
      ? '#ff0040'
      : '#ff00ff';

  return (
    <View style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor="#0d0d0d" />

      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.title}>myTIME</Text>
        <Text style={styles.subtitle}>COMBAT RING</Text>
        <View style={[styles.statusDot, { backgroundColor: statusColor }]} />
        <Text style={[styles.statusText, { color: statusColor }]}>{status}</Text>
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
            onPress={() => setActivePersona(p.id)}>
            <Text style={styles.personaLabel}>{p.label}</Text>
            <Text style={styles.personaDesc}>{p.desc}</Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Action Buttons */}
      <View style={styles.actions}>
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
      </View>

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
    paddingVertical: 20,
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
  statusDot: {
    width: 12,
    height: 12,
    borderRadius: 6,
    marginTop: 12,
  },
  statusText: {
    fontSize: 12,
    marginTop: 4,
    letterSpacing: 2,
  },
  personaRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginVertical: 16,
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
    gap: 12,
    marginVertical: 16,
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
  btnDisabled: {
    opacity: 0.4,
  },
  logContainer: {
    flex: 1,
    marginTop: 8,
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
