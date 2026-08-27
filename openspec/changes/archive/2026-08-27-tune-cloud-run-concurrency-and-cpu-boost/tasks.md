## 1. Module Configuration

- [x] 1.1 Add `container_concurrency` variable to `infra/gcp/modules/shareabouts-service/variables.tf` (number, default null)
- [x] 1.2 Update `google_cloud_run_v2_service` in `infra/gcp/modules/shareabouts-service/main.tf` to set `max_instance_request_concurrency` and `startup_cpu_boost = true`

## 2. Environment Configuration

- [x] 2.1 Update `infra/gcp/envs/prod/main.tf` to pass `container_concurrency` or verify default alignment with `var.workers`
- [x] 2.2 Update `infra/gcp/envs/dev/main.tf` to pass `container_concurrency` or verify default alignment with `var.workers`

## 3. Validation and Deployment

- [x] 3.1 Run `tofu validate` and `tofu plan` in `infra/gcp/envs/prod/` to verify execution plan
- [x] 3.2 Apply the plan with `tofu apply` in `infra/gcp/envs/prod/` and verify Cloud Run revision settings
