# cloud-run-scaling-tuning Specification

## Purpose

Defines infrastructure requirements for Cloud Run instance request concurrency and container startup performance to prevent request queuing during traffic spikes and accelerate instance scale-out.

## Requirements

### Requirement: Aligned Container Request Concurrency
The infrastructure configuration SHALL set Cloud Run `max_instance_request_concurrency` to match the synchronous Gunicorn worker process count configured for the container instance.

#### Scenario: Request burst triggers immediate scale-out
- **WHEN** the number of concurrent in-flight requests on an instance reaches the worker capacity (e.g., 4 requests)
- **THEN** Cloud Run immediately routes subsequent requests to additional available instances or triggers scaling out a new instance rather than queueing requests inside the busy container's socket buffer

#### Scenario: Ingress queueing when cluster reaches max instances
- **WHEN** all active instances are serving at maximum concurrency and `max_instances` has been reached
- **THEN** Cloud Run holds excess requests in the managed ingress queue for up to the pending request timeout rather than dropping them immediately

### Requirement: Startup CPU Boost for Container Provisioning
The infrastructure configuration SHALL enable startup CPU boost on Cloud Run service containers.

#### Scenario: New instance cold start under load
- **WHEN** Cloud Run provisions a new container revision instance during an autoscaling scale-out event
- **THEN** extra CPU capacity is allocated to the container during startup to accelerate Python package imports and Django worker process initialization
