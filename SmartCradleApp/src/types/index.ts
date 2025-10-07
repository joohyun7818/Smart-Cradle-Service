// 타입 정의
export interface AgentStatus {
  agent_uuid: string;
  temperature: number | null;
  crying: string | null;
  direction: string | null;
  face_direction: string | null;
  last_direction_time: string | null;
  last_normal_face_time: string | null;
  last_update: string | null;
}

export interface SensorData {
  timestamp: string;
  temperature: number | null;
  crying: string | null;
  direction: string | null;
}

export interface AlertLog {
  id: number;
  agent_uuid?: string;
  alert_type: string;
  alert_message: string;
  message?: string;
  temperature: number | null;
  face_detected: boolean | null;
  notification_sent?: boolean;
  resolved: boolean;
  created_at: string;
  resolved_at: string | null;
}

export interface AlertHistory {
  id: number;
  alert_type: string;
  alert_message: string;
  temperature: number | null;
  face_detected: boolean | null;
  resolved: boolean;
  created_at: string;
  resolved_at: string | null;
}

export interface AlertDetail {
  alert: AlertHistory;
  sensor_data: SensorData[];
  video_frames: VideoFrameInfo[];
  total_frames: number;
}

export interface VideoFrameInfo {
  id: number;
  timestamp: string;
}

export interface AlertSettings {
  max_temperature: number;
  abnormal_position_timeout: number;
  crying_duration_threshold: number;
  push_notifications_enabled: boolean;
  email_notifications_enabled: boolean;
}

export interface Agent {
  id: number;
  uuid: string;
  ip: string;
  created_at: string;
  updated_at: string;
}

export interface User {
  id: number;
  username: string;
}

export interface LoginResponse {
  success: boolean;
  message?: string;
  user?: User;
}
