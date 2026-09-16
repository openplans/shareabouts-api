## ADDED Requirements

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
