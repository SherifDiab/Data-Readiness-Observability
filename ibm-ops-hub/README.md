# IBM Ops Hub

A full-stack unified monitoring dashboard for IBM platform components. Consolidates operational status of five IBM services into a single real-time view.

## Monitored Components

| Component | Technology | Data Source |
|-----------|-----------|-------------|
| **Spark Jobs** | IBM Cloud Pak for Data | CPD Jobs API |
| **DataStage Jobs** | IBM DataStage | CPD Jobs API or IIS REST API |
| **Event Processing Flows** | IBM Event Processing (Flink) | Kubernetes FlinkDeployment CRDs |
| **Flink Jobs** | Apache Flink (standalone) | Flink REST API (:8081) |
| **API Connect Logs** | IBM API Connect | APIC Analytics REST API |

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Browser                              │
│  React 18 + TypeScript + Tailwind CSS (dark mode ops UI)   │
│  TanStack Query (cache) + WebSocket (real-time updates)     │
└──────────────┬──────────────────────────────────────────────┘
               │  HTTP REST + WebSocket
┌──────────────▼──────────────────────────────────────────────┐
│                 FastAPI Backend (:8000)                      │
│  APScheduler polls IBM APIs every 15-60s                    │
│  Results cached in Redis, history in PostgreSQL             │
│  WebSocket broadcasts updates to all browser clients        │
└───────┬──────────────────┬────────────────────────┬─────────┘
        │                  │                        │
   ┌────▼────┐        ┌────▼────┐            ┌─────▼────┐
   │  Redis  │        │Postgres │            │ IBM APIs  │
   │ (cache) │        │(history)│            │ CPD/APIC  │
   └─────────┘        └─────────┘            │ Flink/K8s │
                                             └──────────┘
```

## Quick Start

### Development (with mock IBM APIs)

```bash
# Clone and setup
cp .env.example .env
# (no need to fill in real IBM credentials for mock mode)

# Set MOCK_MODE=True in .env
echo "MOCK_MODE=True" >> .env

# Start everything including mock server
docker compose --profile mock up

# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
# Mock Server: http://localhost:9000
```

### Production (real IBM services)

```bash
cp .env.example .env
# Fill in your IBM credentials in .env

docker compose up -d
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `CPD_BASE_URL` | Yes | Cloud Pak for Data base URL |
| `CPD_USERNAME` | Yes | CPD admin username |
| `CPD_PASSWORD` | Yes | CPD admin password |
| `CPD_PROJECT_ID` | Yes | Default project to monitor |
| `FLINK_REST_URL` | Yes | Flink JobManager REST URL (port 8081) |
| `APIC_MGMT_URL` | Yes | APIC management server URL |
| `APIC_ANALYTICS_URL` | Yes | APIC analytics server URL |
| `APIC_ORG` | Yes | APIC provider org name |
| `APIC_CATALOG` | Yes | APIC catalog name |
| `APIC_USERNAME` | Yes | APIC admin username |
| `APIC_PASSWORD` | Yes | APIC admin password |
| `K8S_IN_CLUSTER` | No | `True` if running inside K8s cluster (default: True) |
| `K8S_KUBECONFIG` | No | Path to kubeconfig (if not in-cluster) |
| `K8S_NAMESPACE` | No | K8s namespace for Event Processing (default: event-automation) |
| `DATASTAGE_USE_CPD` | No | Use CPD API for DataStage (default: True) |
| `REDIS_URL` | No | Redis connection URL (default: redis://redis:6379/0) |
| `DATABASE_URL` | No | PostgreSQL async URL (default: postgresql+asyncpg://...) |
| `MOCK_MODE` | No | Use mock server instead of real IBM APIs (default: False) |
| `MOCK_SERVER_URL` | No | Mock server base URL (default: http://mock-server:9000) |

## API Endpoints

```
GET  /api/dashboard/summary         → Aggregated health of all 5 components
GET  /api/dashboard/health          → Component-level up/down status

GET  /api/spark/jobs                → List Spark job statuses
GET  /api/spark/jobs/{id}           → Single Spark job

GET  /api/datastage/jobs            → List DataStage job statuses
GET  /api/datastage/jobs/{id}       → Single DataStage job

GET  /api/event-processing/flows    → List Event Processing flows
GET  /api/event-processing/flows/{id}

GET  /api/flink/jobs                → List Flink job statuses
GET  /api/flink/cluster             → Flink cluster overview (slots, TMs)
GET  /api/flink/jobs/{jid}

GET  /api/apic/logs                 → Recent API call logs (filterable)
GET  /api/apic/summary              → APIC metrics summary

GET  /api/settings                  → Current configuration (non-sensitive)
POST /api/settings/refresh/{component} → Force immediate re-poll

WS   /ws                            → WebSocket for real-time updates
```

## Running Tests

```bash
cd backend
pip install pytest pytest-asyncio
pytest tests/ -v
```

## Project Structure

```
ibm-ops-hub/
├── backend/          # FastAPI + APScheduler + SQLAlchemy
│   ├── app/
│   │   ├── services/ # IBM API pollers (one per component)
│   │   ├── routers/  # REST API endpoints
│   │   └── polling/  # Background scheduler
│   └── tests/        # Unit tests with fixtures
├── frontend/         # React + TypeScript + Tailwind
│   └── src/
│       ├── components/ # UI components by feature
│       ├── hooks/      # TanStack Query + WebSocket hooks
│       └── services/   # Axios API client
└── mock-server/      # FastAPI mock of all IBM APIs
```
