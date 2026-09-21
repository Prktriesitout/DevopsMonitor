# Observability UI/UX Design System

## Project: DevOps Monitoring & Observability Dashboard

---

## 1. Design Philosophy & Principles

The DevOps Monitoring Dashboard follows the aesthetic and functional standards of modern high-tier observability platforms (such as Grafana Enterprise, Datadog, and New Relic). The interface is engineered for SREs and DevOps engineers who require immediate situational awareness, rapid incident triage, and zero cognitive friction under high-pressure troubleshooting conditions.

### Core Principles
1. **Information Density Without Cognitive Overload:** Maximize usable screen real estate with compact KPI tiles, concise sparklines, and structured tables while maintaining generous breathing room (8px grid spacing).
2. **Instant Visual Scanning (3-Second Rule):** An operator looking at the screen for 3 seconds must immediately discern whether the system is healthy, degraded, or failing.
3. **Multi-Attribute Status Indication:** Never communicate system health through color alone. Every status element combines a distinct color, an unambiguous icon, and explicit text (e.g., `● Healthy`, `▲ Warning`, `✖ Critical`).
4. **Dark-Mode-First Observability:** A high-contrast dark theme reduces visual fatigue during long on-call rotations and provides crisp contrast for glowing time-series curves and status indicators.
5. **Monospaced Precision for Telemetry:** Numbers, timestamps, metrics, IP addresses, and log streams must use precision monospaced typography to prevent visual jitter during live updates.

---

## 2. Color Palette & Token System

The design system uses a curated, WCAG AA compliant dark-mode palette tailored for operational telemetry.

| Token | Hex Value | Role & Usage Description |
| :--- | :--- | :--- |
| `--bg-canvas` | `#0B0E14` | Deep background canvas behind all panels and views. |
| `--bg-surface` | `#151B26` | Card background for metric panels, charts, and table containers. |
| `--bg-surface-elevated`| `#1D2636` | Hover states, dropdown menus, modal dialogs, and active cards. |
| `--border-subtle` | `#232D3F` | Outer panel borders, divider lines, and table row separators. |
| `--border-focus` | `#3B82F6` | Active input focus ring, selected panel highlight, active tabs. |
| `--text-primary` | `#F1F5F9` | High-emphasis headings, main KPI values, and primary labels. |
| `--text-secondary` | `#94A3B8` | Body text, panel subtitles, axis labels, and inactive tabs. |
| `--text-muted` | `#64748B` | Timestamp footnotes, helper annotations, placeholder text. |
| `--color-primary` | `#3B82F6` | Brand accent, active navigation items, standard metric lines. |
| `--color-success` | `#10B981` | Healthy system status, 2xx HTTP traffic, active replicas. |
| `--color-warning` | `#F59E0B` | Elevated latency, warnings (4xx HTTP codes), memory near threshold. |
| `--color-critical` | `#EF4444` | High 5xx error rate (>5%), service outage, pod crash-loop. |
| `--color-info` | `#06B6D4` | System notifications, informational log lines, deployment updates. |
| `--color-offline` | `#475569` | Dormant pods, stopped services, unmonitored endpoints. |
| `--color-deploying` | `#8B5CF6` | Ongoing rolling updates, pod initialization, image pulling. |

---

## 3. Typography & Hierarchy

The interface leverages two complementary typography families: `Inter` for interface structure and `JetBrains Mono` / `Roboto Mono` for numbers, logs, and telemetry data.

| Usage | Font Family | Size | Weight | Line Height | Letter Spacing |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Page / Section Title** | Inter | 20px (`1.25rem`) | 600 (SemiBold) | 28px | -0.01em |
| **Panel Header** | Inter | 14px (`0.875rem`)| 600 (SemiBold) | 20px | 0.00em |
| **KPI Headline Value** | Roboto Mono | 32px (`2.00rem`) | 700 (Bold) | 36px | -0.02em |
| **KPI Sub-metric / Delta**| Roboto Mono | 12px (`0.75rem`) | 500 (Medium) | 16px | 0.00em |
| **Body & Labels** | Inter | 13px (`0.8125rem`)| 400 (Regular) | 18px | 0.00em |
| **Chart Axis & Legends** | Inter | 11px (`0.6875rem`)| 500 (Medium) | 14px | 0.01em |
| **Log Stream & Trace** | JetBrains Mono| 12px (`0.75rem`) | 400 (Regular) | 18px | 0.00em |
| **Badges & Micro-tags** | Inter | 11px (`0.6875rem`)| 600 (SemiBold) | 14px | 0.02em (UPPER) |

