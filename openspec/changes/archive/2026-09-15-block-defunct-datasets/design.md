## Context

See `proposal.md` for motivation. The Cloud Armor security policy attached to the production load balancer (`custom-domains-b84d-ip-blocklist` in `infra/gcp-domains/security.tf`) currently evaluates three rules before the default allow rule:
- Priority 900: Blocks requests ending in `.php` (`deny(403)`)
- Priority 910: Blocks API requests presenting self-referencing root referers without session cookies (`deny(403)`)
- Priority 1000: Blocks specific source IP CIDRs (`deny(403)`)

Because distributed crawlers evade IP and referer filters, blocking abusive requests based on the requested dataset path at the Cloud Armor layer intercepts the traffic at Google's global edge network before requests ever reach Cloud Run or Cloud SQL.

## Goals / Non-Goals

**Goals:**
- Provide a `blocked_datasets` variable in `infra/gcp-domains/` accepting a list of `{ owner = string, slug = string }` pairs.
- Generate a Cloud Armor CEL rule that matches any request targeting `/api/v2/<owner>/datasets/<slug>` (and all sub-resources such as `/places/...`, `/comments/...`, `/support/...`).
- Deny matching requests immediately at the edge with HTTP 404 Not Found (or 403).
- Configure all known defunct datasets from production logs (e.g. historical `ourmiami` and `pbnyc` cycles) in `infra/gcp-domains/.auto.tfvars`.

**Non-Goals:**
- Modifying Django application code or database schema (datasets remain intact in the database).
- Rate-limiting active datasets (handled separately).
- Altering SSL certificates or host routing rules.

## Decisions

### Decision 1: Match paths using regex alternation in CEL
* **Choice**: `request.path.matches('^/api/v2/(%s)(/.*)?$')` where the inner token is a pipe-separated alternation (`join("|", ...)`) of formatted dataset path prefixes.
* **Rationale**: Cloud Armor imposes a limit on the number of individual boolean sub-expressions per rule (max 10). By combining dataset pairs into a single regular expression alternation, dozens of datasets can be blocked within a single security rule without hitting CEL expression limits.
* **Alternative considered**: Multiple rules (one per dataset) or a large chain of `||` `request.path.startsWith(...)`. This would quickly exceed Cloud Armor rule count and expression complexity limits.

### Decision 2: Deny action with HTTP 404 Not Found
* **Choice**: Action `deny(404)`.
* **Rationale**: For scrapers and search bots, HTTP 404 indicates the resource does not exist, prompting crawlers to drop the URLs from their crawl queues. In contrast, 429 or 403 signals temporary throttling or permission gates, encouraging bots to retry.
* **Alternative considered**: `deny(403)`. While functional, 403 suggests authorization issues rather than resource retirement.

### Decision 3: Structured object variable type
* **Choice**:
  ```hcl
  variable "blocked_datasets" {
    type = list(object({
      owner = string
      slug  = string
    }))
    default = []
  }
  ```
* **Rationale**: Enforces schema validation at OpenTofu plan time and matches the Shareabouts resource hierarchy (`/api/v2/<owner>/datasets/<slug>`).

### Decision 4: Rule Priority 920
* **Choice**: Assign priority `920` in Cloud Armor, placing it directly after the referer rule (910) and before the IP CIDR blocklist (1000).

## Risks / Trade-offs

- **[Risk] Accidental blocking of an active dataset**
  → *Mitigation*: Verify every dataset slug against active frontend services (e.g. ensure `cambridge/pb-fy2028` and active Boston/Somerville cycles are never listed). Unblocking is as simple as removing an entry from `.auto.tfvars` and running `tofu apply`.
- **[Risk] Path variations or URL-encoded paths**
  → *Mitigation*: The regex matches `^/api/v2/<owner>/datasets/<slug>(/.*)?$`, covering dataset root, places, submissions, actions, and snapshots regardless of query parameters.
