# Engineering Rulebook & Agent Guidelines

## Project: DevOps Monitoring & Observability Dashboard

---

## 1. General Principles

1. **Understand Before Modifying:** Always inspect existing code, directory structures, and configurations before writing or editing files. Do not guess file structures or assume dependencies exist.
2. **Prefer Simplicity over Premature Abstraction:** Choose direct, readable, maintainable solutions. Avoid over-engineering, unnecessary design patterns, or introducing complex helper frameworks when standard libraries suffice.
3. **Justify Every Dependency:** Do not add third-party libraries or external tools unless there is a clear, documented requirement. Every added dependency increases build time, container footprint, and security exposure.
4. **Scope Isolation:** Modify only files directly related to the current assigned task. Never alter unrelated configuration files, dependencies, or documentation.
5. **Architectural Integrity:** Never silently alter the system architecture, port numbers, endpoint paths, or service communication patterns defined in `SystemArchitecture.md`.
6. **Zero Duplicate Functionality:** Ensure logging, metrics collection, and routing are implemented once at the canonical location. Do not build competing implementations.
7. **Independent Deployability:** Maintain clear decoupled boundaries so that the application service, Prometheus, Loki, and Grafana can be run together in Kubernetes or isolated via Docker Compose.
8. **Truthful Validation:** Never declare a task complete without executing concrete validation commands (e.g. running pytest, verifying HTTP status codes, inspecting Docker builds). Do not assume code works because it was generated.
9. **Synchronized Documentation:** Whenever an interface, environment variable, or configuration schema is updated, immediately update the relevant documentation in `docs/` and log the modification in `memory.md`.

---

## 2. Technology Standards

### 2.1 Git & Version Control
- Commit messages must follow the Conventional Commits specification:
  - `feat: add prometheus-fastapi-instrumentator integration`
  - `fix: resolve fluent-bit regex parser for ISO-8601 timestamps`
  - `chore: update dependencies in requirements.txt`
  - `ci: add trivy vulnerability scan step to github actions`
- Never commit sensitive secrets, `.env` files with production credentials, or build artifacts (`__pycache__`, `.pytest_cache`).

### 2.2 Bash & Automation Scripts
- Every shell script must include `set -euo pipefail` at the top to exit immediately on error or unset variables.
- Always quote variables (`"${VAR}"`) to avoid word splitting.
- Provide descriptive `echo "[INFO] ..."` or `echo "[ERROR] ..."` output statements for log clarity during pipeline execution.
- Include executable permissions (`chmod +x scripts/*.sh`).

### 2.3 Backend (Python & FastAPI)
- Target Python `3.11` runtime.
- Adhere strictly to PEP 8 style standards, validated using `flake8`.
- Use Pydantic models for request/response payloads to guarantee strict type enforcement.
- Keep route handlers asynchronous (`async def`) for I/O operations and synchronous for CPU-bound tasks.
- Keep endpoint business logic lean; separate routing (`main.py`) from configuration (`config.py`).

### 2.4 Metrics & Logging
- **Metrics Standard:** All Prometheus metrics must follow OpenMetrics naming conventions (snake_case, standard suffixes like `_total`, `_seconds`, `_bytes`).
- **Log Standard:** Logs must be emitted as single-line structured JSON to `stdout` / `stderr`. Human-readable multiline formatting is prohibited in container runtimes.
- Minimum required log fields: `timestamp` (ISO-8601 UTC), `level`, `logger`, `message`, `method`, `url`, `status_code`, `duration_ms`.
- Unhandled exceptions must include a structured `traceback` string in the JSON payload.

### 2.5 Testing
- Test framework: `pytest`.
- All endpoints (`/api/health`, `/api/data`, `/api/simulate-error`, `/metrics`) must have dedicated unit and integration tests.
- Mock external network calls; tests must execute without requiring active external clusters.
- Test coverage must remain at or above **80%** across the application codebase.

---

## 3. Docker Standards

1. **Multi-Stage Builds:** Dockerfiles must use multi-stage builds (`builder` stage for compiling wheels/dependencies, `runtime` stage containing only runtime requirements).
2. **Minimal Base Images:** Use official minimal base images (e.g., `python:3.11-slim`). Avoid heavy base images such as standard `python:3.11` or full Ubuntu images.
3. **Non-Root Execution:** Containers must create and switch to a non-privileged system user (e.g., `appuser:appgroup` with UID/GID 10001) before running the application process.
4. **Clean Build Context:** Always maintain a `.dockerignore` file excluding `.git`, `docs/`, `tests/`, `*.pyc`, `__pycache__`, `venv`, and local environment files.
5. **Layer Caching Optimization:** Copy dependency definition files (`requirements.txt`) and install dependencies *before* copying application source code to maximize Docker cache utilization.
6. **No Embedded Secrets:** Never bake API keys, passwords, or certificates into image layers or build arguments.
7. **Explicit Version Pinning:** Pin package versions in `requirements.txt` and base image tags in `Dockerfile` (e.g. `python:3.11-slim-bookworm`). Avoid generic tags like `latest`.

