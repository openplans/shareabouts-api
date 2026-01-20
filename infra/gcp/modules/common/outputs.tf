output "vpc_id" {
  value = google_compute_network.vpc.id
}

output "vpc_connector_id" {
  value = google_vpc_access_connector.connector.id
}

output "db_instance_name" {
  value = google_sql_database_instance.instance.name
}

output "db_private_ip" {
  value = google_sql_database_instance.instance.private_ip_address
}

output "redis_host" {
  value = google_redis_instance.cache.host
}

output "redis_port" {
  value = google_redis_instance.cache.port
}
