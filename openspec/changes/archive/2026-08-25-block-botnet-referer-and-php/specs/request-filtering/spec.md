## Purpose

Configures request-level Cloud Armor filtering rules to reject abusive HTTP request patterns (such as PHP exploit scans and self-referencing API scraper referers) at the load balancer level before they reach backend services.

## ADDED Requirements

### Requirement: Block Requests for PHP Resources
The load balancer security policy SHALL deny HTTP requests whose path ends with `.php` with an HTTP 403 Forbidden status code.

#### Scenario: Request targeting a .php resource
- **WHEN** an HTTP request is received with a path ending in `.php` (e.g., `/term.php`, `/wp_filemanager.php`)
- **THEN** the load balancer immediately responds with HTTP status 403 Forbidden without forwarding the request to backend services

#### Scenario: Request targeting standard non-PHP application paths
- **WHEN** an HTTP request is received for normal application endpoints (e.g., `/api/v2/...`, `/admin/...`, `/static/...`)
- **THEN** the PHP filtering rule allows the request to continue through subsequent security policy rules

### Requirement: Block Requests to API Endpoints with Suspicious Self-Referencing Referers
The load balancer security policy SHALL deny HTTP requests to `/api/` endpoints whose `Referer` header matches configured blocked referer domains, responding with an HTTP 403 Forbidden status code.

#### Scenario: Scraper request to /api/ with blocked referer
- **WHEN** an HTTP request is received for a path beginning with `/api/` and contains a `Referer` header matching a configured blocked referer URL (e.g., `https://shareaboutsapi.poepublic.com`)
- **THEN** the load balancer immediately responds with HTTP status 403 Forbidden without forwarding the request to Cloud Run

#### Scenario: Admin panel request with same-origin referer
- **WHEN** an HTTP request is received for `/admin/` or `/static/` paths with a same-origin referer (e.g., `https://shareaboutsapi.poepublic.com/admin/sa_api_v2/place/`)
- **THEN** the API referer filtering rule does not match and the request is allowed to proceed

#### Scenario: Legitimate frontend client request to /api/
- **WHEN** an HTTP request is received for `/api/` endpoints with a cross-origin referer from a legitimate civic application domain (e.g., `https://pbideas.cambridgema.gov`) or without a referer
- **THEN** the request is allowed to proceed to the backend service

### Requirement: Configurable Filtering Rules in Infrastructure
The infrastructure module SHALL parameterize blocked referer domains and filtering toggles as Terraform input variables, without hardcoding specific domain names into the core `.tf` policy definition.

#### Scenario: Updating blocked referer domains via variables
- **WHEN** a domain is added or modified in the `blocked_referer_domains` list variable in `.auto.tfvars`
- **THEN** Cloud Armor dynamically constructs the match expression to block that referer domain across the security policy
