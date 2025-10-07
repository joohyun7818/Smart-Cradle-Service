import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  Alert,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { cradleApi } from '../services/api';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';

type RegisterScreenProps = {
  navigation: NativeStackNavigationProp<any>;
};

const RegisterScreen: React.FC<RegisterScreenProps> = ({ navigation }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);

  const handleRegister = async () => {
    // 유효성 검사
    if (!username || !password || !confirmPassword) {
      Alert.alert('오류', '모든 필드를 입력해주세요.');
      return;
    }

    if (username.length < 3) {
      Alert.alert('오류', '아이디는 3자 이상이어야 합니다.');
      return;
    }

    if (password.length < 4) {
      Alert.alert('오류', '비밀번호는 4자 이상이어야 합니다.');
      return;
    }

    if (password !== confirmPassword) {
      Alert.alert('오류', '비밀번호가 일치하지 않습니다.');
      return;
    }

    setLoading(true);

    try {
      const response = await cradleApi.register(username, password);
      
      if (response.success) {
        Alert.alert(
          '회원가입 성공',
          '회원가입이 완료되었습니다. 로그인해주세요.',
          [
            {
              text: '확인',
              onPress: () => navigation.navigate('Login'),
            },
          ]
        );
      } else {
        throw new Error(response.message || '회원가입에 실패했습니다.');
      }
    } catch (error: any) {
      const errorMessage = error.response?.data?.error || error.message || '회원가입에 실패했습니다.';
      Alert.alert('회원가입 실패', errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleBackToLogin = () => {
    navigation.navigate('Login');
  };

  return (
    <KeyboardAvoidingView
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      style={styles.container}
    >
      <View style={styles.content}>
        <Text style={styles.title}>회원가입</Text>
        <Text style={styles.subtitle}>Smart Cradle</Text>

        <View style={styles.inputContainer}>
          <TextInput
            style={styles.input}
            placeholder="아이디 (3자 이상)"
            value={username}
            onChangeText={setUsername}
            autoCapitalize="none"
            editable={!loading}
          />
          <TextInput
            style={styles.input}
            placeholder="비밀번호 (4자 이상)"
            value={password}
            onChangeText={setPassword}
            secureTextEntry
            editable={!loading}
          />
          <TextInput
            style={styles.input}
            placeholder="비밀번호 확인"
            value={confirmPassword}
            onChangeText={setConfirmPassword}
            secureTextEntry
            editable={!loading}
            onSubmitEditing={handleRegister}
          />
        </View>

        <TouchableOpacity
          style={[styles.button, loading && styles.buttonDisabled]}
          onPress={handleRegister}
          disabled={loading}
        >
          <Text style={styles.buttonText}>
            {loading ? '회원가입 중...' : '회원가입'}
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.backButton}
          onPress={handleBackToLogin}
          disabled={loading}
        >
          <Text style={styles.backButtonText}>로그인으로 돌아가기</Text>
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  content: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  title: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#4A90E2',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 18,
    color: '#666',
    marginBottom: 40,
  },
  inputContainer: {
    width: '100%',
    marginBottom: 20,
  },
  input: {
    width: '100%',
    height: 50,
    backgroundColor: '#fff',
    borderRadius: 10,
    paddingHorizontal: 15,
    marginBottom: 15,
    fontSize: 16,
    borderWidth: 1,
    borderColor: '#ddd',
  },
  button: {
    width: '100%',
    height: 50,
    backgroundColor: '#4A90E2',
    borderRadius: 10,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 15,
  },
  buttonDisabled: {
    opacity: 0.6,
  },
  buttonText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: 'bold',
  },
  backButton: {
    padding: 10,
  },
  backButtonText: {
    color: '#4A90E2',
    fontSize: 16,
  },
});

export default RegisterScreen;
