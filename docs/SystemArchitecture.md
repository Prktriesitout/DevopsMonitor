# System Architecture Document

## Project: DevOps Monitoring & Observability Dashboard

---

## 1. High-Level Architecture

The DevOps Monitoring & Observability platform is architected around the decoupled microservices and cloud-native observability pattern. The system consists of the application workload, a monitoring and logging telemetry pipeline, automated alerting, a unified dashboard visualization layer, and dual-pipeline CI/CD automation.

### Architecture Diagram

```mermaid
flowchart TD
    subgraph Developer_and_VCS ["Source Control & CI/CD"]
        DEV["Developer"] -->|git push| GH["GitHub Repository"]
        GH -->|Webhook Trigger| GHA["GitHub Actions CI Pipeline\n(Lint, Test, Docker Build, Trivy Scan)"]
        GH -->|Webhook Trigger| JNK["Jenkins CD Pipeline\n(K8s Deploy, Health Probe, Auto-Rollback)"]
        GHA -->|Push Image| CR["Container Registry\n(Docker Hub / GHCR)"]
        CR -->|Pull Image| K8S_CLUSTER
    end

    subgraph K8S_CLUSTER ["Kubernetes Cluster"]
        subgraph NS_DEFAULT ["Namespace: default"]
            APP1["FastAPI Pod 1\n(:8000)"]
            APP2["FastAPI Pod 2\n(:8000)"]
            APP3["FastAPI Pod 3\n(:8000)"]
            SVC_APP["ClusterIP Service\n(devops-monitored-app-service:8000)"]
            APP1 --- SVC_APP
            APP2 --- SVC_APP
            APP3 --- SVC_APP
        end

        subgraph NS_MONITORING ["Namespace: monitoring"]
            PROM["Prometheus Server\n(:9090)"]
            LOKI["Grafana Loki\n(:3100)"]
            AM["Prometheus Alertmanager\n(:9093)"]
            GRAF["Grafana Dashboard\n(:3000)"]
            FB["Fluent Bit DaemonSet\n(Log Collector)"]
        end

        %% Telemetry and Communication flows
        SVC_APP -->|HTTP Pull /metrics (15s)| PROM
        APP1 -.->|stdout/stderr JSON| FB
        APP2 -.->|stdout/stderr JSON| FB
        APP3 -.->|stdout/stderr JSON| FB
        FB -->|HTTP Push Logs| LOKI

        PROM -->|Evaluate Rules| AM
        AM -->|Webhook / Alert JSON| NOTIF["Alert Webhook / Slack / Email"]

        PROM -->|PromQL Telemetry| GRAF
        LOKI -->|LogQL Stream Query| GRAF
    end

    USER["DevOps Operator / SRE"] -->|HTTP :3000| GRAF
    USER -->|HTTP Request| SVC_APP
```

---

## 2. Technology Stack & Component Responsibilities

| Technology | Layer / Responsibility | Why It Is Selected | Component / Path |
| :--- | :--- | :--- | :--- |
| **Git / GitHub** | Version Control & Source of Truth | Industry standard for declarative infrastructure, version tracking, branch protection, and event triggers. | Root repository |
| **Bash** | Automation & Scripting | Portable shell scripting for pipeline steps, health probe checks, and local environment bootstrapping. | `scripts/*.sh` |
| **Python 3.11** | Application Runtime | High performance, lightweight runtime with rich ecosystem for web APIs and async workloads. | `src/` |
| **FastAPI & Uvicorn** | Web Framework & ASGI Server | Asynchronous, high-throughput microservice framework with native OpenAPI doc generation and fast request handling. | `src/main.py` |
| **Prometheus FastAPI Instrumentator** | Telemetry Instrumentation | Automatically tracks HTTP request count, latencies, status codes, and system metrics in OpenMetrics format without manual boilerplate. | `src/main.py` |
| **Docker** | Container Engine & Packaging | Multi-stage container builds ensuring minimal footprint, reproducible builds, and isolated dependencies. | `Dockerfile`, `docker-compose.yml` |
| **Trivy** | Vulnerability Scanner | Fast container security scanner to detect CVEs in OS packages and Python dependencies prior to deployment. | CI Pipeline stage |
| **Kubernetes (k8s)** | Container Orchestration | Declarative scheduling, zero-downtime rolling updates, automated self-healing, service discovery, and scaling. | `k8s/` |
| **Prometheus** | Metrics Engine & TSDB | Standard time-series database optimized for high scrape frequency, multi-dimensional metric labels, and PromQL. | `monitoring` namespace |
| **Grafana Loki** | Log Aggregation Engine | Horizontally scalable, multi-tenant log aggregation system designed to index metadata labels rather than full text, keeping it cost-efficient. | `monitoring` namespace |
| **Fluent Bit** | Log Forwarding Agent | Extremely lightweight C-based log processor and forwarder, reading node container logs and shipping structured JSON to Loki. | `monitoring` namespace |
| **Alertmanager** | Alert Routing & Deduplication | Handles alert deduplication, grouping, silence windows, and webhook routing to external notification endpoints. | `monitoring` namespace |
| **Grafana** | Unified Observability UI | Visualizes real-time metrics and log streams side-by-side in custom operational dashboards. | Port 3000 |
| **GitHub Actions** | CI Automation | Native repository integration, ephemeral runners, automated linting, test execution, and container building on PRs. | `.github/workflows/deploy.yml` |
| **Jenkins** | CD & Deployment Orchestrator | Enterprise deployment controller managing Kubernetes rollouts, post-deploy health validation, and automated rollback guards. | `jenkins/Jenkinsfile` |

