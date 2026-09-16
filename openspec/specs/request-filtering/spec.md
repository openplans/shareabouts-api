# request-filtering Specification

## Purpose

Configures request-level Cloud Armor filtering rules to reject abusive HTTP request patterns (such as PHP exploit scans and self-referencing API scraper referers) at the load balancer level before they reach backend services.

## Requirements

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

### Requirement: Block Requests for Defunct Datasets
The load balancer security policy SHALL deny HTTP requests targeting configured blocked datasets (specified by owner and slug pairs, e.g., `/api/v2/<owner>/datasets/<slug>`) at the Cloud Armor edge, returning an HTTP 404 Not Found or HTTP 403 Forbidden status code without forwarding traffic to backend services.

#### Scenario: Request targeting a blocked dataset root or sub-resource
- **WHEN** an HTTP request is received for a path matching a configured blocked dataset (e.g., `/api/v2/ourmiami/datasets/psc2014`, `/api/v2/pbnyc/datasets/pbnyc-2018/places/123/support/456?format=csv`)
- **THEN** the load balancer denies the request immediately with an HTTP 404 or 403 response without invoking backend Cloud Run instances

#### Scenario: Request targeting an active or unblocked dataset
- **WHEN** an HTTP request is received for an active dataset not in the blocked list (e.g., `/api/v2/cambridge/datasets/pb-fy2028/actions`)
- **THEN** the request is permitted by the dataset filtering rule and forwarded to the backend service

### Requirement: Configurable Blocked Datasets in Infrastructure
The infrastructure module SHALL parameterize blocked datasets as a list of owner and slug pairs in Terraform/OpenTofu variables, allowing operators to block or unblock datasets without modifying core security rule logic.

#### Scenario: Updating blocked datasets via variable configuration
- **WHEN** an owner and slug entry is added to or removed from the `blocked_datasets` list in `.auto.tfvars`
- **THEN** Cloud Armor dynamically updates the security policy match expression to reflect the current list of blocked datasets

