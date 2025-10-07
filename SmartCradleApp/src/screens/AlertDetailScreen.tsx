import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  ActivityIndicator,
  Image,
  Dimensions,
  TouchableOpacity,
} from 'react-native';
import { useRoute, useNavigation } from '@react-navigation/native';
import { cradleApi } from '../services/api';
import { LineChart } from 'react-native-chart-kit';

const { width } = Dimensions.get('window');

interface SensorData {
  timestamp: string;
  temperature: number | null;
  crying: string | null;
  direction: string | null;
}

interface VideoFrameInfo {
  id: number;
  timestamp: string;
}

interface AlertDetail {
  alert: {
    id: number;
    alert_type: string;
    alert_message: string;
    temperature: number | null;
    face_detected: boolean | null;
    resolved: boolean;
    created_at: string;
    resolved_at: string | null;
  };
  sensor_data: SensorData[];
  video_frames: VideoFrameInfo[];
  total_frames: number;
}

const AlertDetailScreen: React.FC = () => {
  const route = useRoute<any>();
  const navigation = useNavigation();
  const { alertId } = route.params;

  const [alertDetail, setAlertDetail] = useState<AlertDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [currentFrameIndex, setCurrentFrameIndex] = useState(0);

  useEffect(() => {
    fetchAlertDetail();
  }, [alertId]);

  const fetchAlertDetail = async () => {
    setLoading(true);
    try {
      const data = await cradleApi.getAlertDetail(alertId);
      setAlertDetail(data);
    } catch (error) {
      console.error('알림 상세 조회 실패:', error);
    } finally {
      setLoading(false);
    }
  };

  const getChartData = (dataKey: 'temperature' | 'direction') => {
    if (!alertDetail || alertDetail.sensor_data.length === 0) {
      return {
        labels: ['데이터 없음'],
        datasets: [{ data: [0] }],
      };
    }

    const sensorData = alertDetail.sensor_data;
    const step = Math.ceil(sensorData.length / 10);
    const sampledData = sensorData.filter((_, index) => index % step === 0).slice(-10);

    const labels = sampledData.map((item) => {
      const date = new Date(item.timestamp);
      return `${date.getHours()}:${date.getMinutes().toString().padStart(2, '0')}`;
    });

    let values: number[] = [];
    if (dataKey === 'temperature') {
      values = sampledData.map((item) => {
        const temp = item.temperature;
        return temp !== null ? temp : 0;
      });
    } else {
      values = sampledData.map((item) => {
        if (item.direction === '왼쪽' || item.direction?.includes('좌측')) return -1;
        if (item.direction === '오른쪽' || item.direction?.includes('우측')) return 1;
        return 0;
      });
    }

    return {
      labels,
      datasets: [{ data: values }],
    };
  };

  const formatDateTime = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString('ko-KR', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const handlePreviousFrame = () => {
    if (currentFrameIndex > 0) {
      setCurrentFrameIndex(currentFrameIndex - 1);
    }
  };

  const handleNextFrame = () => {
    if (alertDetail && currentFrameIndex < alertDetail.video_frames.length - 1) {
      setCurrentFrameIndex(currentFrameIndex + 1);
    }
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#4A90E2" />
        <Text style={styles.loadingText}>데이터 로딩 중...</Text>
      </View>
    );
  }

  if (!alertDetail) {
    return (
      <View style={styles.container}>
        <Text style={styles.errorText}>알림 정보를 불러올 수 없습니다.</Text>
      </View>
    );
  }

  const currentFrame = alertDetail.video_frames[currentFrameIndex];

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backButton}>
          <Text style={styles.backText}>← 뒤로</Text>
        </TouchableOpacity>
        <Text style={styles.headerTitle}>알림 상세 정보</Text>
      </View>

      {/* 알림 정보 */}
      <View style={styles.alertInfoCard}>
        <Text style={styles.sectionTitle}>📋 알림 정보</Text>
        <Text style={styles.alertMessage}>{alertDetail.alert.alert_message}</Text>
        <View style={styles.infoRow}>
          <Text style={styles.infoLabel}>발생 시간:</Text>
          <Text style={styles.infoValue}>{formatDateTime(alertDetail.alert.created_at)}</Text>
        </View>
        {alertDetail.alert.temperature && (
          <View style={styles.infoRow}>
            <Text style={styles.infoLabel}>체온:</Text>
            <Text style={[styles.infoValue, styles.tempValue]}>
              {alertDetail.alert.temperature.toFixed(1)}°C
            </Text>
          </View>
        )}
        <View style={styles.infoRow}>
          <Text style={styles.infoLabel}>상태:</Text>
          <Text style={[styles.infoValue, alertDetail.alert.resolved && styles.resolvedText]}>
            {alertDetail.alert.resolved ? '해결됨' : '미해결'}
          </Text>
        </View>
      </View>

      {/* 비디오 프레임 */}
      {alertDetail.video_frames.length > 0 && currentFrame && (
        <View style={styles.videoCard}>
          <Text style={styles.sectionTitle}>🎥 알림 시점 영상</Text>
          <View style={styles.videoContainer}>
            <Image
              source={{ uri: cradleApi.getAlertFrameUrl(currentFrame.id) }}
              style={styles.videoImage}
              resizeMode="contain"
            />
          </View>
          <View style={styles.videoControls}>
            <TouchableOpacity
              onPress={handlePreviousFrame}
              disabled={currentFrameIndex === 0}
              style={[styles.controlButton, currentFrameIndex === 0 && styles.controlButtonDisabled]}
            >
              <Text style={styles.controlButtonText}>◀ 이전</Text>
            </TouchableOpacity>
            <Text style={styles.frameCounter}>
              {currentFrameIndex + 1} / {alertDetail.video_frames.length}
            </Text>
            <TouchableOpacity
              onPress={handleNextFrame}
              disabled={currentFrameIndex === alertDetail.video_frames.length - 1}
              style={[
                styles.controlButton,
                currentFrameIndex === alertDetail.video_frames.length - 1 &&
                  styles.controlButtonDisabled,
              ]}
            >
              <Text style={styles.controlButtonText}>다음 ▶</Text>
            </TouchableOpacity>
          </View>
          <Text style={styles.frameTime}>
            프레임 시간: {formatDateTime(currentFrame.timestamp)}
          </Text>
        </View>
      )}

      {/* 센서 데이터 차트 */}
      {alertDetail.sensor_data.length > 0 && (
        <>
          {/* 체온 차트 */}
          <View style={styles.chartCard}>
            <Text style={styles.sectionTitle}>🌡️ 체온 변화</Text>
            <LineChart
              data={getChartData('temperature')}
              width={width - 40}
              height={220}
              chartConfig={{
                backgroundColor: '#fff',
                backgroundGradientFrom: '#fff',
                backgroundGradientTo: '#fff',
                decimalPlaces: 1,
                color: (opacity = 1) => `rgba(255, 99, 71, ${opacity})`,
                labelColor: (opacity = 1) => `rgba(0, 0, 0, ${opacity})`,
                style: {
                  borderRadius: 16,
                },
                propsForDots: {
                  r: '4',
                  strokeWidth: '2',
                  stroke: '#ff6347',
                },
              }}
              bezier
              style={styles.chart}
            />
          </View>

          {/* 방향 차트 */}
          <View style={styles.chartCard}>
            <Text style={styles.sectionTitle}>↔️ 아기 방향 변화</Text>
            <LineChart
              data={getChartData('direction')}
              width={width - 40}
              height={220}
              chartConfig={{
                backgroundColor: '#fff',
                backgroundGradientFrom: '#fff',
                backgroundGradientTo: '#fff',
                decimalPlaces: 0,
                color: (opacity = 1) => `rgba(74, 144, 226, ${opacity})`,
                labelColor: (opacity = 1) => `rgba(0, 0, 0, ${opacity})`,
                style: {
                  borderRadius: 16,
                },
                propsForDots: {
                  r: '4',
                  strokeWidth: '2',
                  stroke: '#4A90E2',
                },
              }}
              bezier
              style={styles.chart}
              yAxisSuffix=""
              yAxisInterval={1}
              formatYLabel={(value) => {
                const num = parseFloat(value);
                if (num < -0.5) return '왼쪽';
                if (num > 0.5) return '오른쪽';
                return '정면';
              }}
            />
          </View>
        </>
      )}

      {/* 통계 정보 */}
      <View style={styles.statsCard}>
        <Text style={styles.sectionTitle}>📊 통계</Text>
        <View style={styles.infoRow}>
          <Text style={styles.infoLabel}>녹화된 데이터:</Text>
          <Text style={styles.infoValue}>{alertDetail.sensor_data.length}개</Text>
        </View>
        <View style={styles.infoRow}>
          <Text style={styles.infoLabel}>녹화된 프레임:</Text>
          <Text style={styles.infoValue}>{alertDetail.total_frames}개</Text>
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
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    marginTop: 10,
    fontSize: 16,
    color: '#666',
  },
  errorText: {
    textAlign: 'center',
    marginTop: 100,
    fontSize: 18,
    color: '#999',
  },
  header: {
    backgroundColor: '#4A90E2',
    padding: 20,
    paddingTop: 60,
  },
  backButton: {
    marginBottom: 10,
  },
  backText: {
    color: '#fff',
    fontSize: 16,
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#fff',
  },
  alertInfoCard: {
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
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 15,
  },
  alertMessage: {
    fontSize: 16,
    color: '#666',
    marginBottom: 15,
    lineHeight: 24,
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
  tempValue: {
    color: '#FF6B6B',
  },
  resolvedText: {
    color: '#51CF66',
  },
  videoCard: {
    backgroundColor: '#fff',
    margin: 15,
    marginTop: 0,
    borderRadius: 15,
    padding: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  videoContainer: {
    backgroundColor: '#000',
    borderRadius: 10,
    overflow: 'hidden',
    aspectRatio: 4 / 3,
    marginBottom: 15,
  },
  videoImage: {
    width: '100%',
    height: '100%',
  },
  videoControls: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  controlButton: {
    backgroundColor: '#4A90E2',
    paddingVertical: 8,
    paddingHorizontal: 15,
    borderRadius: 8,
  },
  controlButtonDisabled: {
    backgroundColor: '#ccc',
  },
  controlButtonText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
  },
  frameCounter: {
    fontSize: 14,
    color: '#666',
  },
  frameTime: {
    fontSize: 12,
    color: '#999',
    textAlign: 'center',
  },
  chartCard: {
    backgroundColor: '#fff',
    margin: 15,
    marginTop: 0,
    borderRadius: 15,
    padding: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  chart: {
    marginVertical: 8,
    borderRadius: 16,
  },
  statsCard: {
    backgroundColor: '#fff',
    margin: 15,
    marginTop: 0,
    marginBottom: 30,
    borderRadius: 15,
    padding: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
});

export default AlertDetailScreen;
