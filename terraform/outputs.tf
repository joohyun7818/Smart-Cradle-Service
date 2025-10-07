# 서버 인스턴스 정보
output "server_instance_name" {
  description = "서버 인스턴스 이름"
  value       = google_compute_instance.server_instance.name
}

output "server_instance_external_ip" {
  description = "서버 인스턴스 외부 IP"
  value       = google_compute_instance.server_instance.network_interface[0].access_config[0].nat_ip
}

output "server_instance_internal_ip" {
  description = "서버 인스턴스 내부 IP"
  value       = google_compute_instance.server_instance.network_interface[0].network_ip
}

# DB 인스턴스 정보
output "db_instance_name" {
  description = "DB 인스턴스 이름"
  value       = google_compute_instance.db_instance.name
}

output "db_instance_external_ip" {
  description = "DB 인스턴스 외부 IP"
  value       = google_compute_instance.db_instance.network_interface[0].access_config[0].nat_ip
}

output "db_instance_internal_ip" {
  description = "DB 인스턴스 내부 IP"
  value       = google_compute_instance.db_instance.network_interface[0].network_ip
}

# 접속 정보
output "web_url" {
  description = "웹 서비스 URL"
  value       = "http://${google_compute_instance.server_instance.network_interface[0].access_config[0].nat_ip}"
}

output "ssh_command_server" {
  description = "서버 인스턴스 SSH 접속 명령어 (gcloud)"
  value       = "gcloud compute ssh ${google_compute_instance.server_instance.name} --zone=${var.zone}"
}

output "ssh_command_db" {
  description = "DB 인스턴스 SSH 접속 명령어 (gcloud)"
  value       = "gcloud compute ssh ${google_compute_instance.db_instance.name} --zone=${var.zone}"
}

output "ssh_direct_command_server" {
  description = "서버 인스턴스 직접 SSH 접속 명령어 (키 사용)"
  value       = "ssh -i ~/.ssh/vm_key ${var.ssh_username}@${google_compute_instance.server_instance.network_interface[0].access_config[0].nat_ip}"
}

output "ssh_direct_command_db" {
  description = "DB 인스턴스 직접 SSH 접속 명령어 (키 사용)"
  value       = "ssh -i ~/.ssh/vm_key ${var.ssh_username}@${google_compute_instance.db_instance.network_interface[0].access_config[0].nat_ip}"
}
