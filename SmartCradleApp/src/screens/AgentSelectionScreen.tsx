import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  RefreshControl,
  Alert,
} from 'react-native';
import { useDispatch, useSelector } from 'react-redux';
import { RootState } from '../store';
import { setAgents, setSelectedAgent } from '../store/agentSlice';
import { cradleApi } from '../services/api';
import { Agent } from '../types';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';

type AgentSelectionScreenProps = {
  navigation: NativeStackNavigationProp<any>;
};

const AgentSelectionScreen: React.FC<AgentSelectionScreenProps> = ({ navigation }) => {
  const dispatch = useDispatch();
  const { agents, selectedAgent } = useSelector((state: RootState) => state.agent);
  const [refreshing, setRefreshing] = useState(false);
  const [loading, setLoading] = useState(true);

  const fetchAgents = async () => {
    try {
      const agentList = await cradleApi.getAgents();
      dispatch(setAgents(agentList));
      
      // 요람이 없으면 등록 화면으로 이동
      if (agentList.length === 0) {
        Alert.alert(
          '요람 없음',
          '등록된 요람이 없습니다. 요람을 등록하시겠습니까?',
          [
            {
              text: '취소',
              style: 'cancel',
            },
            {
              text: '등록',
              onPress: () => navigation.navigate('RegisterCradle'),
            },
          ]
        );
      }
    } catch (error) {
      console.error('요람 목록 조회 실패:', error);
      Alert.alert('오류', '요람 목록을 불러오는데 실패했습니다.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchAgents();
  }, []);

  const handleSelectAgent = (agent: Agent) => {
    dispatch(setSelectedAgent(agent));
    Alert.alert('성공', `${agent.uuid.substring(0, 8)}... 요람이 선택되었습니다.`);
    navigation.goBack();
  };

  const handleAddCradle = () => {
    navigation.navigate('RegisterCradle');
  };

  const onRefresh = () => {
    setRefreshing(true);
    fetchAgents();
  };

  const renderAgentItem = ({ item }: { item: Agent }) => {
    const isSelected = selectedAgent?.uuid === item.uuid;
    
    return (
      <TouchableOpacity
        style={[styles.agentCard, isSelected && styles.agentCardSelected]}
        onPress={() => handleSelectAgent(item)}
      >
        <View style={styles.agentHeader}>
          <View style={styles.agentIcon}>
            <Text style={styles.agentIconText}>🍼</Text>
          </View>
          <View style={styles.agentInfo}>
            <Text style={styles.agentUuid}>
              {item.uuid.length > 16 ? `${item.uuid.substring(0, 16)}...` : item.uuid}
            </Text>
            <Text style={styles.agentIp}>IP: {item.ip}</Text>
            <Text style={styles.agentDate}>
              등록일: {new Date(item.created_at).toLocaleDateString('ko-KR')}
            </Text>
          </View>
        </View>
        
        {isSelected && (
          <View style={styles.selectedBadge}>
            <Text style={styles.selectedText}>✓ 선택됨</Text>
          </View>
        )}
      </TouchableOpacity>
    );
  };

  if (loading) {
    return (
      <View style={styles.centerContainer}>
        <Text style={styles.loadingText}>로딩 중...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>내 요람 목록</Text>
        <Text style={styles.headerSubtitle}>{agents.length}개의 요람</Text>
      </View>

      <FlatList
        data={agents}
        renderItem={renderAgentItem}
        keyExtractor={(item) => item.uuid}
        contentContainerStyle={styles.listContainer}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
        ListEmptyComponent={
          <View style={styles.emptyContainer}>
            <Text style={styles.emptyIcon}>🍼</Text>
            <Text style={styles.emptyText}>등록된 요람이 없습니다</Text>
            <Text style={styles.emptySubtext}>
              아래 버튼을 눌러 요람을 등록하세요
            </Text>
          </View>
        }
      />

      <TouchableOpacity style={styles.addButton} onPress={handleAddCradle}>
        <Text style={styles.addButtonText}>+ 요람 추가</Text>
      </TouchableOpacity>
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
  loadingText: {
    fontSize: 16,
    color: '#999',
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
    flexGrow: 1,
  },
  agentCard: {
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
  agentCardSelected: {
    borderWidth: 2,
    borderColor: '#4A90E2',
  },
  agentHeader: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  agentIcon: {
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: '#E3F2FD',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 15,
  },
  agentIconText: {
    fontSize: 30,
  },
  agentInfo: {
    flex: 1,
  },
  agentUuid: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 5,
  },
  agentIp: {
    fontSize: 14,
    color: '#666',
    marginBottom: 3,
  },
  agentDate: {
    fontSize: 12,
    color: '#999',
  },
  selectedBadge: {
    marginTop: 10,
    paddingVertical: 5,
    paddingHorizontal: 10,
    backgroundColor: '#4A90E2',
    borderRadius: 5,
    alignSelf: 'flex-start',
  },
  selectedText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: '600',
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 100,
  },
  emptyIcon: {
    fontSize: 80,
    marginBottom: 20,
  },
  emptyText: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 10,
  },
  emptySubtext: {
    fontSize: 14,
    color: '#999',
    textAlign: 'center',
  },
  addButton: {
    margin: 15,
    height: 50,
    backgroundColor: '#4A90E2',
    borderRadius: 10,
    justifyContent: 'center',
    alignItems: 'center',
  },
  addButtonText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: 'bold',
  },
});

export default AgentSelectionScreen;
