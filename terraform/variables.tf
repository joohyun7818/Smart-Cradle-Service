# GCP 프로젝트 설정
variable "project_id" {
  description = "GCP 프로젝트 ID"
  type        = string
}

variable "region" {
  description = "GCP 리전"
  type        = string
  default     = "asia-northeast3"
}

variable "zone" {
  description = "GCP 존"
  type        = string
  default     = "asia-northeast3-a"
}

# 인스턴스 타입
variable "server_machine_type" {
  description = "서버 인스턴스 머신 타입"
  type        = string
  default     = "t2a-standard-1"
}

variable "db_machine_type" {
  description = "DB 인스턴스 머신 타입"
  type        = string
  default     = "t2a-standard-1"
}

# MySQL 설정
variable "mysql_root_password" {
  description = "MySQL root 비밀번호"
  type        = string
  sensitive   = true
}

variable "mysql_database" {
  description = "MySQL 데이터베이스 이름"
  type        = string
  default     = "smartcradle"
}

variable "mysql_user" {
  description = "MySQL 사용자 이름"
  type        = string
  default     = "sc_user"
}

variable "mysql_password" {
  description = "MySQL 사용자 비밀번호"
  type        = string
  sensitive   = true
}

# Flask 설정
variable "secret_key" {
  description = "Flask SECRET_KEY"
  type        = string
  sensitive   = true
}

# Docker 설정
variable "docker_image" {
  description = "사용할 Docker 이미지"
  type        = string
  default     = "joohyun7818/smart-cradle-flask:latest"
}

# SSH 공개키 설정
variable "ssh_public_key_path" {
  description = "SSH 공개키 파일 경로"
  type        = string
  default     = "~/.ssh/vm_key.pub"
}

variable "ssh_username" {
  description = "SSH 접속 사용자명"
  type        = string
  default     = "admin"
}
