## Why

Cloud Run service revisions currently use a default `containerConcurrency` of 80 despite running only 4 synchronous Gunicorn worker processes per container. When traffic bursts arrive, excess requests queue inside the container's socket backlog instead of immediately scaling out to additional instances. Additionally, when new instances scale out, cold start latency reaches 10–13 seconds due to GeoDjango and GDAL initialization thrashing on a single vCPU. Aligning container concurrency with worker capacity and enabling startup CPU boost reduces queuing delays and accelerates autoscaling.

## What Changes

- Align Cloud Run's `max_instance_request_concurrency` with the configured `workers` count (default 4), so Cloud Run immediately triggers instance scale-out when active workers are saturated.
- Enable `startup_cpu_boost = true` on the Cloud Run service container definition to allocate extra CPU during container boot and worker startup.
- Expose `container_concurrency` as a configurable variable in the `shareabouts-service` Terraform module with a default value equal to `var.workers`.
- Maintain existing `min_instances = 1` and `max_instances = 5` safeguards in the production environment to protect costs and database connection limits.

## Capabilities

### New Capabilities
- `cloud-run-scaling-tuning`: Configures Cloud Run instance request concurrency limits aligned with synchronous worker processes and enables startup CPU boost for faster container initialization.

### Modified Capabilities
<!-- None -->

## Impact

- **Infrastructure as Code**: Updates to `infra/gcp/modules/shareabouts-service/main.tf` and `infra/gcp/modules/shareabouts-service/variables.tf`.
- **Environment Configurations**: `infra/gcp/envs/prod/main.tf` and `infra/gcp/envs/dev/main.tf`.
- **Performance**: Eliminates in-container request queuing during bursts and cuts cold start scale-out time.
