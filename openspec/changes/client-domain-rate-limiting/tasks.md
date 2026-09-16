## 1. Variable Configuration

- [ ] 1.1 Add input variables in `infra/gcp-domains/variables.tf` for client rate limiting (`enable_client_rate_limiting`, `client_rate_limit_count`, `client_rate_limit_interval_sec`, `client_rate_limit_preview`)
- [ ] 1.2 Update `infra/gcp-domains/.auto.tfvars` and `.auto.tfvars.example` with default rate limiting configurations

## 2. Cloud Armor Security Policy

- [ ] 2.1 Add dynamic rate-limiting rule (priority 950) with `rate_limit_options` in `infra/gcp-domains/security.tf`
- [ ] 2.2 Configure CEL match expression to target client host domains while excluding API server domains

## 3. Validation and Deployment

- [ ] 3.1 Run `tofu validate` and `tofu plan` in `infra/gcp-domains` to verify configuration syntax and execution plan
- [ ] 3.2 Apply the plan with `tofu apply` and verify Cloud Armor rate limiting rule is active
