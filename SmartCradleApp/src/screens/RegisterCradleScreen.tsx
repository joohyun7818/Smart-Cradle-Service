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
import { setAgents, setSelectedAgent } from '../store/agentSlice';
import { cradleApi } from '../services/api';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import QRScanner from '../components/QRScanner';

type RegisterCradleScreenProps = {
  navigation: NativeStackNavigationProp<any>;
};

const RegisterCradleScreen: React.FC<RegisterCradleScreenProps> = ({ navigation }) => {
  const [cradleUuid, setCradleUuid] = useState('');
  const [loading, setLoading] = useState(false);
  const [scannerVisible, setScannerVisible] = useState(false);
  const dispatch = useDispatch();

  const handleRegister = async () => {
    if (!cradleUuid || cradleUuid.trim().length === 0) {
      Alert.alert('오류', '요람 UUID를 입력해주세요.');
      return;
    }

    setLoading(true);

    try {
      const response = await cradleApi.registerCradle(cradleUuid.trim());
      
      if (response.success && response.agent) {
        // 등록 성공
        Alert.alert(
          '성공',
          '요람이 등록되었습니다!',
          [
            {
              text: '확인',
              onPress: async () => {
                // 요람 목록 새로고침
                try {
                  const agents = await cradleApi.getAgents();
                  dispatch(setAgents(agents));
                  
                  // 방금 등록한 요람 선택
                  dispatch(setSelectedAgent(response.agent));
                  
                  // 대시보드로 이동
                  navigation.navigate('Dashboard');
                } catch (error) {
                  console.error('요람 목록 조회 실패:', error);
                  navigation.goBack();
                }
              },
            },
          ]
        );
      } else {
        throw new Error(response.message || '요람 등록에 실패했습니다.');
      }
    } catch (error: any) {
      const errorMessage = error.response?.data?.message || error.message || '요람 등록에 실패했습니다.';
      Alert.alert('등록 실패', errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleScanQR = () => {
    setScannerVisible(true);
  };

  const handleQRScanned = (data: string) => {
    setCradleUuid(data);
    setScannerVisible(false);
    Alert.alert('성공', 'QR 코드를 스캔했습니다. 등록 버튼을 눌러주세요.');
  };

  return (
    <KeyboardAvoidingView
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      style={styles.container}
    >
      <View style={styles.content}>
        <Text style={styles.title}>요람 등록</Text>
        <Text style={styles.subtitle}>Smart Cradle</Text>

        <View style={styles.infoBox}>
          <Text style={styles.infoIcon}>📱</Text>
          <Text style={styles.infoText}>
            요람 기기에 표시된 UUID를 입력하거나{'\n'}
            QR 코드를 스캔하세요.
          </Text>
        </View>

        <View style={styles.inputContainer}>
          <Text style={styles.label}>요람 UUID</Text>
          <TextInput
            style={styles.input}
            placeholder="예: abc123def456"
            value={cradleUuid}
            onChangeText={setCradleUuid}
            autoCapitalize="none"
            autoCorrect={false}
            editable={!loading}
          />
        </View>

        <TouchableOpacity
          style={[styles.button, loading && styles.buttonDisabled]}
          onPress={handleRegister}
          disabled={loading}
        >
          <Text style={styles.buttonText}>
            {loading ? '등록 중...' : '요람 등록'}
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.qrButton}
          onPress={handleScanQR}
          disabled={loading}
        >
          <Text style={styles.qrButtonText}>📷 QR 코드 스캔</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.backButton}
          onPress={() => navigation.goBack()}
          disabled={loading}
        >
          <Text style={styles.backButtonText}>취소</Text>
        </TouchableOpacity>

        <View style={styles.helpBox}>
          <Text style={styles.helpTitle}>💡 도움말</Text>
          <Text style={styles.helpText}>
            • 요람 기기를 먼저 전원에 연결하고 네트워크에 연결하세요.{'\n'}
            • UUID는 요람 기기의 디스플레이에 표시됩니다.{'\n'}
            • 문제가 있으면 요람 기기를 재시작해보세요.
          </Text>
        </View>
      </View>

      <QRScanner
        visible={scannerVisible}
        onClose={() => setScannerVisible(false)}
        onScan={handleQRScanned}
      />
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
    padding: 20,
    paddingTop: 60,
  },
  title: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#4A90E2',
    textAlign: 'center',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 18,
    color: '#666',
    textAlign: 'center',
    marginBottom: 30,
  },
  infoBox: {
    backgroundColor: '#E3F2FD',
    borderRadius: 15,
    padding: 20,
    marginBottom: 30,
    alignItems: 'center',
  },
  infoIcon: {
    fontSize: 40,
    marginBottom: 10,
  },
  infoText: {
    fontSize: 14,
    color: '#1976D2',
    textAlign: 'center',
    lineHeight: 20,
  },
  inputContainer: {
    marginBottom: 20,
  },
  label: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    marginBottom: 8,
  },
  input: {
    height: 50,
    backgroundColor: '#fff',
    borderRadius: 10,
    paddingHorizontal: 15,
    fontSize: 16,
    borderWidth: 1,
    borderColor: '#ddd',
  },
  button: {
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
  qrButton: {
    height: 50,
    backgroundColor: '#fff',
    borderRadius: 10,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 15,
    borderWidth: 2,
    borderColor: '#4A90E2',
  },
  qrButtonText: {
    color: '#4A90E2',
    fontSize: 16,
    fontWeight: '600',
  },
  backButton: {
    padding: 10,
    alignItems: 'center',
  },
  backButtonText: {
    color: '#999',
    fontSize: 16,
  },
  helpBox: {
    marginTop: 30,
    padding: 15,
    backgroundColor: '#fff',
    borderRadius: 10,
  },
  helpTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 10,
  },
  helpText: {
    fontSize: 13,
    color: '#666',
    lineHeight: 20,
  },
});

export default RegisterCradleScreen;
