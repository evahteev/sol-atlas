# System Requirements

System requirements and prerequisites for deploying SOL Atlas.

---

## Minimum Requirements

### Minimal Setup (Light Integration)

**Use Cases:**
- Community bots
- Lightweight AI chat widgets
- Basic onboarding flows

**Components:**
- `bot-app`
- `webchatbot-app`
- `engine-api`
- `flowapi-api`
- `warehouse-api`
- Redis
- PostgreSQL (via PgBouncer)
- Elasticsearch

**Resource Requirements:**
- **CPU:** 4 cores minimum
- **Memory:** 8GB minimum
- **Storage:** 50GB minimum
- **Network:** 100Mbps

**Kubernetes:**
- **Version:** 1.24+ (or compatible)
- **Nodes:** 2 nodes minimum
- **Namespace:** 1 namespace per application

---

## Production Requirements

### Enterprise / Full Deployment

**Use Cases:**
- Production deployments with high traffic
- Advanced analytics and event processing
- Complex workflows with async processing

**Additional Components:**
- ClickHouse
- RabbitMQ
- Workers (multiple types)

**Resource Requirements:**
- **CPU:** 16 cores minimum
- **Memory:** 32GB minimum
- **Storage:** 500GB minimum (SSD recommended)
- **Network:** 1Gbps

**Kubernetes:**
- **Version:** 1.24+ (or compatible)
- **Nodes:** 5+ nodes recommended
- **Namespace:** 1 namespace per application
- **HA Setup:** Recommended for stateful components

---

## Component-Specific Requirements

### Stateless Services

**bot-app:**
- **CPU:** 0.5 cores per instance
- **Memory:** 512MB per instance
- **Replicas:** 2+ for HA

**webchatbot-app:**
- **CPU:** 0.25 cores per instance
- **Memory:** 256MB per instance
- **Replicas:** 2+ for HA

**engine-api:**
- **CPU:** 1 core per instance
- **Memory:** 1GB per instance
- **Replicas:** 2+ for HA

**flowapi-api:**
- **CPU:** 0.5 cores per instance
- **Memory:** 512MB per instance
- **Replicas:** 2+ for HA

**warehouse-api:**
- **CPU:** 0.5 cores per instance
- **Memory:** 512MB per instance
- **Replicas:** 2+ for HA

**Workers:**
- **CPU:** 1 core per instance (varies by type)
- **Memory:** 1GB per instance (varies by type)
- **Replicas:** 2+ for HA

### Stateful Services

**PostgreSQL:**
- **CPU:** 2 cores minimum, 4 cores recommended
- **Memory:** 4GB minimum, 8GB recommended
- **Storage:** 100GB minimum (SSD recommended)
- **HA:** Primary + 2 replicas recommended

**ClickHouse:**
- **CPU:** 4 cores minimum, 8 cores recommended
- **Memory:** 8GB minimum, 16GB recommended
- **Storage:** 200GB minimum (SSD recommended)
- **HA:** 3 replicas, 2 shards recommended

**Redis:**
- **CPU:** 1 core minimum, 2 cores recommended
- **Memory:** 2GB minimum, 4GB recommended
- **Storage:** 10GB minimum (ephemeral)
- **HA:** Sentinel mode (3 nodes) or Cluster mode

**RabbitMQ:**
- **CPU:** 1 core minimum, 2 cores recommended
- **Memory:** 2GB minimum, 4GB recommended
- **Storage:** 20GB minimum
- **HA:** 3 nodes with quorum queues

**Elasticsearch:**
- **CPU:** 2 cores minimum, 4 cores recommended
- **Memory:** 4GB minimum, 8GB recommended
- **Storage:** 100GB minimum (SSD recommended)
- **HA:** 3 nodes minimum

---

## Software Prerequisites

### Kubernetes

- **Version:** 1.24+ (or compatible)
- **CNI:** Calico, Flannel, or compatible
- **Storage:** CSI-compatible storage (for StatefulSets)
- **Ingress:** NGINX Ingress Controller or compatible

