import axios from 'axios';
import { AgentStatus, SensorData, AlertLog, AlertSettings, LoginResponse } from '../types';

// 서버 URL - 도메인 사용 (IP 변경에 영향받지 않음)
const API_BASE_URL = 'http://www.smartcradle.kro.kr';

// Axios 인스턴스 생성
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  withCredentials: true, // 세션 쿠키를 위해 필요
  headers: {
    'Content-Type': 'application/json',
  },
});

// API 서비스
export const cradleApi = {
  // 인증
  login: async (username: string, password: string): Promise<LoginResponse> => {
    const response = await api.post(`${API_BASE_URL}/login`, 
      { username, password },
      {
        headers: {
          'Content-Type': 'application/json',
        },
      }
    );
    return response.data;
  },

  register: async (username: string, password: string): Promise<any> => {
    const response = await api.post(`${API_BASE_URL}/register`, 
      { username, password },
      {
        headers: {
          'Content-Type': 'application/json',
        },
      }
    );
    return response.data;
  },

  logout: async (): Promise<void> => {
    await api.post(`${API_BASE_URL}/logout`);
  },

  // 요람 목록 조회
  getAgents: async (): Promise<any[]> => {
    const response = await api.get(`${API_BASE_URL}/api/agents`);
    return response.data;
  },

  // 요람 등록
  registerCradle: async (cradleUuid: string): Promise<any> => {
    const response = await api.post(`${API_BASE_URL}/register_cradle`, 
      { cradle_uuid: cradleUuid },
      {
        headers: {
          'Content-Type': 'application/json',
        },
      }
    );
    return response.data;
  },

  // 요람 선택
  selectCradle: async (uuid: string): Promise<any> => {
    const response = await api.post(`${API_BASE_URL}/select_cradle`, 
      { uuid },
      {
        headers: {
          'Content-Type': 'application/json',
        },
      }
    );
    return response.data;
  },

  // 요람 삭제
  deleteCradle: async (uuid: string): Promise<any> => {
    const response = await api.post(`${API_BASE_URL}/delete_cradle`, 
      { uuid },
      {
        headers: {
          'Content-Type': 'application/json',
        },
      }
    );
    return response.data;
  },

  // 에이전트 상태 조회
  getAgentStatus: async (uuid: string): Promise<AgentStatus> => {
    const response = await api.get(`${API_BASE_URL}/api/agent_status/${uuid}`);
    return response.data;
  },

  // 알림 설정 조회
  getAlertSettings: async (uuid: string): Promise<AlertSettings> => {
    const response = await api.get(`${API_BASE_URL}/api/alert_settings/${uuid}`);
    return response.data;
  },

  // 센서 데이터 조회
  getSensorData: async (
    uuid: string,
    startDate: string,
    endDate: string
  ): Promise<SensorData[]> => {
    const response = await api.get(`${API_BASE_URL}/api/sensor_data/${uuid}`, {
      params: {
        start_date: startDate,
        end_date: endDate,
      },
    });
    return response.data;
  },

  // 알림 로그 조회
  getAlertLogs: async (): Promise<AlertLog[]> => {
    const response = await api.get(`${API_BASE_URL}/api/alert_logs`);
    return response.data;
  },

  // 알림 해결 처리
  resolveAlert: async (logId: number): Promise<void> => {
    await api.post(`${API_BASE_URL}/api/alert_logs/${logId}/resolve`);
  },

  // 알림 설정 업데이트
  updateAlertSettings: async (
    uuid: string,
    settings: Partial<AlertSettings>
  ): Promise<void> => {
    await api.post(`${API_BASE_URL}/api/alert_settings/${uuid}`, settings);
  },

  // 모터 제어
  controlMotor: async (uuid: string, action: 'start' | 'stop'): Promise<void> => {
    await api.post(`${API_BASE_URL}/control_motor/${uuid}`, { action });
  },

  // 비디오 URL 가져오기
  getVideoUrl: (uuid: string, date: string, time: string): string => {
    return `${API_BASE_URL}/api/video/${uuid}?date=${date}&time=${time}`;
  },

  // 비디오 스트림 URL
  getStreamUrl: (uuid: string): string => {
    return `${API_BASE_URL}/stream/${uuid}`;
  },

  // 알림 히스토리 조회
  getAlertHistory: async (uuid: string): Promise<any[]> => {
    const response = await api.get(`${API_BASE_URL}/api/alert_history/${uuid}`);
    return response.data;
  },

  // 알림 상세 정보 조회
  getAlertDetail: async (alertId: number): Promise<any> => {
    const response = await api.get(`${API_BASE_URL}/api/alert_detail/${alertId}`);
    return response.data;
  },

  // 알림 프레임 URL 가져오기
  getAlertFrameUrl: (frameId: number): string => {
    return `${API_BASE_URL}/api/alert_frame/${frameId}`;
  },
};

export default api;