---

## 3. Service Architecture & Communication

### 3.1 Application Service (`src/main.py`)
- **Protocol:** HTTP/1.1 REST API over port `8000`.
- **Endpoints:**
  - `GET /api/health`: Synthetic health probe returning `{ "status": "healthy", "timestamp": "<ISO-8601>" }`. Used by Kubernetes `livenessProbe` and `readinessProbe`.
  - `GET /api/data`: Sample operational endpoint returning simulated data payloads and tracking request latency histograms.
  - `GET /api/simulate-error`: Chaos endpoint intentionally returning HTTP 500 (`"Simulated Database Timeout"`) with traceback for verifying error logging and alert rules.
  - `GET /metrics`: Standard OpenMetrics formatted scrape target exposing request rates, status codes, request durations, and Python runtime metrics.
- **Logging:** Structured JSON logs streamed to standard output (`stdout`) and error output (`stderr`).

### 3.2 Metrics Collector (Prometheus)
- **Scrape Strategy:** Pull-based HTTP scraping targeting `devops-monitored-app-service:8000/metrics` every 15 seconds.
- **Kubernetes Integration:** Prometheus discovers pods dynamically using Kubernetes Service discovery (`ServiceMonitor` custom resource or pod annotations).
- **Rule Engine:** Evaluates alerting rules (`HighHTTPErrorRate`, `AppPodDown`, `HighLatencyDetected`) every 15 seconds.

### 3.3 Log Service (Loki & Fluent Bit)
- **Collection Mechanism:** Fluent Bit runs as a DaemonSet with read access to `/var/log/containers/*.log` on each node.
- **Parsing:** Parses the application's structured JSON log fields (`level`, `status_code`, `method`, `duration_ms`, `traceback`).
- **Storage:** Ships formatted log batches via HTTP POST to Loki (`http://loki:3100/loki/api/v1/push`).
- **Query Interface:** Exposes LogQL API over HTTP port 3100 to Grafana.

### 3.4 Alert Service (Prometheus Alertmanager)
- **Input:** Receives firing alert states from Prometheus via HTTP POST on port 9093.
- **Processing:** Groups alerts by alertname and namespace, suppresses flapping alerts, and evaluates silence windows.
- **Notification Outlets:** Dispatches webhook payloads to configured endpoints (Slack, Discord, custom webhook HTTP listener).

### 3.5 Dashboard Service (Grafana)
- **Datasources:** Configured with Prometheus (`http://prometheus:9090`) and Loki (`http://loki:3100`).
- **Dashboards:** Provisioned automatically via declarative JSON configurations, eliminating manual dashboard setup.
- **Access:** Exposed via NodePort or Port-Forwarding on HTTP port 3000.

---

## 4. End-to-End Data Flows

### 4.1 Application Request & Metrics Data Flow
1. Client sends an HTTP request (`GET /api/data`) to `devops-monitored-app-service:8000`.
2. Kubernetes Service routes the request to an available pod replica (`devops-monitored-app`).
3. The `prometheus-fastapi-instrumentator` middleware intercepts the request:
   - Increments `http_requests_total{handler="/api/data",method="GET",status="200"}`.
   - Observes execution duration in `http_request_duration_seconds_bucket`.
4. FastAPI returns response payload `200 OK`.
5. Every 15 seconds, Prometheus scrapes `/metrics` and updates its internal time-series database.

