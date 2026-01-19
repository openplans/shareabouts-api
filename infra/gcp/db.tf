# Cloud SQL instance is shared across environments; different databases are
# created within the instance for each environment.
resource "google_sql_database_instance" "instance" {
  name             = "${var.service_name}-db-instance"
  region           = var.region
  database_version = "POSTGRES_15"
  depends_on       = [google_service_networking_connection.private_vpc_connection]

  settings {
    tier = "db-f1-micro" # Smallest for testing
    ip_configuration {
      ipv4_enabled    = false
      private_network = google_compute_network.vpc.id
    }
  }
  deletion_protection = false # For easier cleanup during testing
}

resource "google_sql_database" "database" {
  name     = "${var.service_name}-${var.environment}"
  instance = google_sql_database_instance.instance.name
}

resource "google_sql_user" "user" {
  name     = "${var.service_name}-${var.environment}"
  instance = google_sql_database_instance.instance.name
  password = random_password.db_password.result
}