---

## 4. UI Components & Visual Specification

### 4.1 Global Top Navigation & Breadcrumbs
- **Height:** 48px, sticky top with `backdrop-filter: blur(8px)`.
- **Elements:**
  - Left: System logo (`⚡ DevOps Monitor`), Active Environment selector (`production`, `staging`), Refresh Interval dropdown (`5s`, `15s`, `1m`, `Manual`).
  - Center: Global Time Range Picker (default: `Last 1 Hour`, quick selects for `15m`, `6h`, `24h`).
  - Right: Alert bell counter badge (`FIRING: 0`), Cluster Health indicator (`● All 3 Pods Ready`), User profile / Docs link.

### 4.2 KPI Metric Cards (Panel 1)
- **Container:** Rounded 8px card (`--bg-surface`), border `1px solid --border-subtle`, internal padding 16px.
- **Card Content Structure:**
  - *Title:* Small uppercase caption (`TOTAL REQUEST RATE`, `--text-secondary`).
  - *Primary Value:* Large bold monospaced number (`42.5 req/s`, `--text-primary`).
  - *Trend Sparkline / Indicator:* Delta comparison (`▲ +4.2% vs last hr`, green if positive, red if error rate).
- **The 4 Primary KPI Cards:**
  1. **Total Request Rate:** Current throughput (`42.5 req/sec`).
  2. **Average Response Time:** Service latency (`24 ms`).
  3. **Error Rate (5xx):** Percentage of failed requests (`0.8 %`). Color turns red if > 5.0%.
  4. **Active Pod Count:** Replicas running (`3 / 3 Replicas Healthy`).

### 4.3 Time-Series Chart Panels (Panel 2)
- **Chart Type:** Dual-axis smoothed line chart with semi-transparent area gradients.
- **Left Y-Axis:** Requests Per Second (RPS) split by status:
  - `HTTP 200 (Success)`: Emerald Green (`#10B981`) line with 10% fill.
  - `HTTP 500 (Server Error)`: Bright Crimson Red (`#EF4444`) line with 25% fill.
- **Right Y-Axis:** Request Latency in milliseconds:
  - `p50 Latency`: Blue (`#3B82F6`) dashed line.
  - `p95 Latency`: Amber (`#F59E0B`) solid line.
  - `p99 Latency`: Purple (`#8B5CF6`) dotted line.
- **Interaction:** Synchronized hover crosshair displaying exact timestamp, status codes, and latency breakdown in a floating dark tooltip.

### 4.4 Kubernetes Resource Utilization Gauges (Panel 3)
- **CPU & Memory Radial Gauges:**
  - Arc meter displaying current utilization against Kubernetes resource requests and limits.
  - Display format: `CPU: 18% (90m / 500m)` and `Memory: 240MiB / 512MiB (47%)`.
  - Color thresholds:
    - `0% - 69%`: Emerald Green (`#10B981`)
    - `70% - 84%`: Amber Warning (`#F59E0B`)
    - `85% - 100%`: Crimson Critical (`#EF4444`)
- **Pod Status & Restart Counter:**
  - Grid showing each individual pod replica name (`devops-monitored-app-6f89b9d4f4-5s9lm`), status badge (`RUNNING`), uptime, and restart count (`0 Restarts`).

### 4.5 Live Application Log Stream Panel (Panel 4)
- **Query Bar:** Pre-populated LogQL search bar with syntax highlighting:
  `{app="devops-monitored-app"} |= "ERROR"`
- **Log Stream Viewer:**
  - Terminal-inspired console box (`--bg-canvas`) with auto-scroll toggle and search filter.
  - Color-coded log level badges:
    - `[INFO]`: Subtle cyan (`#06B6D4`)
    - `[WARNING]`: Amber (`#F59E0B`)
    - `[ERROR]`: Crimson red (`#EF4444`) with expandable stack trace drawer.
  - Format: `TIMESTAMP | LEVEL | LOGGER | MESSAGE | DETAILS (method, status, duration)`.

