## 1. Terraform Variable & Local Declarations

- [x] 1.1 Declare `block_php_requests` and `blocked_referer_domains` input variables in `infra/gcp-domains/variables.tf`
- [x] 1.2 Define local CEL expression generator for blocked referers in `infra/gcp-domains/security.tf`

## 2. Cloud Armor Security Policy Rules

- [x] 2.1 Add Cloud Armor rule for blocking `.php` requests (priority 900) in `infra/gcp-domains/security.tf`
- [x] 2.2 Add Cloud Armor rule for blocking abusive API referers (priority 910) in `infra/gcp-domains/security.tf`

## 3. Configuration & Cleanup

- [x] 3.1 Update `infra/gcp-domains/.auto.tfvars` with blocked referer domains and remove invalid `169.254.169.126/32` entry
- [x] 3.2 Update `infra/gcp-domains/.auto.tfvars.example` with documentation and examples for the new variables

## 4. Verification & Validation

- [x] 4.1 Validate OpenTofu / Terraform configuration syntax and plan in `infra/gcp-domains/`
- [x] 4.2 Run `openspec validate` to ensure change and spec coherence
