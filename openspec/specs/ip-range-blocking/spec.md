## Purpose

Configures IP range blocklists at the GCP load balancer level to reject abusive network traffic before it reaches backend services.

## Requirements

### Requirement: Block Traffic from Specified IP Ranges
The load balancer security policy SHALL deny HTTP requests originating from client IP addresses matching configured CIDR ranges with a 403 Forbidden status code.

#### Scenario: Request from a blocked IP CIDR range
- **WHEN** an HTTP request is received from an IP address within a configured blocked CIDR range
- **THEN** the load balancer immediately responds with HTTP status 403 Forbidden without forwarding the request to Cloud Run

#### Scenario: Request from an unblocked IP address
- **WHEN** an HTTP request is received from an IP address outside the configured blocked CIDR ranges
- **THEN** the load balancer evaluates default rules and forwards legitimate traffic to Cloud Run

### Requirement: Configurable IP Blocklist Ranges via Infrastructure Code
The infrastructure module SHALL accept a configurable list of IP CIDR strings for the load balancer security policy.

#### Scenario: Adding a new IP range to the blocklist
- **WHEN** a new IP CIDR range is added to the Terraform variable `blocked_ip_ranges` and applied
- **THEN** Cloud Armor updates the security policy rule set to block requests from that CIDR range