### Container Runtime

- **Docker:** 20.10+ (or compatible)
- **containerd:** 1.6+ (or compatible)

### Tools

- **kubectl:** 1.24+ (or compatible)
- **helm:** 3.8+ (optional, for package management)

---

## Network Requirements

### Internal Communication

- **Service Mesh:** Internal-only communication between services
- **DNS:** Kubernetes DNS (CoreDNS) for service discovery
- **Ports:**
  - PostgreSQL: 5432 (internal only)
  - Redis: 6379 (internal only)
  - RabbitMQ: 5672, 15672 (internal only)
  - Elasticsearch: 9200, 9300 (internal only)
  - ClickHouse: 8123, 9000 (internal only)

### External Access

- **Ingress:** HTTP/HTTPS (80, 443) for webchatbot and admin UI
- **Telegram Bot API:** Outbound HTTPS (443) to Telegram servers
- **WebSocket:** For warehouse-api real-time events

---

## Storage Requirements

### Persistent Volumes

- **PostgreSQL:** 100GB+ (SSD recommended)
- **ClickHouse:** 200GB+ (SSD recommended)
- **Elasticsearch:** 100GB+ (SSD recommended)
- **RabbitMQ:** 20GB+ (standard storage)

### Storage Classes

- **Fast SSD:** For databases and Elasticsearch
- **Standard:** For RabbitMQ and backups

---

## Security Requirements

### Authentication

- **JWT:** For service-to-service authentication
- **Kubernetes Secrets:** For credential storage
- **Vault:** Optional, for enterprise secret management

### Network Security

- **Network Policies:** Restrict inter-pod communication
- **Service Mesh:** Internal-only communication
- **TLS:** For external-facing services (HTTPS)

### Access Control

- **RBAC:** Kubernetes role-based access control
- **Namespace Isolation:** Each application in its own namespace

---

## Monitoring Requirements

### Metrics

- **Prometheus:** For metrics collection
- **Grafana:** For dashboards and visualization

### Logging

- **Centralized Logging:** ELK stack, Loki, or compatible
- **Log Retention:** 30 days minimum

### Alerting

- **Alertmanager:** For alert routing
- **PagerDuty / Slack:** For notifications

---

## Backup Requirements

### Database Backups

- **PostgreSQL:** pgBackRest, daily backups
- **ClickHouse:** Daily backups
- **Elasticsearch:** ES snapshots, weekly backups

### Configuration Backups

- **Kubernetes ConfigMaps:** Version controlled
- **Secrets:** Encrypted backups
- **RabbitMQ Definitions:** Regular backups

---

## Performance Requirements

### Latency

- **API Response Time:** < 200ms (p95)
- **RAG Query Time:** < 500ms (p95)
- **WebSocket Latency:** < 100ms

### Throughput

- **Messages per Second:** 100+ (per bot instance)
- **Concurrent Users:** 1000+ (per deployment)
- **RAG Queries per Second:** 50+ (per Elasticsearch cluster)

---

## Scalability Requirements

### Horizontal Scaling

- **Stateless Services:** Auto-scale based on CPU/memory
- **HPA:** Configured for all stateless deployments

### Vertical Scaling

- **Stateful Services:** Manual scaling or scheduled scaling
- **Database:** Scale based on query performance

---

## Development Requirements

### Local Development

- **Docker:** 20.10+
- **Docker Compose:** 2.0+
- **Python:** 3.9+ (for bot-app)
- **Node.js:** 18+ (for webchatbot-app, flowapi-api)
- **Java:** 17+ (for engine-api)

### Tools

- **Git:** 2.30+
- **kubectl:** 1.24+
- **helm:** 3.8+ (optional)

---

## Next Steps

- Read the [Architecture Overview](architecture.md) for system design
- Check the [Components Guide](components.md) for component details
- Learn about the [Launcher Wizard](launcher-wizard.md) for automated deployment

