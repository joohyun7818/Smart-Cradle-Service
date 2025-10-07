import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  RefreshControl,
  TouchableOpacity,
  Dimensions,
  Alert,
} from 'react-native';
import { useSelector, useDispatch } from 'react-redux';
import { RootState } from '../store';
import { setAgentStatus } from '../store/agentSlice';
import { cradleApi } from '../services/api';
import { AgentStatus } from '../types';
import VideoStream from '../components/VideoStream';

const { width } = Dimensions.get('window');

const DashboardScreen: React.FC = () => {
  const dispatch = useDispatch();
  const { selectedAgent, agentStatus } = useSelector((state: RootState) => state.agent);
  const [refreshing, setRefreshing] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());
  const [motorRunning, setMotorRunning] = useState(false);
  const [motorControlling, setMotorControlling] = useState(false);

  // 실시간 데이터 업데이트
  useEffect(() => {
    if (!selectedAgent) return;

    const fetchAgentStatus = async () => {
      try {
        const status = await cradleApi.getAgentStatus(selectedAgent.uuid);
        dispatch(setAgentStatus(status));
        setLastUpdate(new Date());
      } catch (error) {
        console.error('상태 조회 실패:', error);
      }
    };

    // 초기 로드
    fetchAgentStatus();

    // 2초마다 자동 업데이트
    const interval = setInterval(fetchAgentStatus, 2000);

    return () => clearInterval(interval);
  }, [selectedAgent, dispatch]);

  const onRefresh = async () => {
    if (!selectedAgent) return;

    setRefreshing(true);
    try {
      const status = await cradleApi.getAgentStatus(selectedAgent.uuid);
      dispatch(setAgentStatus(status));
      setLastUpdate(new Date());
    } catch (error) {
      console.error('새로고침 실패:', error);
    } finally {
      setRefreshing(false);
    }
  };

  const handleMotorControl = async (action: 'start' | 'stop') => {
    if (!selectedAgent) {
      Alert.alert('오류', '선택된 요람이 없습니다.');
      return;
    }

    try {
      setMotorControlling(true);
      await cradleApi.controlMotor(selectedAgent.uuid, action);
      setMotorRunning(action === 'start');
      Alert.alert('성공', `모터가 ${action === 'start' ? '시작' : '정지'}되었습니다.`);
    } catch (error: any) {
      Alert.alert('오류', error.response?.data?.error || '모터 제어에 실패했습니다.');
    } finally {
      setMotorControlling(false);
    }
  };

  const getTemperatureColor = (temp: number | null): string => {
    if (!temp) return '#999';
    if (temp >= 38) return '#E74C3C'; // 빨강 (위험)
    if (temp >= 37) return '#F39C12'; // 노랑 (주의)
    return '#27AE60'; // 초록 (정상)
  };

  const getDirectionColor = (direction: string | null): string => {
    if (!direction) return '#999';
    if (direction === '정면 유지 중') return '#27AE60';
    if (direction.includes('인식')) return '#E74C3C';
    return '#F39C12';
  };

  const getDirectionIcon = (direction: string | null): string => {
    if (!direction) return '❓';
    if (direction === '정면 유지 중') return '✅';
    if (direction.includes('인식 안됨') || direction.includes('인식 오류')) return '❌';
    return '⚠️';
  };

  if (!selectedAgent) {
    return (
      <View style={styles.container}>
        <Text style={styles.noAgentText}>요람을 선택해주세요</Text>
      </View>
    );
  }

  return (
    <ScrollView
      style={styles.container}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
      }
    >
      <View style={styles.header}>
        <Text style={styles.headerTitle}>실시간 모니터링</Text>
        <Text style={styles.lastUpdateText}>
          마지막 업데이트: {lastUpdate.toLocaleTimeString()}
        </Text>
      </View>

      {/* 비디오 스트림 카드 */}
      {selectedAgent && (
        <View style={styles.card}>
          <View style={styles.cardHeader}>
            <Text style={styles.cardTitle}>📹 실시간 영상</Text>
          </View>
          <View style={styles.cardContent}>
            <VideoStream
              streamUrl={cradleApi.getStreamUrl(selectedAgent.uuid)}
              width={width - 70}
              height={(width - 70) * 0.75}
            />
          </View>
        </View>
      )}

      {/* 온도 카드 */}
      <View style={styles.card}>
        <View style={styles.cardHeader}>
          <Text style={styles.cardTitle}>🌡️ 체온</Text>
        </View>
        <View style={styles.cardContent}>
          <Text
            style={[
              styles.temperatureText,
              { color: getTemperatureColor(agentStatus?.temperature || null) },
            ]}
          >
            {agentStatus?.temperature ? `${agentStatus.temperature.toFixed(1)}°C` : 'N/A'}
          </Text>
          <Text style={styles.statusLabel}>
            {!agentStatus?.temperature
              ? '데이터 없음'
              : agentStatus.temperature >= 38
              ? '높음 - 주의 필요'
              : agentStatus.temperature >= 37
              ? '약간 높음'
              : '정상'}
          </Text>
        </View>
      </View>

      {/* 얼굴 방향 카드 */}
      <View style={styles.card}>
        <View style={styles.cardHeader}>
          <Text style={styles.cardTitle}>👶 얼굴 방향</Text>
        </View>
        <View style={styles.cardContent}>
          <Text style={styles.directionIcon}>
            {getDirectionIcon(agentStatus?.direction || null)}
          </Text>
          <Text
            style={[
              styles.directionText,
              { color: getDirectionColor(agentStatus?.direction || null) },
            ]}
          >
            {agentStatus?.direction || '확인 중...'}
          </Text>
        </View>
      </View>

      {/* 울음 감지 카드 */}
      <View style={styles.card}>
        <View style={styles.cardHeader}>
          <Text style={styles.cardTitle}>🔊 울음 감지</Text>
        </View>
        <View style={styles.cardContent}>
          <Text style={styles.cryingText}>
            {agentStatus?.crying || '감지 안됨'}
          </Text>
        </View>
      </View>

      {/* 모터 제어 카드 */}
      <View style={styles.card}>
        <View style={styles.cardHeader}>
          <Text style={styles.cardTitle}>🔄 모터 제어</Text>
        </View>
        <View style={styles.cardContent}>
          <View style={styles.motorControlContainer}>
            <TouchableOpacity
              style={[
                styles.motorButton,
                styles.startButton,
                (motorRunning || motorControlling) && styles.disabledButton,
              ]}
              onPress={() => handleMotorControl('start')}
              disabled={motorRunning || motorControlling}
            >
              <Text style={styles.buttonText}>
                {motorControlling ? '제어 중...' : '시작'}
              </Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[
                styles.motorButton,
                styles.stopButton,
                (!motorRunning || motorControlling) && styles.disabledButton,
              ]}
              onPress={() => handleMotorControl('stop')}
              disabled={!motorRunning || motorControlling}
            >
              <Text style={styles.buttonText}>
                {motorControlling ? '제어 중...' : '정지'}
              </Text>
            </TouchableOpacity>
          </View>
          <Text style={styles.motorStatusText}>
            현재 상태: {motorRunning ? '작동 중' : '정지'}
          </Text>
        </View>
      </View>

      {/* 정보 카드 */}
      <View style={styles.infoCard}>
        <Text style={styles.infoTitle}>요람 정보</Text>
        <View style={styles.infoRow}>
          <Text style={styles.infoLabel}>UUID:</Text>
          <Text style={styles.infoValue}>{selectedAgent?.uuid.substring(0, 8)}...</Text>
        </View>
        <View style={styles.infoRow}>
          <Text style={styles.infoLabel}>IP:</Text>
          <Text style={styles.infoValue}>{selectedAgent?.ip}</Text>
        </View>
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  header: {
    backgroundColor: '#4A90E2',
    padding: 20,
    paddingTop: 60,
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#fff',
  },
  lastUpdateText: {
    fontSize: 12,
    color: '#fff',
    opacity: 0.8,
    marginTop: 5,
  },
  noAgentText: {
    textAlign: 'center',
    marginTop: 100,
    fontSize: 18,
    color: '#999',
  },
  card: {
    backgroundColor: '#fff',
    margin: 15,
    borderRadius: 15,
    padding: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  cardHeader: {
    marginBottom: 15,
  },
  cardTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
  },
  cardContent: {
    alignItems: 'center',
  },
  temperatureText: {
    fontSize: 48,
    fontWeight: 'bold',
    marginBottom: 10,
  },
  statusLabel: {
    fontSize: 16,
    color: '#666',
  },
  directionIcon: {
    fontSize: 48,
    marginBottom: 10,
  },
  directionText: {
    fontSize: 20,
    fontWeight: 'bold',
  },
  cryingText: {
    fontSize: 20,
    color: '#333',
  },
  infoCard: {
    backgroundColor: '#fff',
    margin: 15,
    borderRadius: 15,
    padding: 20,
    marginBottom: 30,
  },
  infoTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 15,
  },
  infoRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 10,
  },
  infoLabel: {
    fontSize: 14,
    color: '#666',
  },
  infoValue: {
    fontSize: 14,
    color: '#333',
    fontWeight: '500',
  },
  motorControlContainer: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    width: '100%',
    marginBottom: 15,
  },
  motorButton: {
    flex: 1,
    paddingVertical: 15,
    paddingHorizontal: 20,
    borderRadius: 10,
    marginHorizontal: 5,
    alignItems: 'center',
    justifyContent: 'center',
  },
  startButton: {
    backgroundColor: '#4CAF50',
  },
  stopButton: {
    backgroundColor: '#f44336',
  },
  disabledButton: {
    backgroundColor: '#cccccc',
    opacity: 0.6,
  },
  buttonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  motorStatusText: {
    fontSize: 14,
    color: '#666',
    textAlign: 'center',
  },
});

export default DashboardScreen;
