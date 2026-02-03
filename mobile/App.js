/**
 * myTIME Mobile - Combat Ring Client
 *
 * React Native entry point for the Android SIP/VOIP client.
 * Bridges to the Dojo Bridge service for ElevenLabs voice synthesis.
 */

import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import CombatRingScreen from './src/screens/CombatRingScreen';

const Stack = createNativeStackNavigator();

const App = () => {
  return (
    <NavigationContainer>
      <Stack.Navigator
        screenOptions={{
          headerShown: false,
          contentStyle: { backgroundColor: '#0d0d0d' },
        }}>
        <Stack.Screen name="CombatRing" component={CombatRingScreen} />
      </Stack.Navigator>
    </NavigationContainer>
  );
};

export default App;
