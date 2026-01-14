output "service_url" {
  value = google_cloud_run_v2_service.default.uri
}

output "database_connection_name" {
  value = google_sql_database_instance.instance.connection_name
}

output "redis_host" {
  value = google_redis_instance.cache.host
}

output "bucket_name" {
  value = google_storage_bucket.static.name
}