### 4.2 Application Logging Data Flow
1. Application processes a request or triggers an unhandled exception (`GET /api/simulate-error`).
2. Structured JSON logger formats the event:
   ```json
   {"timestamp":"2026-09-20T21:40:15.891Z","level":"ERROR","logger":"app.main","message":"Internal Server Error triggered","method":"GET","url":"/api/simulate-error","status_code":500,"traceback":"..."}
   ```
3. Docker container runtime captures the JSON stream and writes it to `/var/log/pods/...`.
4. Fluent Bit tail plugin reads the log line, adds Kubernetes pod labels (`app=devops-monitored-app`), and forwards it to Loki.
5. Operators querying Grafana with LogQL `{app="devops-monitored-app"} |= "ERROR"` see the log entry in real time.

### 4.3 Alert Generation & Dispatch Flow
1. Users or automated chaos tests generate repeated 500 errors via `/api/simulate-error`.
2. Prometheus calculates the 5xx rate over a 2-minute sliding window:
   `sum(rate(http_requests_total{status="500"}[2m])) / sum(rate(http_requests_total[2m])) * 100 > 5`
3. If condition persists for > 1 minute, the alert state shifts from `PENDING` to `FIRING`.
4. Prometheus pushes the firing alert payload to Alertmanager.
5. Alertmanager evaluates grouping and dispatches an HTTP POST alert notification to the configured webhook channel.

### 4.4 Dashboard Query Data Flow
1. SRE opens the Grafana Dashboard in browser (`http://localhost:3000`).
2. Grafana executes dual queries:
   - PromQL query to Prometheus for Request Rate, Latency percentiles, and Error Rate.
   - LogQL query to Loki for live error logs matching `{app="devops-monitored-app"}`.
3. Renders the 4 operational panels with sub-second dashboard auto-refresh (5s interval).

### 4.5 Deployment & Automated Rollback Flow
1. Pipeline executes `kubectl apply -f k8s/deployment.yaml`.
2. Kubernetes initiates a RollingUpdate: spins up new pods, runs readiness checks against `/api/health`.
3. Pipeline executes a health validation guard script:
   - Loops 10 times with 3-second delay calling `http://<app-service-ip>/api/health`.
   - If all checks return HTTP 200, deployment is marked **SUCCESS**.
   - If checks time out or return non-200, the pipeline immediately runs `kubectl rollout undo deployment/devops-monitored-app` and fails the pipeline with **ROLLBACK TRIGGERED**.

---

## 5. CI/CD Architecture & Pipeline Division

To maintain clean separation of concerns without duplicating responsibilities:

```
+-------------------------------------------------------------------------------+
|                       GITHUB ACTIONS (Continuous Integration)                 |
|                                                                               |
|  [Pull Request / Push to main]                                                |
|           │                                                                   |
|           ▼                                                                   |
|  Stage 1: Code Quality & Linting (flake8, black check)                        |
|           │                                                                   |
|           ▼                                                                   |
|  Stage 2: Automated Unit & Endpoint Tests (pytest, test coverage)             |
|           │                                                                   |
|           ▼                                                                   |
|  Stage 3: Multi-Stage Docker Image Build (pinned python:3.11-slim)            |
|           │                                                                   |
|           ▼                                                                   |
|  Stage 4: Container Security Scanning (Trivy scan for HIGH/CRITICAL CVEs)     |
|           │                                                                   |
|           ▼                                                                   |
|  Stage 5: Publish Container Image to Registry with Git SHA and SemVer tags     |
+---------------------------------------+---------------------------------------+
                                        │
                                        ▼ Triggers Deployment
+-------------------------------------------------------------------------------+
|                         JENKINS (Continuous Deployment)                       |
|                                                                               |
|  Stage 1: Fetch Immutable Artifact Tag (from Registry)                        |
|           │                                                                   |
|           ▼                                                                   |
|  Stage 2: Apply Kubernetes Manifests (k8s/deployment.yaml, k8s/service.yaml)  |
|           │                                                                   |
|           ▼                                                                   |
|  Stage 3: Monitor Rollout Status (kubectl rollout status deployment)          |
|           │                                                                   |
|           ▼                                                                   |
|  Stage 4: Synthetic Health Verification Guard (curl /api/health in loop)      |
|           │                                                                   |
|           ├── Success ──► Stage 5: Notify Deployment Succeeded (Slack/Webhook)|
|           │                                                                   |
|           └── Failure ──► Stage 5: Trigger Rollback Guard                     |
|                                    (kubectl rollout undo deployment)          |
|                                    Notify Deployment Failed & Rolled Back     |
+-------------------------------------------------------------------------------+
```

---

## 6. Kubernetes Architecture