### 4.6 Alertmanager Banner & Notification Cards
- When an alert is actively firing, a non-intrusive sticky alert banner slides in at the top of the dashboard:
  - Icon: Pulsing crimson exclamation triangle (`⚠`).
  - Text: `HighHTTPErrorRate — HTTP 5xx error rate is 8.4% over 2 minutes (threshold: >5%)`.
  - Action buttons: `[Acknowledge]`, `[Silence 15m]`, `[View Logs]`.

---

## 5. Dashboard Grid Layout & Information Hierarchy

The main operational screen is organized into a 12-column responsive layout:

```text
+---------------------------------------------------------------------------------------------------+
| Top Navigation: Brand | Environment: [Production ▼] | Range: [Last 1h ▼] | Status: [3/3 Pods OK]  |
+---------------------------------------------------------------------------------------------------+
| [Alert Banner - Displays only when firing: HighHTTPErrorRate in default namespace]                |
+---------------------------------------------------------------------------------------------------+
| PANEL 1: KPI OVERVIEW BAR (4 Columns x 1 Row)                                                     |
| +---------------------+ +---------------------+ +---------------------+ +---------------------+ |
| | Total Request Rate  | | Avg Response Time   | | Error Rate (5xx)    | | Active Pods         | |
| | 42.5 req/sec        | | 24 ms               | | 0.8 % (Normal)      | | 3 Replicas (100%)   | |
| +---------------------+ +---------------------+ +---------------------+ +---------------------+ |
+---------------------------------------------------------------------------------------------------+
| PANEL 2: HTTP TRAFFIC & LATENCY TRENDS (12 Columns x 2 Rows)                                      |
| +-----------------------------------------------------------------------------------------------+ |
| | Left Y: Request Throughput (200 OK vs 500 Error)       Right Y: Latency (p50, p95, p99 ms)    | |
| | [ Time-series graph past 1 hour with crosshair inspection ]                                   | |
| +-----------------------------------------------------------------------------------------------+ |
+---------------------------------------------------------------------------------------------------+
| PANEL 3: K8S RESOURCE UTILIZATION (6 Cols)    | PANEL 4: REAL-TIME LOG STREAM (6 Cols)             |
| +-------------------------------------------+ | +-----------------------------------------------+ |
| | CPU Utilization:    [=======   ] 18%      | | | LogQL: {app="devops-monitored-app"} |= "ERROR"| |
| | Memory Utilization: [============] 47%    | | | 21:40:15 [ERROR] Internal Server Error 500    | |
| | Pod Replicas:                             | | | 21:38:02 [WARN]  High latency on /checkout    | |
| | - pod-5s9lm: Running (0 restarts, 4h)     | | | 21:35:10 [INFO]  Metrics scraped successfully | |
| | - pod-9k2xz: Running (0 restarts, 4h)     | | | [ Auto-scroll: ON ] [ Pause ] [ Clear ]       | |
| +-------------------------------------------+ | +-----------------------------------------------+ |
+---------------------------------------------------------------------------------------------------+
```

---

## 6. Status Representation Matrix

To prevent ambiguity, every operational state combines 3 distinct visual indicators:

| State | Visual Badge & Text | Icon | Accent Color | Border & Glow | Condition Criteria |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Healthy** | `● Healthy` | Checkmark (`✓`) | `#10B981` | None / subtle | All probes 200, error rate < 1%, latency < 100ms. |
| **Warning** | `▲ Warning` | Triangle (`⚠`) | `#F59E0B` | Subtle amber glow | Error rate 1% - 5%, latency 100ms - 500ms, CPU > 75%. |
| **Critical** | `✖ Critical` | Octagon (`⛔`) | `#EF4444` | Pulsing red border | Error rate > 5%, pod crash-looping, health probe failure. |
| **Deploying**| `↻ Deploying`| Spinner (`⟳`) | `#8B5CF6` | Soft violet border | Rolling update in progress, waiting for readiness probe. |
| **Offline** | `○ Offline` | Minus (`-`) | `#475569` | Gray border | Pod terminated, replica count 0, service stopped. |
| **Unknown** | `? Unknown` | Question (`?`) | `#94A3B8` | Dashed gray border | Prometheus scrape timeout, network unreachable. |
