## 1. Variable Configuration

- [x] 1.1 Add `blocked_datasets` input variable in `infra/gcp-domains/variables.tf` as `list(object({ owner = string, slug = string }))`
- [x] 1.2 Update `infra/gcp-domains/.auto.tfvars.example` with example `blocked_datasets` configurations
- [x] 1.3 Add defunct datasets identified from production logs (including historical `ourmiami` and `pbnyc` cycles) to `infra/gcp-domains/.auto.tfvars`

## 2. Cloud Armor Security Policy

- [x] 2.1 Update `locals` in `infra/gcp-domains/security.tf` to include `blocked_datasets` in `has_security_rules` and construct the regex alternation match expression
- [x] 2.2 Add dynamic Cloud Armor rule at priority 920 with action `deny(404)` in `infra/gcp-domains/security.tf`

## 3. Validation and Deployment

- [x] 3.1 Run `tofu validate` and `tofu plan` in `infra/gcp-domains/` to verify syntax and inspect the proposed Cloud Armor rule diff
- [x] 3.2 Apply the plan with `tofu apply` and verify via curl/logs that requests to blocked dataset paths return HTTP 404 without reaching Cloud Run

