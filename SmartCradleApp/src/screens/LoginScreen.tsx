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
import { useDispatch } from 'react-redux';
import { loginStart, loginSuccess, loginFailure } from '../store/authSlice';
import { cradleApi } from '../services/api';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';

type LoginScreenProps = {
  navigation: NativeStackNavigationProp<any>;
};

const LoginScreen: React.FC<LoginScreenProps> = ({ navigation }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const dispatch = useDispatch();

  const handleLogin = async () => {
    if (!username || !password) {
      Alert.alert('오류', '아이디와 비밀번호를 입력해주세요.');
      return;
    }

    setLoading(true);
    dispatch(loginStart());

    try {
      const response = await cradleApi.login(username, password);
      
      if (response.success && response.user) {
        dispatch(loginSuccess(response.user));
        // Redux 상태가 변경되면 AppNavigator에서 자동으로 Main으로 전환됩니다
      } else {
        throw new Error(response.message || '로그인에 실패했습니다.');
      }
    } catch (error: any) {
      const errorMessage = error.response?.data?.error || error.message || '로그인에 실패했습니다.';
      dispatch(loginFailure(errorMessage));
      Alert.alert('로그인 실패', errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = () => {
    navigation.navigate('Register');
  };

  return (
    <KeyboardAvoidingView
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      style={styles.container}
    >
      <View style={styles.content}>
        <Text style={styles.title}>스마트 아기 요람</Text>
        <Text style={styles.subtitle}>Smart Cradle</Text>

        <View style={styles.inputContainer}>
          <TextInput
            style={styles.input}
            placeholder="아이디"
            value={username}
            onChangeText={setUsername}
            autoCapitalize="none"
            editable={!loading}
          />
          <TextInput
            style={styles.input}
            placeholder="비밀번호"
            value={password}
            onChangeText={setPassword}
            secureTextEntry
            editable={!loading}
            onSubmitEditing={handleLogin}
          />
        </View>

        <TouchableOpacity
          style={[styles.button, loading && styles.buttonDisabled]}
          onPress={handleLogin}
          disabled={loading}
        >
          <Text style={styles.buttonText}>
            {loading ? '로그인 중...' : '로그인'}
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.registerButton}
          onPress={handleRegister}
          disabled={loading}
        >
          <Text style={styles.registerButtonText}>회원가입</Text>
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
  registerButton: {
    padding: 10,
  },
  registerButtonText: {
    color: '#4A90E2',
    fontSize: 16,
  },
});

export default LoginScreen;
