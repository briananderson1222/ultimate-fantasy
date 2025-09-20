import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TextInput,
  TouchableOpacity,
  Alert,
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import * as LocalAuthentication from 'expo-local-authentication';
import { Ionicons } from '@expo/vector-icons';

interface AuthFormData {
  email: string;
  password: string;
}

export default function AuthScreen() {
  const navigation = useNavigation();
  const [isLogin, setIsLogin] = useState(true);
  const [loading, setLoading] = useState(false);
  const [biometricSupported, setBiometricSupported] = useState(false);
  const [savedCredentials, setSavedCredentials] = useState(false);
  const [formData, setFormData] = useState<AuthFormData>({
    email: '',
    password: '',
  });

  useEffect(() => {
    checkBiometricSupport();
    checkSavedCredentials();
  }, []);

  const checkBiometricSupport = async () => {
    const hasHardware = await LocalAuthentication.hasHardwareAsync();
    const isEnrolled = await LocalAuthentication.isEnrolledAsync();
    setBiometricSupported(hasHardware && isEnrolled);
  };

  const checkSavedCredentials = async () => {
    try {
      const token = await AsyncStorage.getItem('uf_auth_token');
      const biometricEnabled = await AsyncStorage.getItem('uf_biometric_enabled');
      setSavedCredentials(!!(token && biometricEnabled === 'true'));
    } catch (error) {
      console.log('Error checking saved credentials:', error);
    }
  };

  const handleBiometricAuth = async () => {
    try {
      const result = await LocalAuthentication.authenticateAsync({
        promptMessage: 'Authenticate to access Ultimate Fantasy',
        cancelLabel: 'Cancel',
        fallbackLabel: 'Use Password',
      });

      if (result.success) {
        const token = await AsyncStorage.getItem('uf_auth_token');
        if (token) {
          navigation.navigate('Main' as never);
        } else {
          Alert.alert('Error', 'No saved session found. Please sign in.');
        }
      }
    } catch (error) {
      Alert.alert('Authentication Error', 'Failed to authenticate with biometrics');
    }
  };

  const handleSubmit = async () => {
    if (!formData.email || !formData.password) {
      Alert.alert('Error', 'Please fill in all fields');
      return;
    }

    setLoading(true);

    try {
      // Mock authentication - replace with actual API call
      await new Promise(resolve => setTimeout(resolve, 1000));

      // Mock successful authentication
      const mockToken = 'mock_jwt_token_' + Date.now();
      await AsyncStorage.setItem('uf_auth_token', mockToken);
      await AsyncStorage.setItem('uf_user_email', formData.email);

      // Offer biometric setup for new users
      if (biometricSupported && !savedCredentials) {
        Alert.alert(
          'Enable Biometric Authentication?',
          'Would you like to use fingerprint/face recognition for faster sign-in?',
          [
            { text: 'Not Now', style: 'cancel' },
            {
              text: 'Enable',
              onPress: async () => {
                await AsyncStorage.setItem('uf_biometric_enabled', 'true');
              },
            },
          ]
        );
      }

      navigation.navigate('Main' as never);
    } catch (error) {
      Alert.alert('Error', 'Authentication failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const toggleMode = () => {
    setIsLogin(!isLogin);
    setFormData({ email: '', password: '' });
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <View style={styles.content}>
        <View style={styles.header}>
          <Ionicons name="trophy" size={60} color="#2563eb" />
          <Text style={styles.title}>Ultimate Fantasy</Text>
          <Text style={styles.subtitle}>
            {isLogin ? 'Welcome back!' : 'Create your account'}
          </Text>
        </View>

        <View style={styles.form}>
          <View style={styles.inputContainer}>
            <Ionicons name="mail-outline" size={20} color="#666" style={styles.inputIcon} />
            <TextInput
              style={styles.input}
              placeholder="Email"
              value={formData.email}
              onChangeText={(text) => setFormData({ ...formData, email: text })}
              keyboardType="email-address"
              autoCapitalize="none"
              autoComplete="email"
            />
          </View>

          <View style={styles.inputContainer}>
            <Ionicons name="lock-closed-outline" size={20} color="#666" style={styles.inputIcon} />
            <TextInput
              style={styles.input}
              placeholder="Password"
              value={formData.password}
              onChangeText={(text) => setFormData({ ...formData, password: text })}
              secureTextEntry
              autoComplete="password"
            />
          </View>

          <TouchableOpacity
            style={[styles.button, loading && styles.buttonDisabled]}
            onPress={handleSubmit}
            disabled={loading}
          >
            {loading ? (
              <ActivityIndicator color="#fff" />
            ) : (
              <Text style={styles.buttonText}>
                {isLogin ? 'Sign In' : 'Sign Up'}
              </Text>
            )}
          </TouchableOpacity>

          {biometricSupported && savedCredentials && (
            <TouchableOpacity style={styles.biometricButton} onPress={handleBiometricAuth}>
              <Ionicons name="finger-print" size={24} color="#2563eb" />
              <Text style={styles.biometricText}>Use Biometric Authentication</Text>
            </TouchableOpacity>
          )}

          <TouchableOpacity style={styles.switchButton} onPress={toggleMode}>
            <Text style={styles.switchText}>
              {isLogin
                ? "Don't have an account? Sign Up"
                : 'Already have an account? Sign In'}
            </Text>
          </TouchableOpacity>
        </View>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8fafc',
  },
  content: {
    flex: 1,
    justifyContent: 'center',
    paddingHorizontal: 24,
  },
  header: {
    alignItems: 'center',
    marginBottom: 40,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#1e293b',
    marginTop: 12,
  },
  subtitle: {
    fontSize: 16,
    color: '#64748b',
    marginTop: 8,
  },
  form: {
    gap: 16,
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#fff',
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 4,
    borderWidth: 1,
    borderColor: '#e2e8f0',
  },
  inputIcon: {
    marginRight: 12,
  },
  input: {
    flex: 1,
    fontSize: 16,
    paddingVertical: 12,
    color: '#1e293b',
  },
  button: {
    backgroundColor: '#2563eb',
    paddingVertical: 16,
    borderRadius: 12,
    alignItems: 'center',
    marginTop: 8,
  },
  buttonDisabled: {
    opacity: 0.6,
  },
  buttonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  biometricButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 12,
    marginTop: 8,
  },
  biometricText: {
    color: '#2563eb',
    fontSize: 16,
    fontWeight: '500',
    marginLeft: 8,
  },
  switchButton: {
    alignItems: 'center',
    paddingVertical: 12,
    marginTop: 16,
  },
  switchText: {
    color: '#64748b',
    fontSize: 14,
  },
});