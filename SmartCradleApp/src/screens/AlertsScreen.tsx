import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  FlatList,
} from 'react-native';
import { useSelector } from 'react-redux';
import { RootState } from '../store';
import { cradleApi } from '../services/api';
import { AlertLog } from '../types';

const AlertsScreen: React.FC = () => {
  const { selectedAgent } = useSelector((state: RootState) => state.agent);
  const [alerts, setAlerts] = useState<AlertLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchAlerts = async () => {
    // 요람이 선택되지 않았으면 API 호출하지 않음
    if (!selectedAgent) {
      setLoading(false);
      setRefreshing(false);
      return;
    }

    try {
      const data = await cradleApi.getAlertLogs();
      setAlerts(data);
    } catch (error) {
      console.error('알림 조회 실패:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchAlerts();
  }, [selectedAgent]);

  const handleResolve = async (alertId: number) => {
    try {
      await cradleApi.resolveAlert(alertId);
      fetchAlerts(); // 새로고침
    } catch (error) {
      console.error('알림 해결 실패:', error);
    }
  };

  const getAlertIcon = (alertType: string): string => {
    switch (alertType) {
      case 'high_temperature':
        return '🌡️';
      case 'face_not_detected':
        return '❌';
      case 'abnormal_position':
        return '⚠️';
      default:
        return '📢';
    }
  };

  const getAlertColor = (alertType: string): string => {
    switch (alertType) {
      case 'high_temperature':
        return '#E74C3C';
      case 'face_not_detected':
        return '#E74C3C';
      case 'abnormal_position':
        return '#F39C12';
      default:
        return '#3498DB';
    }
  };

  const renderAlertItem = ({ item }: { item: AlertLog }) => (
    <View
      style={[
        styles.alertCard,
        item.resolved && styles.alertCardResolved,
      ]}
    >
      <View style={styles.alertHeader}>
        <View style={styles.alertIconContainer}>
          <Text style={styles.alertIcon}>{getAlertIcon(item.alert_type)}</Text>
        </View>
        <View style={styles.alertInfo}>
          <Text
            style={[
              styles.alertMessage,
              { color: getAlertColor(item.alert_type) },
            ]}
          >
            {item.message}
          </Text>
          <Text style={styles.alertTime}>
            {new Date(item.created_at).toLocaleString('ko-KR')}
          </Text>
        </View>
      </View>

      {item.temperature && (
        <Text style={styles.alertDetail}>체온: {item.temperature.toFixed(1)}°C</Text>
      )}

      {!item.resolved && (
        <TouchableOpacity
          style={styles.resolveButton}
          onPress={() => handleResolve(item.id)}
        >
          <Text style={styles.resolveButtonText}>해결 완료</Text>
        </TouchableOpacity>
      )}

      {item.resolved && (
        <View style={styles.resolvedBadge}>
          <Text style={styles.resolvedText}>✓ 해결됨</Text>
        </View>
      )}
    </View>
  );

  if (!selectedAgent) {
    return (
      <View style={styles.centerContainer}>
        <Text style={styles.noAgentText}>선택된 요람이 없습니다.</Text>
        <Text style={styles.noAgentSubtext}>요람 선택 탭에서 요람을 선택해주세요.</Text>
      </View>
    );
  }

  if (loading) {
    return (
      <View style={styles.centerContainer}>
        <Text>로딩 중...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>알림 기록</Text>
        <Text style={styles.headerSubtitle}>최근 24시간</Text>
      </View>

      <FlatList
        data={alerts}
        renderItem={renderAlertItem}
        keyExtractor={(item) => item.id.toString()}
        contentContainerStyle={styles.listContainer}
        refreshing={refreshing}
        onRefresh={() => {
          setRefreshing(true);
          fetchAlerts();
        }}
        ListEmptyComponent={
          <View style={styles.emptyContainer}>
            <Text style={styles.emptyText}>알림이 없습니다</Text>
          </View>
        }
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  centerContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
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
    opacity: 0.8,
    marginTop: 5,
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
  },
  alertCardResolved: {
    opacity: 0.6,
  },
  alertHeader: {
    flexDirection: 'row',
    alignItems: 'flex-start',
  },
  alertIconContainer: {
    marginRight: 15,
  },
  alertIcon: {
    fontSize: 32,
  },
  alertInfo: {
    flex: 1,
  },
  alertMessage: {
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 5,
  },
  alertTime: {
    fontSize: 12,
    color: '#666',
  },
  alertDetail: {
    fontSize: 14,
    color: '#666',
    marginTop: 10,
    marginLeft: 47,
  },
  resolveButton: {
    backgroundColor: '#27AE60',
    borderRadius: 8,
    padding: 10,
    marginTop: 15,
    alignItems: 'center',
  },
  resolveButtonText: {
    color: '#fff',
    fontWeight: 'bold',
  },
  resolvedBadge: {
    marginTop: 10,
    alignSelf: 'flex-start',
    backgroundColor: '#E8F5E9',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 15,
  },
  resolvedText: {
    color: '#27AE60',
    fontSize: 12,
    fontWeight: 'bold',
  },
  emptyContainer: {
    alignItems: 'center',
    marginTop: 50,
  },
  emptyText: {
    fontSize: 16,
    color: '#999',
  },
  noAgentText: {
    fontSize: 18,
    color: '#999',
    textAlign: 'center',
  },
  noAgentSubtext: {
    fontSize: 14,
    color: '#bbb',
    textAlign: 'center',
    marginTop: 10,
  },
});

export default AlertsScreen;
