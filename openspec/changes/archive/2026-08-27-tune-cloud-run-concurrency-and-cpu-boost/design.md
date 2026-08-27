## Context

The Shareabouts API service runs on Cloud Run via OpenTofu/Terraform (`infra/gcp/modules/shareabouts-service`). Currently, containers run Gunicorn with 4 synchronous worker processes (`WORKERS=4`). Because `max_instance_request_concurrency` is omitted, Cloud Run defaults to 80 concurrent requests per instance. During traffic bursts, requests queue inside the container's TCP socket buffer before Cloud Run triggers scaling. Furthermore, new instance cold starts take 10–13 seconds to initialize GeoDjango C extensions on 1 vCPU.

See `proposal.md` for motivation and `specs/cloud-run-scaling-tuning/spec.md` for requirements.

## Goals / Non-Goals

**Goals:**
- Set Cloud Run container concurrency to match the number of active Gunicorn workers (`var.workers`, default 4).
- Enable `startup_cpu_boost` on Cloud Run containers to accelerate Python/GeoDjango initialization during autoscaling scale-out.
- Add an explicit `container_concurrency` variable to `shareabouts-service` module (defaulting to the numeric value of `var.workers`).
- Preserve existing instance limits (`min_instances = 1`, `max_instances = 5` in prod) for cost control and database safety.

**Non-Goals:**
- Modifying Gunicorn worker architecture (e.g. switching to asyncio or thread pools).
- Changing Cloud SQL instance tier or connection pooler setup.

## Decisions

### Decision: Concurrency = Workers (4) vs 2x (8)
- **Choice**: Match `container_concurrency` directly to `var.workers` (e.g. 4).
- **Rationale**: Since Gunicorn workers are synchronous, a 5th concurrent request cannot be served concurrently by that container and would otherwise wait. With concurrency set to 4, Cloud Run routes the 5th request to another warm instance or immediately begins scaling out, keeping queue times to a minimum.
- **Alternatives Considered**:
  - *2x Concurrency (8)*: Assumes I/O wait creates capacity for multiplexing, but with sync workers, requests still block sequentially in the OS socket buffer.
  - *Keep Default (80)*: Causes severe head-of-line blocking and delayed scale-out.

### Decision: Enabling Startup CPU Boost
- **Choice**: Set `startup_cpu_boost = true` in container specifications.
- **Rationale**: Startup CPU boost temporarily increases CPU allocation during container initialization and worker startup at no extra cost (billed only for baseline instance resources), significantly reducing the 10–13s cold start latency.

## Risks / Trade-offs

- **[Risk] Faster Autoscaling Scale-out**: Instances spin up more aggressively when concurrency reaches 4.
  - **Mitigation**: Total instances are capped by `max_instances = 5` in prod, ensuring maximum cluster concurrency is 20 (well within `db-f1-micro`'s 25–50 connection limit and keeping billing bounded).
- **[Risk] Queueing during peak overload (>20 concurrent requests)**:
  - **Mitigation**: Cloud Run automatically holds excess requests in Google's managed ingress queue for up to 60 seconds and dispatches them as soon as any worker completes.

## Migration Plan

1. Add `container_concurrency` variable to `infra/gcp/modules/shareabouts-service/variables.tf`.
2. Update `google_cloud_run_v2_service` in `infra/gcp/modules/shareabouts-service/main.tf` to set `max_instance_request_concurrency` and `startup_cpu_boost`.
3. Pass `container_concurrency` (or rely on default) in `infra/gcp/envs/prod/main.tf` and `infra/gcp/envs/dev/main.tf`.
4. Run `tofu plan` in `infra/gcp/envs/prod/` and review changes.
5. Deploy with `tofu apply`.
