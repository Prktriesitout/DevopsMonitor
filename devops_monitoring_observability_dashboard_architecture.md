# DevOps Monitoring & Observability Platform

A end-to-end, production-grade DevOps monitoring and CI/CD platform. This project demonstrates containerized microservice deployment on Kubernetes managed via automated pipelines (Jenkins & GitHub Actions), fully instrumented with Prometheus, Grafana, Loki, and Alertmanager for real-time operational visibility.

## 1. System Architecture Overview

```
                                    +-----------------------+
                                    |   GitHub Repository   |
                                    +-----------+-----------+
                                                |
                                      (Trigger Webhook / Push)
                                                v
                                 +--------------+--------------+
                                 |  CI/CD Pipelines           |
                                 |  (Jenkins / GitHub Actions)|
                                 +--------------+--------------+
                                                |
                                        (Build & Push Image)
                                                v
                                    +-----------+-----------+
                                    |  Docker Registry      |
                                    +-----------+-----------+
                                                |
                                            (Deploy)
                                                v
+---------------------------------------------------------------------------------------------------+
| Kubernetes Cluster                                                                                |
|                                                                                                   |
|  [ default Namespace ]                                                                            |
|  +---------------------------------------------------------------------------------------------+  |
|  |  Python FastAPI Microservice Pods (Replicas: 3)                                              |  |
|  |  - /api/health  - /api/data  - /api/simulate-error  - /metrics                                 |  |
|  +------------------------------+--------------------------------------------------------------+  |
|                                 |                                 |                               |
|                                 | (Scrape Metrics)                | (Collect Stdout/Stderr Logs)  |
|                                 v                                 v                               |
|  [ monitoring Namespace ]                                                                         |
|  +------------------------------+----+                       +----+----------------------------+  |
|  | Prometheus                        |                       | Grafana Loki / Fluent Bit       |  |
|  | (Time-Series Metrics Database)    |                       | (Log Aggregation Service)       |  |
|  +--------------+--------------------+                       +--------------+------------------+  |
|                 |                                                           |                     |
|                 | (Alert Rules Evaluated)                                   | (Query Logs)        |
|                 v                                                           v                     |
|  +--------------+--------------------+                       +--------------+------------------+  |
|  | Alertmanager                      |                       | Grafana Visual Dashboards        |  |
|  | (Routes Notifications)            |                       | (Metrics + Logs Single Pane)     |  |
|  +--------------+--------------------+                       +---------------------------------+  |
|                 |                                                                                 |
+-----------------|---------------------------------------------------------------------------------+
                  |
                  v
       +--------------------+
       | Slack / Email /    |
       | Webhook Alert      |
       +--------------------+

```

## 2. Tech Stack Breakdown

* **Application:** Python FastAPI REST API (Instrumented with `prometheus-fastapi-instrumentator` & Python `structlog`/standard JSON logger running under Uvicorn).

* **Containerization:** Docker (Multi-stage builds with Python slim runtime for minimal image size).

* **Orchestration:** Kubernetes (Deployments, ClusterIP Services, ConfigMaps, Horizontal Pod Autoscaler).

* **CI/CD:** Jenkins & GitHub Actions (Automated linting, building, scanning, deployment, and rollback).

* **Metrics Engine:** Prometheus & Node Exporter.

* **Log Engine:** Grafana Loki & Fluent Bit.

* **Alerting Engine:** Prometheus Alertmanager.

* **Visualization:** Grafana (Customized Dashboards).

## 3. Expected Terminal & API Outputs

### 3.1 Kubernetes Cluster Status Output

When checking the status of all deployed workloads using `kubectl`, your terminal output will look like this:

```
$ kubectl get pods -n monitoring
NAME                                                     READY   STATUS    RESTARTS   AGE
kube-prometheus-stack-grafana-76bf4749f9-x2k4p           1/1     Running   0          2d
kube-prometheus-stack-operator-6d5f78c85c-l8qzw          1/1     Running   0          2d
prometheus-kube-prometheus-stack-prometheus-0            2/2     Running   0          2d
alertmanager-kube-prometheus-stack-alertmanager-0       2/2     Running   0          2d
loki-0                                                   1/1     Running   0          2d
fluent-bit-4x9zq                                         1/1     Running   0          2d

$ kubectl get pods -n default
NAME                                                     READY   STATUS    RESTARTS   AGE
devops-monitored-app-6f89b9d4f4-5s9lm                   1/1     Running   0          4h
devops-monitored-app-6f89b9d4f4-9k2xz                   1/1     Running   0          4h
devops-monitored-app-6f89b9d4f4-r7m8p                   1/1     Running   0          4h

```

### 3.2 Prometheus `/metrics` API Output

When calling `http://<app-service-ip>/metrics`, the FastAPI application exposes OpenMetrics formatted metrics generated via `prometheus-fastapi-instrumentator`:

```
# HELP http_requests_total Total number of HTTP requests processed
# TYPE http_requests_total counter
http_requests_total{handler="/api/data",method="GET",status="200"} 1420
http_requests_total{handler="/api/simulate-error",method="GET",status="500"} 38

# HELP http_request_duration_seconds HTTP request duration in seconds
# TYPE http_request_duration_seconds histogram
http_request_duration_seconds_bucket{le="0.05",handler="/api/data",method="GET"} 1100
http_request_duration_seconds_bucket{le="0.1",handler="/api/data",method="GET"} 1380
http_request_duration_seconds_bucket{le="+Inf",handler="/api/data",method="GET"} 1420
http_request_duration_seconds_sum{handler="/api/data",method="GET"} 42.15
http_request_duration_seconds_count{handler="/api/data",method="GET"} 1420

# HELP process_cpu_seconds_total Total user and system CPU time spent in seconds
# TYPE process_cpu_seconds_total counter
process_cpu_seconds_total 12.48

# HELP python_gc_objects_collected_total Objects collected by GC
# TYPE python_gc_objects_collected_total counter
python_gc_objects_collected_total{generation="0"} 14250

```

