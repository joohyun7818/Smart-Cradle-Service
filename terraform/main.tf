# Terraform 버전 및 Provider 설정
terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# VPC 네트워크
resource "google_compute_network" "smart_cradle_network" {
  name                    = "smart-cradle-network"
  auto_create_subnetworks = false
}

# 서브넷
resource "google_compute_subnetwork" "smart_cradle_subnet" {
  name          = "smart-cradle-subnet"
  ip_cidr_range = "10.128.0.0/20"
  region        = var.region
  network       = google_compute_network.smart_cradle_network.id
}

# 방화벽 규칙 - SSH
resource "google_compute_firewall" "allow_ssh" {
  name    = "smart-cradle-allow-ssh"
  network = google_compute_network.smart_cradle_network.name

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }

  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["smart-cradle-server", "smart-cradle-db"]
}

# 방화벽 규칙 - HTTP (서버 인스턴스)
resource "google_compute_firewall" "allow_http" {
  name    = "smart-cradle-allow-http"
  network = google_compute_network.smart_cradle_network.name

  allow {
    protocol = "tcp"
    ports    = ["80"]
  }

  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["smart-cradle-server"]
}

# 방화벽 규칙 - MQTT (서버 인스턴스)
resource "google_compute_firewall" "allow_mqtt" {
  name    = "smart-cradle-allow-mqtt"
  network = google_compute_network.smart_cradle_network.name

  allow {
    protocol = "tcp"
    ports    = ["1883"]
  }

  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["smart-cradle-server"]
}

# 방화벽 규칙 - MySQL (내부 네트워크만 허용)
resource "google_compute_firewall" "allow_mysql_internal" {
  name    = "smart-cradle-allow-mysql-internal"
  network = google_compute_network.smart_cradle_network.name

  allow {
    protocol = "tcp"
    ports    = ["3306"]
  }

  source_tags = ["smart-cradle-server"]
  target_tags = ["smart-cradle-db"]
}

# 방화벽 규칙 - 내부 통신
resource "google_compute_firewall" "allow_internal" {
  name    = "smart-cradle-allow-internal"
  network = google_compute_network.smart_cradle_network.name

  allow {
    protocol = "tcp"
    ports    = ["0-65535"]
  }

  allow {
    protocol = "udp"
    ports    = ["0-65535"]
  }

  allow {
    protocol = "icmp"
  }

  source_ranges = ["10.128.0.0/20"]
}

# 시작 스크립트 템플릿
locals {
  # SSH 공개키 읽기
  ssh_public_key_content = trimspace(file(pathexpand(var.ssh_public_key_path)))
  
  # DB 인스턴스용 시작 스크립트
  db_startup_script = templatefile("${path.module}/scripts/db_startup.sh", {
    mysql_root_password = var.mysql_root_password
    mysql_database      = var.mysql_database
    mysql_user          = var.mysql_user
    mysql_password      = var.mysql_password
    ssh_public_key      = local.ssh_public_key_content
  })
}

# DB 인스턴스
resource "google_compute_instance" "db_instance" {
  name         = "smart-cradle-db"
  machine_type = var.db_machine_type
  zone         = var.zone

  tags = ["smart-cradle-db"]

  boot_disk {
    initialize_params {
      image = "ubuntu-os-cloud/ubuntu-2204-lts"
      size  = 20
      type  = "pd-standard"
    }
  }

  network_interface {
    subnetwork = google_compute_subnetwork.smart_cradle_subnet.id
    access_config {
      // Ephemeral public IP
    }
  }

  metadata = {
    startup-script = local.db_startup_script
    ssh-keys       = "${var.ssh_username}:${file(pathexpand(var.ssh_public_key_path))}"
  }

  service_account {
    scopes = ["cloud-platform"]
  }

  allow_stopping_for_update = true
}

# 서버 인스턴스
resource "google_compute_instance" "server_instance" {
  name         = "smart-cradle-server"
  machine_type = var.server_machine_type
  zone         = var.zone

  tags = ["smart-cradle-server"]

  boot_disk {
    initialize_params {
      image = "ubuntu-os-cloud/ubuntu-2204-lts"
      size  = 30
      type  = "pd-standard"
    }
  }

  network_interface {
    subnetwork = google_compute_subnetwork.smart_cradle_subnet.id
    access_config {
      // Ephemeral public IP
    }
  }

  metadata = {
    startup-script = templatefile("${path.module}/scripts/server_startup.sh", {
      mysql_host       = google_compute_instance.db_instance.network_interface[0].network_ip
      mysql_port       = "3306"
      mysql_database   = var.mysql_database
      mysql_user       = var.mysql_user
      mysql_password   = var.mysql_password
      mqtt_broker_host = "mosquitto"
      mqtt_broker_port = "1883"
      secret_key       = var.secret_key
      docker_image     = var.docker_image
      ssh_public_key   = local.ssh_public_key_content
    })
    ssh-keys = "${var.ssh_username}:${file(pathexpand(var.ssh_public_key_path))}"
  }

  service_account {
    scopes = ["cloud-platform"]
  }

  allow_stopping_for_update = true

  depends_on = [google_compute_instance.db_instance]
}