### 6.1 Namespaces
- `default`: Hosts application microservices (`devops-monitored-app`).
- `monitoring`: Hosts observability infrastructure (`prometheus`, `alertmanager`, `loki`, `fluent-bit`, `grafana`).

### 6.2 Workloads & Manifests
- **Deployment (`devops-monitored-app`):**
  - Replicas: `3`
  - Strategy: `RollingUpdate` with `maxSurge: 1`, `maxUnavailable: 0` (zero downtime).
  - Pod spec includes security context (`runAsNonRoot: true`), explicit resource requests and limits.
- **Service (`devops-monitored-app-service`):**
  - Type: `ClusterIP`
  - Port: `8000`, TargetPort: `8000`
- **ConfigMap (`devops-app-config`):**
  - Key-value configurations: `PORT: "8000"`, `LOG_LEVEL: "INFO"`, `ENVIRONMENT: "production"`.
- **Health Probes:**
  - `readinessProbe`: `httpGet: { path: /api/health, port: 8000 }`, `initialDelaySeconds: 5`, `periodSeconds: 10`.
  - `livenessProbe`: `httpGet: { path: /api/health, port: 8000 }`, `initialDelaySeconds: 10`, `periodSeconds: 15`.
- **Resource Limits & Requests:**
  - Requests: `cpu: 100m`, `memory: 128Mi`
  - Limits: `cpu: 500m`, `memory: 512Mi`
- **Scaling Strategy (HPA):**
  - Target CPU utilization: `70%`.
  - Min replicas: `2`, Max replicas: `6`.
- **Persistent Storage:**
  - PersistentVolumeClaims (PVC) for Prometheus TSDB storage and Loki chunk directory.

---

## 7. Intended Repository Directory Structure

```text
devops-project1/
├── .github/
│   └── workflows/
│       └── deploy.yml               # GitHub Actions CI pipeline specification
├── jenkins/
│   └── Jenkinsfile                  # Jenkins Declarative CD pipeline specification
├── k8s/
│   ├── namespace.yaml               # Cluster namespace definitions (monitoring, default)
│   ├── deployment.yaml              # Application Deployment manifest (3 replicas)
│   ├── service.yaml                 # Application ClusterIP Service manifest
│   ├── configmap.yaml               # Application environment configuration
│   ├── hpa.yaml                     # Horizontal Pod Autoscaler manifest
│   ├── servicemonitor.yaml          # Prometheus Operator ServiceMonitor resource
│   └── prometheus-rules.yaml        # Alertmanager alert rules specification
├── src/
│   ├── __init__.py
│   ├── main.py                      # FastAPI application with Prometheus & structlog
│   ├── config.py                    # Application environment configuration loader
│   ├── requirements.txt             # Locked Python application dependencies
│   └── tests/
│       ├── __init__.py
│       ├── test_main.py             # Endpoint tests (/health, /data, /simulate-error)
│       └── test_metrics.py          # Metrics exposition validation tests
├── docker/
│   ├── prometheus/
│   │   ├── prometheus.yml           # Prometheus scrape configuration
│   │   └── alert_rules.yml          # Standalone Prometheus alert rules
│   ├── alertmanager/
│   │   └── alertmanager.yml         # Alertmanager notification routing configuration
│   ├── loki/
│   │   └── loki-config.yaml         # Grafana Loki storage and retention configuration
│   ├── fluent-bit/
│   │   └── fluent-bit.conf          # Fluent Bit log ingestion and Loki output config
│   └── grafana/
│       ├── provisioning/
│       │   ├── datasources/
│       │   │   └── datasources.yaml # Automated datasource provisioning (Prometheus, Loki)
│       │   └── dashboards/
│       │       └── dashboards.yaml  # Automated dashboard provider configuration
│       └── dashboards/
│           └── devops-dashboard.json # Exported unified Grafana dashboard JSON
├── scripts/
│   ├── health_check.sh              # Synthetic health probe & automated rollback guard
│   ├── simulate_traffic.sh          # Traffic generator for load & error simulation
│   └── setup_local.sh               # Local environment bootstrap script
├── docs/
│   ├── PRD.md                       # Product Requirements Document
│   ├── SystemArchitecture.md        # System Architecture & Technical Specifications
│   ├── Rulebook.md                  # Engineering Standards & Agent Constraints
│   ├── Design.md                    # Observability UI/UX Design System
│   ├── Task.md                      # Phased Implementation Roadmap
│   └── memory.md                    # Persistent AI State & Memory Register
├── Dockerfile                       # Multi-stage production container build file
├── .dockerignore                    # Build context exclusions
├── docker-compose.yml               # Local standalone observability & app stack
└── README.md                        # Master repository documentation
```
