import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  RefreshControl,
  Dimensions,
} from 'react-native';
import { useSelector } from 'react-redux';
import { RootState } from '../store';
import { cradleApi } from '../services/api';
import { useNavigation } from '@react-navigation/native';
import { LineChart, PieChart } from 'react-native-chart-kit';

const { width } = Dimensions.get('window');

interface AlertHistoryItem {
  id: number;
  alert_type: string;
  alert_message: string;
  temperature: number | null;
  face_detected: boolean | null;
  resolved: boolean;
  created_at: string;
  resolved_at: string | null;
}

interface SensorData {
  timestamp: string;
  temperature: number | null;
  crying: string | null;
  direction: string | null;
}

const HistoryScreen: React.FC = () => {
  const navigation = useNavigation<any>();
  const { selectedAgent } = useSelector((state: RootState) => state.agent);
  const [alerts, setAlerts] = useState<AlertHistoryItem[]>([]);
  const [sensorData, setSensorData] = useState<SensorData[]>([]);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  const fetchAlerts = async () => {
    if (!selectedAgent) return;

    setLoading(true);
    try {
      const data = await cradleApi.getAlertHistory(selectedAgent.uuid);
      setAlerts(data);
    } catch (error) {
      console.error('알림 히스토리 조회 실패:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchSensorData = async () => {
    if (!selectedAgent) return;

    try {
      // 최근 24시간 데이터 조회
      const end = new Date();
      const start = new Date(end.getTime() - 24 * 60 * 60 * 1000);
      const data = await cradleApi.getSensorData(
        selectedAgent.uuid,
        start.toISOString(),
        end.toISOString()
      );
      setSensorData(data);
    } catch (error) {
      console.error('센서 데이터 조회 실패:', error);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await Promise.all([fetchAlerts(), fetchSensorData()]);
    setRefreshing(false);
  };

  useEffect(() => {
    fetchAlerts();
    fetchSensorData();
  }, [selectedAgent]);

  const getAlertIcon = (alertType: string) => {
    switch (alertType) {
      case 'high_temperature':
        return '🌡️';
      case 'abnormal_position':
        return '↔️';
      case 'face_not_detected':
        return '😴';
      default:
        return '⚠️';
    }
  };

  const getAlertTypeLabel = (alertType: string) => {
    switch (alertType) {
      case 'high_temperature':
        return '체온 경고';
      case 'abnormal_position':
        return '자세 경고';
      case 'face_not_detected':
        return '얼굴 인식 경고';
      default:
        return '알림';
    }
  };

  const formatDateTime = (dateString: string) => {
    const date = new Date(dateString);
    const month = date.getMonth() + 1;
    const day = date.getDate();
    const hours = date.getHours();
    const minutes = date.getMinutes();
    return `${month}/${day} ${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}`;
  };

  // 온도 시계열 그래프 데이터
  const getTemperatureChartData = () => {
    if (sensorData.length === 0) {
      return {
        labels: ['데이터 없음'],
        datasets: [{ data: [0] }],
      };
    }

    const step = Math.ceil(sensorData.length / 12);
    const sampledData = sensorData.filter((_, index) => index % step === 0).slice(-12);

    const labels = sampledData.map((item) => {
      const date = new Date(item.timestamp);
      return `${date.getHours()}:${date.getMinutes().toString().padStart(2, '0')}`;
    });

    const values = sampledData.map((item) => {
      const temp = item.temperature;
      return temp !== null ? temp : 0;
    });

    return {
      labels,
      datasets: [{ data: values.length > 0 ? values : [0] }],
    };
  };

  // 얼굴 방향 비율 그래프 데이터
  const getDirectionPieData = () => {
    if (sensorData.length === 0) {
      return [];
    }

    const directionCount: { [key: string]: number } = {};
    sensorData.forEach((item) => {
      const dir = item.direction || '알 수 없음';
      directionCount[dir] = (directionCount[dir] || 0) + 1;
    });

    const colors = ['#4A90E2', '#FF6B6B', '#51CF66', '#FFA94D'];
    return Object.entries(directionCount).map(([name, count], index) => ({
      name,
      population: count,
      color: colors[index % colors.length],
      legendFontColor: '#666',
      legendFontSize: 12,
    }));
  };

  // 알림 타임라인 데이터
  const getAlertTimelineData = () => {
    if (alerts.length === 0) {
      return {
        labels: ['알림 없음'],
        datasets: [{ data: [0] }],
      };
    }

    // 24시간을 6개 구간으로 나누기 (4시간씩)
    const now = new Date();
    const intervals = 6;
    const intervalHours = 4;
    const counts = new Array(intervals).fill(0);
    const labels: string[] = [];

    for (let i = intervals - 1; i >= 0; i--) {
      const intervalStart = new Date(now.getTime() - (i + 1) * intervalHours * 60 * 60 * 1000);
      const intervalEnd = new Date(now.getTime() - i * intervalHours * 60 * 60 * 1000);
      
      labels.push(`${intervalStart.getHours()}시`);

      alerts.forEach((alert) => {
        const alertDate = new Date(alert.created_at);
        if (alertDate >= intervalStart && alertDate < intervalEnd) {
          counts[intervals - 1 - i]++;
        }
      });
    }

    return {
      labels,
      datasets: [{ data: counts.some(c => c > 0) ? counts : [0] }],
    };
  };

  const getCryingTimelineData = () => {
    const now = new Date();
    const hours = 24;
    const counts = new Array(hours).fill(0);
    const labels: string[] = [];

    // Create 24 hourly buckets
    for (let i = hours - 1; i >= 0; i--) {
      const hour = new Date(now.getTime() - i * 60 * 60 * 1000);
      if (i % 4 === 0) {  // Only show labels every 4 hours
        labels.push(`${hour.getHours()}시`);
      } else {
        labels.push('');
      }
    }

    // Count crying occurrences per hour
    sensorData.forEach((data) => {
      if (data.crying === 'Crying') {
        const dataTime = new Date(data.timestamp);
        const hoursDiff = Math.floor((now.getTime() - dataTime.getTime()) / (1000 * 60 * 60));
        
        if (hoursDiff >= 0 && hoursDiff < hours) {
          counts[hours - 1 - hoursDiff]++;
        }
      }
    });

    return {
      labels,
      datasets: [{ data: counts.some(c => c > 0) ? counts : [0] }],
    };
  };

  const renderAlertItem = ({ item }: { item: AlertHistoryItem }) => (
    <TouchableOpacity
      style={[styles.alertCard, item.resolved && styles.alertCardResolved]}
      onPress={() => navigation.navigate('AlertDetail', { alertId: item.id })}
    >
      <View style={styles.alertHeader}>
        <View style={styles.alertIconContainer}>
          <Text style={styles.alertIcon}>{getAlertIcon(item.alert_type)}</Text>
        </View>
        <View style={styles.alertInfo}>
          <Text style={styles.alertType}>{getAlertTypeLabel(item.alert_type)}</Text>
          <Text style={styles.alertTime}>{formatDateTime(item.created_at)}</Text>
        </View>
        {item.resolved && (
          <View style={styles.resolvedBadge}>
            <Text style={styles.resolvedText}>해결됨</Text>
          </View>
        )}
      </View>
      <Text style={styles.alertMessage} numberOfLines={2}>
        {item.alert_message}
      </Text>
      {item.temperature && (
        <Text style={styles.alertTemp}>체온: {item.temperature.toFixed(1)}°C</Text>
      )}
    </TouchableOpacity>
  );

  if (!selectedAgent) {
    return (
      <View style={styles.container}>
        <Text style={styles.noAgentText}>선택된 요람이 없습니다.</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>히스토리 & 통계</Text>
        <Text style={styles.headerSubtitle}>최근 24시간 / 30일</Text>
      </View>

      {loading && !refreshing ? (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#4A90E2" />
          <Text style={styles.loadingText}>데이터 로딩 중...</Text>
        </View>
      ) : (
        <ScrollView
          style={styles.scrollView}
          refreshControl={
            <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
          }
        >
          {/* 온도 시계열 그래프 */}
          <View style={styles.chartCard}>
            <Text style={styles.chartTitle}>🌡️ 체온 변화 (24시간)</Text>
            <LineChart
              data={getTemperatureChartData()}
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
            <Text style={styles.chartSubtext}>시간대별 체온 추이</Text>
          </View>

          {/* 얼굴 방향 비율 그래프 */}
          {getDirectionPieData().length > 0 && (
            <View style={styles.chartCard}>
              <Text style={styles.chartTitle}>↔️ 아기 방향 분포 (24시간)</Text>
              <PieChart
                data={getDirectionPieData()}
                width={width - 40}
                height={220}
                chartConfig={{
                  color: (opacity = 1) => `rgba(0, 0, 0, ${opacity})`,
                }}
                accessor="population"
                backgroundColor="transparent"
                paddingLeft="15"
                absolute
              />
              <Text style={styles.chartSubtext}>방향별 시간 비율</Text>
            </View>
          )}

          {/* 울음 감지 타임라인 */}
          <View style={styles.chartCard}>
            <Text style={styles.chartTitle}>😢 울음 감지 타임라인 (24시간)</Text>
            <LineChart
              data={getCryingTimelineData()}
              width={width - 40}
              height={220}
              chartConfig={{
                backgroundColor: '#fff',
                backgroundGradientFrom: '#fff',
                backgroundGradientTo: '#fff',
                decimalPlaces: 0,
                color: (opacity = 1) => `rgba(156, 39, 176, ${opacity})`,
                labelColor: (opacity = 1) => `rgba(0, 0, 0, ${opacity})`,
                style: {
                  borderRadius: 16,
                },
                propsForDots: {
                  r: '4',
                  strokeWidth: '2',
                  stroke: '#9C27B0',
                },
              }}
              bezier
              style={styles.chart}
            />
            <Text style={styles.chartSubtext}>시간대별 울음 발생 패턴</Text>
          </View>

          {/* 알림 타임라인 그래프 */}
          <View style={styles.chartCard}>
            <Text style={styles.chartTitle}>⚠️ 알림 발생 타임라인 (24시간)</Text>
            <LineChart
              data={getAlertTimelineData()}
              width={width - 40}
              height={220}
              chartConfig={{
                backgroundColor: '#fff',
                backgroundGradientFrom: '#fff',
                backgroundGradientTo: '#fff',
                decimalPlaces: 0,
                color: (opacity = 1) => `rgba(255, 159, 64, ${opacity})`,
                labelColor: (opacity = 1) => `rgba(0, 0, 0, ${opacity})`,
                style: {
                  borderRadius: 16,
                },
                propsForDots: {
                  r: '4',
                  strokeWidth: '2',
                  stroke: '#FF9F40',
                },
              }}
              bezier
              style={styles.chart}
            />
            <Text style={styles.chartSubtext}>4시간 단위 알림 발생 건수</Text>
          </View>

          {/* 알림 리스트 섹션 */}
          <View style={styles.alertListSection}>
            <Text style={styles.sectionTitle}>📋 알림 목록</Text>
            {alerts.length === 0 ? (
              <View style={styles.emptyAlertContainer}>
                <Text style={styles.emptyIcon}>📭</Text>
                <Text style={styles.emptyText}>알림 기록이 없습니다.</Text>
                <Text style={styles.emptySubtext}>
                  체온이나 자세 이상 시 알림이 표시됩니다.
                </Text>
              </View>
            ) : (
              alerts.map((item) => (
                <TouchableOpacity
                  key={item.id}
                  style={[styles.alertCard, item.resolved && styles.alertCardResolved]}
                  onPress={() => navigation.navigate('AlertDetail', { alertId: item.id })}
                >
                  <View style={styles.alertHeader}>
                    <View style={styles.alertIconContainer}>
                      <Text style={styles.alertIcon}>{getAlertIcon(item.alert_type)}</Text>
                    </View>
                    <View style={styles.alertInfo}>
                      <Text style={styles.alertType}>{getAlertTypeLabel(item.alert_type)}</Text>
                      <Text style={styles.alertTime}>{formatDateTime(item.created_at)}</Text>
                    </View>
                    {item.resolved && (
                      <View style={styles.resolvedBadge}>
                        <Text style={styles.resolvedText}>해결됨</Text>
                      </View>
                    )}
                  </View>
                  <Text style={styles.alertMessage} numberOfLines={2}>
                    {item.alert_message}
                  </Text>
                  {item.temperature && (
                    <Text style={styles.alertTemp}>체온: {item.temperature.toFixed(1)}°C</Text>
                  )}
                </TouchableOpacity>
              ))
            )}
          </View>
        </ScrollView>
      )}
    </View>
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
  headerSubtitle: {
    fontSize: 14,
    color: '#fff',
    marginTop: 5,
    opacity: 0.9,
  },
  noAgentText: {
    textAlign: 'center',
    marginTop: 100,
    fontSize: 18,
    color: '#999',
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
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 40,
  },
  emptyIcon: {
    fontSize: 64,
    marginBottom: 20,
  },
  emptyText: {
    fontSize: 18,
    fontWeight: '600',
    color: '#333',
    marginBottom: 10,
  },
  emptySubtext: {
    fontSize: 14,
    color: '#999',
    textAlign: 'center',
  },
  listContainer: {
    padding: 15,
  },
  alertCard: {
    backgroundColor: '#fff',
    borderRadius: 15,
    padding: 15,
    marginBottom: 15,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
    borderLeftWidth: 4,
    borderLeftColor: '#FF6B6B',
  },
  alertCardResolved: {
    opacity: 0.7,
    borderLeftColor: '#51CF66',
  },
  alertHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 10,
  },
  alertIconContainer: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#FFF5F5',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  alertIcon: {
    fontSize: 20,
  },
  alertInfo: {
    flex: 1,
  },
  alertType: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    marginBottom: 3,
  },
  alertTime: {
    fontSize: 13,
    color: '#999',
  },
  resolvedBadge: {
    backgroundColor: '#51CF66',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
  },
  resolvedText: {
    fontSize: 11,
    color: '#fff',
    fontWeight: '600',
  },
  alertMessage: {
    fontSize: 14,
    color: '#666',
    marginBottom: 8,
    lineHeight: 20,
  },
  alertTemp: {
    fontSize: 13,
    color: '#FF6B6B',
    fontWeight: '500',
  },
  scrollView: {
    flex: 1,
  },
  chartCard: {
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
  chartTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 15,
  },
  chart: {
    marginVertical: 8,
    borderRadius: 16,
  },
  chartSubtext: {
    fontSize: 12,
    color: '#666',
    textAlign: 'center',
    marginTop: 10,
  },
  alertListSection: {
    margin: 15,
    marginTop: 0,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 15,
  },
  emptyAlertContainer: {
    backgroundColor: '#fff',
    borderRadius: 15,
    padding: 40,
    alignItems: 'center',
  },
});

export default HistoryScreen;
