import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  Switch,
  TextInput,
  TouchableOpacity,
  Alert,
  Modal,
  FlatList,
  ActivityIndicator,
} from 'react-native';
import { useSelector, useDispatch } from 'react-redux';
import { RootState } from '../store';
import { setSelectedAgent } from '../store/agentSlice';
import { cradleApi } from '../services/api';
import { AlertSettings as AlertSettingsType, Agent } from '../types';

const SettingsScreen: React.FC = () => {
  const dispatch = useDispatch();
  const { selectedAgent } = useSelector((state: RootState) => state.agent);
  const [settings, setSettings] = useState<AlertSettingsType>({
    max_temperature: 38.0,
    abnormal_position_timeout: 30,
    crying_duration_threshold: 30,
    push_notifications_enabled: true,
    email_notifications_enabled: false,
  });
  const [loading, setLoading] = useState(false);
  const [fetching, setFetching] = useState(true);
  
  // 요람 관리 상태
  const [agents, setAgents] = useState<Agent[]>([]);
  const [showAgentModal, setShowAgentModal] = useState(false);
  const [showAddModal, setShowAddModal] = useState(false);
  const [newCradleUuid, setNewCradleUuid] = useState('');
  const [agentsLoading, setAgentsLoading] = useState(false);

  // 현재 설정 로드
  useEffect(() => {
    const loadSettings = async () => {
      if (!selectedAgent) return;

      try {
        const currentSettings = await cradleApi.getAlertSettings(selectedAgent.uuid);
        setSettings(currentSettings);
      } catch (error) {
        console.error('설정 로드 실패:', error);
      } finally {
        setFetching(false);
      }
    };

    loadSettings();
  }, [selectedAgent]);

  // 요람 목록 로드
  const loadAgents = async () => {
    setAgentsLoading(true);
    try {
      const data = await cradleApi.getAgents();
      setAgents(data);
    } catch (error) {
      console.error('요람 목록 로드 실패:', error);
      Alert.alert('오류', '요람 목록을 불러올 수 없습니다.');
    } finally {
      setAgentsLoading(false);
    }
  };

  // 요람 선택
  const handleSelectAgent = async (agent: Agent) => {
    try {
      await cradleApi.selectCradle(agent.uuid);
      dispatch(setSelectedAgent(agent));
      setShowAgentModal(false);
      Alert.alert('성공', `${agent.uuid.substring(0, 8)}... 요람이 선택되었습니다.`);
    } catch (error: any) {
      console.error('요람 선택 실패:', error);
      Alert.alert('오류', error.response?.data?.message || '요람 선택에 실패했습니다.');
    }
  };

  // 요람 추가
  const handleAddCradle = async () => {
    if (!newCradleUuid.trim()) {
      Alert.alert('오류', '요람 UUID를 입력해주세요.');
      return;
    }

    setLoading(true);
    try {
      await cradleApi.registerCradle(newCradleUuid.trim());
      Alert.alert('성공', '요람이 등록되었습니다.');
      setNewCradleUuid('');
      setShowAddModal(false);
      loadAgents(); // 목록 새로고침
    } catch (error: any) {
      console.error('요람 등록 실패:', error);
      Alert.alert('오류', error.response?.data?.message || '요람 등록에 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  // 요람 삭제
  const handleDeleteCradle = async (agent: Agent) => {
    Alert.alert(
      '요람 삭제',
      `${agent.uuid.substring(0, 8)}... 요람을 삭제하시겠습니까?\n모든 데이터가 삭제됩니다.`,
      [
        { text: '취소', style: 'cancel' },
        {
          text: '삭제',
          style: 'destructive',
          onPress: async () => {
            try {
              await cradleApi.deleteCradle(agent.uuid);
              Alert.alert('성공', '요람이 삭제되었습니다.');
              
              // 삭제된 요람이 선택된 요람이면 초기화
              if (selectedAgent?.uuid === agent.uuid) {
                const remaining = agents.filter(a => a.uuid !== agent.uuid);
                if (remaining.length > 0) {
                  dispatch(setSelectedAgent(remaining[0]));
                }
              }
              
              loadAgents(); // 목록 새로고침
            } catch (error: any) {
              console.error('요람 삭제 실패:', error);
              Alert.alert('오류', error.response?.data?.message || '요람 삭제에 실패했습니다.');
            }
          },
        },
      ]
    );
  };

  const handleSave = async () => {
    if (!selectedAgent) {
      Alert.alert('오류', '요람을 선택해주세요.');
      return;
    }

    setLoading(true);
    try {
      await cradleApi.updateAlertSettings(selectedAgent.uuid, settings);
      Alert.alert('성공', '설정이 저장되었습니다.');
    } catch (error) {
      console.error('설정 저장 실패:', error);
      Alert.alert('오류', '설정 저장에 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  if (!selectedAgent) {
    return (
      <View style={styles.container}>
        <Text style={styles.noAgentText}>요람을 선택해주세요</Text>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>설정</Text>
      </View>

      {/* 요람 관리 섹션 */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>🍼 요람 관리</Text>
        
        {selectedAgent && (
          <View style={styles.currentCradle}>
            <Text style={styles.currentCradleLabel}>현재 선택된 요람:</Text>
            <Text style={styles.currentCradleUuid}>
              {selectedAgent.uuid.substring(0, 16)}...
            </Text>
          </View>
        )}

        <View style={styles.buttonRow}>
          <TouchableOpacity
            style={[styles.actionButton, styles.selectButton]}
            onPress={() => {
              loadAgents();
              setShowAgentModal(true);
            }}
          >
            <Text style={styles.actionButtonText}>요람 선택</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.actionButton, styles.addButton]}
            onPress={() => setShowAddModal(true)}
          >
            <Text style={styles.actionButtonText}>요람 추가</Text>
          </TouchableOpacity>
        </View>
      </View>

      {!selectedAgent ? (
        <View style={styles.noAgentContainer}>
          <Text style={styles.noAgentText}>요람을 선택하거나 추가해주세요</Text>
        </View>
      ) : (
        <>
          <View style={styles.section}>
        <Text style={styles.sectionTitle}>🌡️ 온도 설정</Text>
        <View style={styles.settingRow}>
          <Text style={styles.settingLabel}>최대 체온 (°C)</Text>
          <TextInput
            style={styles.input}
            value={settings.max_temperature.toString()}
            onChangeText={(text) => {
              const value = parseFloat(text);
              if (!isNaN(value)) {
                setSettings({ ...settings, max_temperature: value });
              }
            }}
            keyboardType="decimal-pad"
            editable={!loading}
          />
        </View>
        <Text style={styles.helpText}>
          설정한 체온을 초과하면 알림이 발생합니다.
        </Text>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>👶 자세 감지 설정</Text>
        <View style={styles.settingRow}>
          <Text style={styles.settingLabel}>허용 시간 (초)</Text>
          <TextInput
            style={styles.input}
            value={settings.abnormal_position_timeout.toString()}
            onChangeText={(text) => {
              const value = parseInt(text);
              if (!isNaN(value)) {
                setSettings({ ...settings, abnormal_position_timeout: value });
              }
            }}
            keyboardType="number-pad"
            editable={!loading}
          />
        </View>
        <Text style={styles.helpText}>
          비정상 자세가 설정한 시간 이상 지속되면 알림이 발생합니다.
        </Text>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>😢 울음 감지 설정</Text>
        <View style={styles.settingRow}>
          <Text style={styles.settingLabel}>알림 임계값 (초)</Text>
          <TextInput
            style={styles.input}
            value={settings.crying_duration_threshold.toString()}
            onChangeText={(text) => {
              const value = parseInt(text);
              if (!isNaN(value)) {
                setSettings({ ...settings, crying_duration_threshold: value });
              }
            }}
            keyboardType="number-pad"
            editable={!loading}
          />
        </View>
        <Text style={styles.helpText}>
          울음이 설정한 시간 이상 지속되면 알림이 발생합니다.
        </Text>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>🔔 알림 설정</Text>
        
        <View style={styles.switchRow}>
          <Text style={styles.settingLabel}>푸시 알림</Text>
          <Switch
            value={settings.push_notifications_enabled}
            onValueChange={(value) =>
              setSettings({ ...settings, push_notifications_enabled: value })
            }
            disabled={loading}
          />
        </View>

        <View style={styles.switchRow}>
          <Text style={styles.settingLabel}>이메일 알림</Text>
          <Switch
            value={settings.email_notifications_enabled}
            onValueChange={(value) =>
              setSettings({ ...settings, email_notifications_enabled: value })
            }
            disabled={loading}
          />
        </View>
      </View>

      <TouchableOpacity
        style={[styles.saveButton, loading && styles.saveButtonDisabled]}
        onPress={handleSave}
        disabled={loading}
      >
        <Text style={styles.saveButtonText}>
          {loading ? '저장 중...' : '설정 저장'}
        </Text>
      </TouchableOpacity>

          <View style={styles.infoSection}>
            <Text style={styles.infoTitle}>💡 알림 정보</Text>
            <Text style={styles.infoText}>
              • 고온 알림: 체온이 설정 값을 초과하면 발생{'\n'}
              • 얼굴 인식 실패: 얼굴이 인식되지 않으면 발생{'\n'}
              • 비정상 자세: 정면이 아닌 상태가 지속되면 발생{'\n'}
              • 울음 알림: 울음이 설정 시간 이상 지속되면 발생{'\n'}
              • 중복 알림 방지: 일정 시간 동안 같은 알림 차단
            </Text>
          </View>
        </>
      )}

      {/* 요람 선택 모달 */}
      <Modal
        visible={showAgentModal}
        transparent
        animationType="slide"
        onRequestClose={() => setShowAgentModal(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>요람 선택</Text>
              <TouchableOpacity onPress={() => setShowAgentModal(false)}>
                <Text style={styles.modalClose}>✕</Text>
              </TouchableOpacity>
            </View>

            {agentsLoading ? (
              <ActivityIndicator size="large" color="#4A90E2" style={styles.loader} />
            ) : (
              <FlatList
                data={agents}
                keyExtractor={(item) => item.uuid}
                renderItem={({ item }) => (
                  <View style={styles.agentItem}>
                    <TouchableOpacity
                      style={styles.agentItemContent}
                      onPress={() => handleSelectAgent(item)}
                    >
                      <Text style={styles.agentUuid}>
                        {item.uuid.substring(0, 16)}...
                      </Text>
                      <Text style={styles.agentIp}>{item.ip || '연결 대기'}</Text>
                      {selectedAgent?.uuid === item.uuid && (
                        <Text style={styles.selectedBadge}>✓ 선택됨</Text>
                      )}
                    </TouchableOpacity>
                    <TouchableOpacity
                      style={styles.deleteButton}
                      onPress={() => handleDeleteCradle(item)}
                    >
                      <Text style={styles.deleteButtonText}>🗑️</Text>
                    </TouchableOpacity>
                  </View>
                )}
                ListEmptyComponent={
                  <Text style={styles.emptyText}>등록된 요람이 없습니다</Text>
                }
              />
            )}
          </View>
        </View>
      </Modal>

      {/* 요람 추가 모달 */}
      <Modal
        visible={showAddModal}
        transparent
        animationType="fade"
        onRequestClose={() => setShowAddModal(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.addModalContent}>
            <Text style={styles.modalTitle}>요람 추가</Text>
            
            <TextInput
              style={styles.uuidInput}
              placeholder="요람 UUID 입력"
              value={newCradleUuid}
              onChangeText={setNewCradleUuid}
              autoCapitalize="none"
              autoCorrect={false}
            />

            <View style={styles.modalButtons}>
              <TouchableOpacity
                style={[styles.modalButton, styles.cancelButton]}
                onPress={() => {
                  setShowAddModal(false);
                  setNewCradleUuid('');
                }}
              >
                <Text style={styles.cancelButtonText}>취소</Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={[styles.modalButton, styles.confirmButton]}
                onPress={handleAddCradle}
                disabled={loading}
              >
                <Text style={styles.confirmButtonText}>
                  {loading ? '등록 중...' : '등록'}
                </Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>
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
  noAgentText: {
    textAlign: 'center',
    marginTop: 100,
    fontSize: 18,
    color: '#999',
  },
  section: {
    backgroundColor: '#fff',
    margin: 15,
    borderRadius: 15,
    padding: 20,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 15,
  },
  settingRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  settingLabel: {
    fontSize: 16,
    color: '#333',
  },
  input: {
    width: 100,
    height: 40,
    backgroundColor: '#f5f5f5',
    borderRadius: 8,
    paddingHorizontal: 15,
    fontSize: 16,
    textAlign: 'center',
    borderWidth: 1,
    borderColor: '#ddd',
  },
  helpText: {
    fontSize: 12,
    color: '#666',
    marginTop: 5,
    fontStyle: 'italic',
  },
  switchRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 10,
  },
  saveButton: {
    backgroundColor: '#4A90E2',
    margin: 15,
    padding: 15,
    borderRadius: 10,
    alignItems: 'center',
  },
  saveButtonDisabled: {
    opacity: 0.6,
  },
  saveButtonText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: 'bold',
  },
  infoSection: {
    backgroundColor: '#fff',
    margin: 15,
    marginTop: 0,
    borderRadius: 15,
    padding: 20,
    marginBottom: 30,
  },
  infoTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 10,
  },
  infoText: {
    fontSize: 14,
    color: '#666',
    lineHeight: 22,
  },
  // 요람 관리 스타일
  currentCradle: {
    backgroundColor: '#f0f8ff',
    padding: 12,
    borderRadius: 8,
    marginBottom: 15,
  },
  currentCradleLabel: {
    fontSize: 14,
    color: '#666',
    marginBottom: 5,
  },
  currentCradleUuid: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#4A90E2',
    fontFamily: 'monospace',
  },
  buttonRow: {
    flexDirection: 'row',
    gap: 10,
  },
  actionButton: {
    flex: 1,
    padding: 15,
    borderRadius: 10,
    alignItems: 'center',
  },
  selectButton: {
    backgroundColor: '#4A90E2',
  },
  addButton: {
    backgroundColor: '#27AE60',
  },
  actionButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
  noAgentContainer: {
    padding: 40,
    alignItems: 'center',
  },
  // 모달 스타일
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  modalContent: {
    backgroundColor: '#fff',
    width: '85%',
    maxHeight: '70%',
    borderRadius: 15,
    padding: 20,
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 20,
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
  },
  modalClose: {
    fontSize: 28,
    color: '#999',
  },
  loader: {
    marginVertical: 40,
  },
  agentItem: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#f5f5f5',
    padding: 15,
    borderRadius: 10,
    marginBottom: 10,
  },
  agentItemContent: {
    flex: 1,
  },
  agentUuid: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
    fontFamily: 'monospace',
  },
  agentIp: {
    fontSize: 14,
    color: '#666',
    marginTop: 5,
  },
  selectedBadge: {
    fontSize: 14,
    color: '#27AE60',
    fontWeight: 'bold',
    marginTop: 5,
  },
  deleteButton: {
    padding: 10,
  },
  deleteButtonText: {
    fontSize: 20,
  },
  emptyText: {
    textAlign: 'center',
    color: '#999',
    fontSize: 16,
    marginVertical: 40,
  },
  addModalContent: {
    backgroundColor: '#fff',
    width: '85%',
    borderRadius: 15,
    padding: 25,
  },
  uuidInput: {
    backgroundColor: '#f5f5f5',
    padding: 15,
    borderRadius: 10,
    fontSize: 16,
    marginTop: 15,
    marginBottom: 20,
    fontFamily: 'monospace',
  },
  modalButtons: {
    flexDirection: 'row',
    gap: 10,
  },
  modalButton: {
    flex: 1,
    padding: 15,
    borderRadius: 10,
    alignItems: 'center',
  },
  cancelButton: {
    backgroundColor: '#f5f5f5',
  },
  confirmButton: {
    backgroundColor: '#4A90E2',
  },
  cancelButtonText: {
    color: '#666',
    fontSize: 16,
    fontWeight: 'bold',
  },
  confirmButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
});

export default SettingsScreen;