### 3.3 Python Application Log Format (Structured JSON Output)

Application logs generated via Python structured logging are output to standard stdout/stderr for Loki collection:

```
{"timestamp":"2026-09-20T21:40:12.102Z","level":"INFO","logger":"app.main","message":"HTTP Request processed","method":"GET","url":"/api/data","status_code":200,"duration_ms":12.4}
{"timestamp":"2026-09-20T21:40:15.891Z","level":"ERROR","logger":"app.main","message":"Internal Server Error triggered","method":"GET","url":"/api/simulate-error","status_code":500,"traceback":"Traceback (most recent call last):\n  File \"/app/main.py\", line 45, in simulate_error\n    raise HTTPException(status_code=500, detail=\"Simulated Database Timeout\")"}

```

## 4. Expected Visual Dashboard Displays (Grafana)

Your Grafana Web UI (`http://localhost:3000`) will feature a main **Unified DevOps Operational Dashboard** divided into four panel sections:

### Panel 1: Key Performance Indicators (KPI Overview Bar)

```
+------------------------+ +------------------------+ +------------------------+ +------------------------+
| Total Request Rate     | | Average Response Time  | | Error Rate (5xx)       | | Active Pod Count       |
| 42.5 req/sec           | | 24 ms                  | | 0.8 %                  | | 3 Replicas (Healthy)   |
+------------------------+ +------------------------+ +------------------------+ +------------------------+

```

### Panel 2: HTTP Traffic & Latency Trends (Time-Series Graph)

* **X-Axis:** Time (Past 1 Hour)

* **Y-Axis (Left):** Requests Per Second (RPS) split by HTTP status code (`200 OK` in Green, `500 Error` in Red).

* **Y-Axis (Right):** Latency distribution (`p50`, `p95`, `p99` percentiles in milliseconds).

### Panel 3: Kubernetes Resource Utilization

* **CPU Usage Gauge:** Displays cluster memory & CPU percentage against requests/limits (e.g., `CPU: 18% | Memory: 240MiB / 512MiB`).

* **Pod Restart Counter:** Counter displaying individual pod crash loops or restarts.

### Panel 4: Real-time Application Log Stream (Loki Query Panel)

Query: `{app="devops-monitored-app"} |= "ERROR"`

```
2026-09-20 21:40:15.891 [ERROR] app.main: Internal Server Error triggered | method=GET url=/api/simulate-error status_code=500
2026-09-20 21:38:02.112 [WARNING] app.main: High latency detected on endpoint | method=POST url=/api/checkout duration_ms=480.2

```

## 5. Expected Alertmanager Notification Output

When an anomaly occurs (e.g., Error rate exceeds 5% for more than 2 minutes), Alertmanager triggers a webhook alert formatted as follows:

```
{
  "receiver": "slack-notifications",
  "status": "firing",
  "alerts": [
    {
      "status": "firing",
      "labels": {
        "alertname": "HighHTTPErrorRate",
        "severity": "critical",
        "service": "devops-monitored-app",
        "namespace": "default"
      },
      "annotations": {
        "summary": "High 5xx HTTP error rate detected",
        "description": "HTTP 5xx error rate is currently at 8.4% over the last 2 minutes (threshold: >5%)."
      },
      "startsAt": "2026-09-20T21:42:00.000Z"
    }
  ]
}

```

## 6. Expected CI/CD Pipeline Console Output

During an automated GitHub Actions or Jenkins deployment, the pipeline stage log output looks like this:

```
[INFO] Starting Pipeline Execution for Commit #a1b2c3d...
[STAGE 1/5] Linting & Unit Testing (flake8 & pytest) .. PASSED (8s)
[STAGE 2/5] Building Docker Image ..................... PASSED (14s)
            Successfully tagged: myregistry/monitored-app:v1.2.0
[STAGE 3/5] Security Vulnerability Scan (Trivy) ...... PASSED (5s)
            Found 0 Critical / 0 High vulnerabilities.
[STAGE 4/5] Deploying to Kubernetes Cluster .......... PASSED (9s)
            deployment.apps/devops-monitored-app configured
            service/devops-monitored-app-service unchanged
[STAGE 5/5] Health Check & Automated Rollback Guard .. PASSED (12s)
            HTTP GET http://devops-monitored-app/api/health -> 200 OK
[SUCCESS] Pipeline Completed Successfully in 48s.

```

## 7. Directory Structure Preview

```
.
├── .github/
│   └── workflows/
│       └── deploy.yml          # GitHub Actions CI/CD Pipeline
├── jenkins/
│   └── Jenkinsfile             # Jenkins Pipeline Script
├── k8s/
│   ├── deployment.yaml         # Kubernetes Deployment Spec
│   ├── service.yaml            # Kubernetes Service Spec
│   ├── servicemonitor.yaml     # Prometheus Service Monitor Spec
│   └── prometheus-rules.yaml   # Prometheus Alert Rules Spec
├── src/
│   ├── main.py                 # FastAPI App with Prometheus instrumentator & JSON logging
│   ├── requirements.txt        # Python dependencies (fastapi, uvicorn, prometheus-fastapi-instrumentator)
│   └── tests/
│       └── test_main.py        # Pytest test cases
├── Dockerfile                  # Multi-stage Python Dockerfile
├── docker-compose.yml          # Local testing setup
└── README.md                   # System Documentation

```