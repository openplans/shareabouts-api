# Memorystore for Redis instance is shared across environments; use
# environment name as key prefix to differentiate.
resource "google_redis_instance" "cache" {
  name           = "${var.service_name}-redis"
  tier           = "BASIC"
  memory_size_gb = 1
  region         = var.region

  authorized_network = google_compute_network.vpc.id
  connect_mode       = "DIRECT_PEERING"

  depends_on = [google_service_networking_connection.private_vpc_connection]
}