---

## 4. Kubernetes Standards

1. **Declarative Manifests:** All cluster state must be declared in YAML manifests under `k8s/`. Never rely on imperative commands (`kubectl run`, `kubectl expose`) for infrastructure definition.
2. **Explicit Namespaces:** All manifests must declare an explicit `metadata.namespace` or be deployed to targeted namespaces (`default` for app, `monitoring` for telemetry).
3. **Health Probes (Mandatory):**
   - Every Pod Deployment must declare both `livenessProbe` and `readinessProbe`.
   - Probes must target `HTTP GET /api/health` on port 8000.
   - Configure reasonable thresholds (`initialDelaySeconds: 5`, `periodSeconds: 10`, `failureThreshold: 3`).
4. **Resource Guarantees & Limits:**
   - Every container must define explicit `resources.requests` and `resources.limits` for both `cpu` and `memory`.
   - Never run pods without memory limits to avoid host-level node Out-Of-Memory (OOM) kills.
5. **Zero-Downtime Deployment Strategy:**
   - Use `RollingUpdate` with `maxSurge: 1` and `maxUnavailable: 0` to ensure at least 100% replica availability during rollouts.
6. **Label Standardization:**
   - Standard labels must be applied to all resources:
     ```yaml
     labels:
       app.kubernetes.io/name: devops-monitored-app
       app.kubernetes.io/instance: production
       app.kubernetes.io/version: "1.0.0"
       app.kubernetes.io/component: backend
       app.kubernetes.io/part-of: devops-observability-platform
     ```
7. **Secrets and Configuration Separation:**
   - Non-sensitive variables must reside in `ConfigMap`.
   - Sensitive tokens (registry keys, alert webhooks) must reside in `Secret` or be injected via environment variables at deploy time.

---

## 5. CI/CD Standards

1. **Fail-Fast Pipelines:** Pipelines must execute fast checks first (syntax linting, unit tests) before launching resource-intensive stages (Docker build, vulnerability scanning).
2. **Security Quality Gate:**
   - Run Trivy on built Docker images.
   - If a `CRITICAL` vulnerability is discovered, fail the pipeline build immediately.
3. **Immutable Image Tagging:**
   - Images must be tagged with the Git commit short SHA (e.g., `myregistry/monitored-app:sha-a1b2c3d`) and semantic version (e.g., `v1.0.0`).
   - Never deploy using the untracked `latest` tag in production pipelines.
4. **Automated Rollback Guard:**
   - The deployment pipeline must assert the health of the newly deployed pods via HTTP GET to `/api/health`.
   - If the endpoint fails within the health probe window (e.g. 60 seconds), execute `kubectl rollout undo deployment/devops-monitored-app` and register a pipeline failure.
5. **No Bypassing Tests:** Never comment out tests, add `|| true` to suppress test failures, or skip Trivy scans to make a broken pipeline appear green.

---

## 6. Project Constraints & Prohibitions

To ensure project stability, efficiency, and adherence to requirements, AI agents must adhere to the following prohibitions:

1. **NO Total Rewrites:** Never delete or rewrite entire components or configurations to fix an isolated issue. Pinpoint and patch specific root causes.
2. **NO Cloud Cost Incurrence:** Do not introduce cloud-managed services (AWS CloudWatch, Datadog, Google Cloud Logging, AWS EKS) unless explicitly instructed. Keep infrastructure self-hosted on local/standard Kubernetes and Docker.
3. **NO Unnecessary Microservices:** Do not decompose the project into unrequested services (e.g., separate auth microservice, worker queue, cache cluster) when the monolithic FastAPI microservice satisfies all requirements.
4. **NO Hardcoded Credentials:** Never store plain-text passwords, tokens, or webhook URLs in code, Dockerfiles, or git-tracked YAML manifests.
5. **NO Unvalidated Completions:** Never set a task status to "Completed" in `memory.md` or `Task.md` without running explicit test commands and observing their passing output.
6. **NO Unannounced Architecture Shifts:** Do not swap core technologies (e.g. replacing FastAPI with Flask/Node.js, or Prometheus with InfluxDB, or Grafana with Kibana) without explicit user authorization.
7. **NO Breaking Changes Without Rollback Path:** Every deployment and infrastructure modification must have a verified rollback mechanism.
