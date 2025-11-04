# UCBLLogger Enhanced EKS Deployment Best Practices

This guide provides best practices for deploying the Enhanced UCBLLogger in production EKS environments.

## Table of Contents

1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Resource Planning](#resource-planning)
3. [Security Best Practices](#security-best-practices)
4. [Performance Optimization](#performance-optimization)
5. [Monitoring and Alerting](#monitoring-and-alerting)
6. [Disaster Recovery](#disaster-recovery)
7. [Troubleshooting](#troubleshooting)
8. [Maintenance](#maintenance)

## Pre-Deployment Checklist

### Infrastructure Requirements

- [ ] **EKS Cluster Version**: Kubernetes 1.21+ recommended
- [ ] **Node Groups**: Sufficient capacity for logging overhead (10-20% additional resources)
- [ ] **Storage Classes**: Fast SSD storage for log buffers
- [ ] **Network Policies**: Configured for secure communication
- [ ] **Load Balancers**: Application Load Balancer for health checks

### AWS Services Setup

- [ ] **CloudWatch Logs**: Log groups created with appropriate retention
- [ ] **IAM Roles**: IRSA configured for CloudWatch access
- [ ] **VPC Configuration**: Proper subnet and security group setup
- [ ] **Route53**: DNS configuration for health check endpoints

### Kubernetes Configuration

- [ ] **RBAC**: Service accounts and cluster roles configured
- [ ] **Pod Security Standards**: Appropriate security policies applied
- [ ] **Resource Quotas**: Namespace quotas configured
- [ ] **Network Policies**: Traffic restrictions in place

## Resource Planning

### CPU and Memory Requirements

#### Base Requirements (per pod)

| Component | CPU Request | CPU Limit | Memory Request | Memory Limit |
|-----------|-------------|-----------|----------------|--------------|
| Basic Logger | 100m | 500m | 256Mi | 1Gi |
| Enhanced Logger | 200m | 1000m | 512Mi | 2Gi |
| High Volume | 500m | 2000m | 1Gi | 4Gi |

#### Scaling Factors

```yaml
# Example resource configuration
resources:
  requests:
    cpu: 200m
    memory: 512Mi
    ephemeral-storage: 1Gi
  limits:
    cpu: 1000m
    memory: 2Gi
    ephemeral-storage: 5Gi
```

### Storage Requirements

#### Temporary Storage

```yaml
volumes:
- name: log-buffer
  emptyDir:
    sizeLimit: 2Gi
- name: tmp
  emptyDir:
    sizeLimit: 1Gi
```

#### Persistent Storage (if needed)

```yaml
volumeClaimTemplates:
- metadata:
    name: log-storage
  spec:
    accessModes: ["ReadWriteOnce"]
    storageClassName: "gp3"
    resources:
      requests:
        storage: 10Gi
```

### Network Requirements

#### Bandwidth Planning

- **Internal Traffic**: 10-50 Mbps per pod for Kubernetes API calls
- **External Traffic**: 100-500 Mbps per pod for CloudWatch delivery
- **Health Checks**: Minimal bandwidth (<1 Mbps)

#### Port Configuration

```yaml
ports:
- name: http
  containerPort: 8000
  protocol: TCP
- name: health
  containerPort: 8080
  protocol: TCP
- name: metrics
  containerPort: 9090
  protocol: TCP
```

## Security Best Practices

### Container Security

#### Security Context

```yaml
securityContext:
  runAsNonRoot: true
  runAsUser: 1000
  runAsGroup: 1000
  fsGroup: 1000
  allowPrivilegeEscalation: false
  readOnlyRootFilesystem: true
  capabilities:
    drop:
    - ALL
  seccompProfile:
    type: RuntimeDefault
```

#### Image Security

```dockerfile
# Use minimal base images
FROM python:3.11-slim

# Create non-root user
RUN groupadd -r ucbllogger && useradd -r -g ucbllogger ucbllogger

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY --chown=ucbllogger:ucbllogger . /app
WORKDIR /app

# Switch to non-root user
USER ucbllogger

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1

EXPOSE 8000 8080 9090
CMD ["python", "main.py"]
```

### Network Security

#### Network Policies

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: ucbl-logger-network-policy
spec:
  podSelector:
    matchLabels:
      app: my-application
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: monitoring
    ports:
    - protocol: TCP
      port: 9090
  egress:
  - to: []
    ports:
    - protocol: TCP
      port: 443  # HTTPS to AWS
    - protocol: UDP
      port: 53   # DNS
```

### Data Security

#### Sensitive Data Redaction

```python
# Configure comprehensive redaction patterns
security_config = SecurityConfig(
    enable_data_redaction=True,
    redaction_patterns=[
        # PII patterns
        r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
        
        # Financial patterns
        r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',  # Credit cards
        
        # Security patterns
        r'\b[A-Za-z0-9]{32,}\b',  # API keys
        r'Bearer\s+[A-Za-z0-9\-._~+/]+=*',  # Bearer tokens
        
        # Custom patterns for your application
        r'password["\s]*[:=]["\s]*[^"\s]+',  # Passwords
        r'secret["\s]*[:=]["\s]*[^"\s]+',    # Secrets
    ],
    audit_redactions=True
)
```

### IAM Security

#### Minimal IAM Policy

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": [
        "arn:aws:logs:*:*:log-group:/aws/eks/my-application:*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:DescribeLogGroups",
        "logs:DescribeLogStreams"
      ],
      "Resource": [
        "arn:aws:logs:*:*:log-group:/aws/eks/my-application"
      ]
    }
  ]
}
```

## Performance Optimization

### Application-Level Optimization

#### Async Processing

```python
# Enable async processing for high-throughput scenarios
logger = EnhancedEKSLogger(
    service_name="my-application",
    async_processing=True,
    worker_threads=4,
    queue_size=10000
)
```

#### Batch Processing

```python
# Optimize CloudWatch batching
cloudwatch_config = CloudWatchConfig(
    batch_size=1000,
    max_batch_wait_time=30,
    enable_compression=True,
    compression_level=6
)
```

#### Memory Management

```python
# Configure memory-efficient buffering
buffer_config = BufferConfig(
    max_size=50000,
    flush_interval=10,
    memory_threshold=0.8,  # Flush when 80% of memory limit reached
    enable_compression=True
)
```

### Kubernetes-Level Optimization

#### Pod Disruption Budgets

```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: my-application-pdb
spec:
  minAvailable: 2
  selector:
    matchLabels:
      app: my-application
```

#### Horizontal Pod Autoscaler

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: my-application-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: my-application
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  - type: Pods
    pods:
      metric:
        name: ucbl_logger_buffer_usage_percent
      target:
        type: AverageValue
        averageValue: "60"
```

#### Vertical Pod Autoscaler

```yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: my-application-vpa
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: my-application
  updatePolicy:
    updateMode: "Auto"
  resourcePolicy:
    containerPolicies:
    - containerName: my-application
      maxAllowed:
        cpu: 4000m
        memory: 8Gi
      minAllowed:
        cpu: 200m
        memory: 512Mi
```

### Node-Level Optimization

#### Node Affinity

```yaml
affinity:
  nodeAffinity:
    preferredDuringSchedulingIgnoredDuringExecution:
    - weight: 100
      preference:
        matchExpressions:
        - key: node-type
          operator: In
          values:
          - compute-optimized
    - weight: 50
      preference:
        matchExpressions:
        - key: kubernetes.io/arch
          operator: In
          values:
          - amd64
```

#### Taints and Tolerations

```yaml
# For dedicated logging nodes
tolerations:
- key: "logging-dedicated"
  operator: "Equal"
  value: "true"
  effect: "NoSchedule"
```

## Monitoring and Alerting

### Essential Metrics

#### Application Metrics

```yaml
# Key metrics to monitor
- ucbl_logger_logs_total
- ucbl_logger_buffer_usage_percent
- ucbl_logger_sampling_rate
- ucbl_logger_cloudwatch_error_rate
- ucbl_logger_health_check_success_rate
```

#### Infrastructure Metrics

```yaml
# Kubernetes metrics
- container_cpu_usage_seconds_total
- container_memory_working_set_bytes
- container_network_receive_bytes_total
- container_network_transmit_bytes_total
```

### Alerting Rules

#### Critical Alerts

```yaml
groups:
- name: ucbl_logger_critical
  rules:
  - alert: UCBLLoggerDown
    expr: up{job="ucbl-logger"} == 0
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "UCBLLogger instance is down"
      
  - alert: UCBLLoggerBufferOverflow
    expr: ucbl_logger_buffer_usage_percent > 95
    for: 2m
    labels:
      severity: critical
    annotations:
      summary: "UCBLLogger buffer near overflow"
```

#### Warning Alerts

```yaml
- alert: UCBLLoggerHighLatency
  expr: ucbl_logger_cloudwatch_delivery_latency_seconds > 30
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "UCBLLogger CloudWatch delivery latency high"
```

### Dashboards

#### Grafana Dashboard Structure

1. **Overview Panel**: Service health, log volume, error rates
2. **Performance Panel**: CPU, memory, network usage
3. **Buffer Panel**: Buffer usage, flush rates, failures
4. **CloudWatch Panel**: Delivery rates, errors, latency
5. **Sampling Panel**: Sampling rates, efficiency metrics
6. **Security Panel**: Redaction events, security alerts

## Disaster Recovery

### Backup Strategies

#### Configuration Backup

```bash
#!/bin/bash
# Backup Kubernetes configurations
kubectl get configmap ucbl-logger-config -o yaml > backup/configmap.yaml
kubectl get secret ucbl-logger-secrets -o yaml > backup/secrets.yaml
kubectl get deployment my-application -o yaml > backup/deployment.yaml
```

#### Log Buffer Backup

```python
# Implement buffer persistence for critical logs
buffer_config = BufferConfig(
    enable_persistence=True,
    persistence_path="/var/log/ucbl-buffer",
    backup_interval=300,  # 5 minutes
    max_backup_files=10
)
```

### Failover Procedures

#### Multi-Region Setup

```yaml
# Primary region deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-application-primary
  labels:
    region: us-west-2
    role: primary

---
# Secondary region deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-application-secondary
  labels:
    region: us-east-1
    role: secondary
```

#### Circuit Breaker Configuration

```python
# Configure circuit breaker for CloudWatch failures
cloudwatch_config = CloudWatchConfig(
    circuit_breaker_enabled=True,
    failure_threshold=10,
    recovery_timeout=300,
    fallback_handler="local_file"
)
```

### Recovery Procedures

#### Automated Recovery

```yaml
# Kubernetes Job for log recovery
apiVersion: batch/v1
kind: Job
metadata:
  name: ucbl-logger-recovery
spec:
  template:
    spec:
      containers:
      - name: recovery
        image: ucbl-logger:latest
        command: ["python", "recovery.py"]
        env:
        - name: RECOVERY_MODE
          value: "true"
        - name: BACKUP_PATH
          value: "/var/log/backup"
```

## Troubleshooting

### Common Issues

#### High Memory Usage

**Symptoms:**
- OOMKilled pods
- High memory metrics

**Solutions:**
```python
# Reduce buffer size
buffer_config = BufferConfig(
    max_size=5000,
    flush_interval=2,
    memory_threshold=0.7
)

# Enable compression
sampling_config = SamplingConfig(
    enabled=True,
    default_rate=0.05
)
```

#### CloudWatch Rate Limiting

**Symptoms:**
- Rate limit errors in logs
- Delayed log delivery

**Solutions:**
```python
# Optimize batching
cloudwatch_config = CloudWatchConfig(
    batch_size=500,
    max_batch_wait_time=60,
    enable_compression=True,
    retry_backoff_multiplier=1.5
)
```

#### Performance Degradation

**Symptoms:**
- High CPU usage
- Slow response times

**Solutions:**
```python
# Reduce monitoring frequency
performance_config = PerformanceThresholds(
    collection_interval=300,
    enable_detailed_metrics=False
)

# Enable async processing
logger = EnhancedEKSLogger(
    async_processing=True,
    worker_threads=2
)
```

### Debugging Tools

#### Debug Mode

```python
# Enable debug mode for troubleshooting
logger = EnhancedEKSLogger(
    service_name="debug-service",
    debug_mode=True,
    log_level=logging.DEBUG
)
```

#### Health Check Endpoint

```bash
# Check logger health
kubectl exec <pod-name> -- curl localhost:8080/health

# Get detailed metrics
kubectl exec <pod-name> -- curl localhost:9090/metrics
```

#### Log Analysis

```bash
# Analyze log patterns
kubectl logs <pod-name> | grep "ERROR" | tail -20

# Check buffer statistics
kubectl logs <pod-name> | grep "buffer_stats"

# Monitor sampling efficiency
kubectl logs <pod-name> | grep "sampling_efficiency"
```

## Maintenance

### Regular Maintenance Tasks

#### Weekly Tasks

- [ ] Review log volume trends
- [ ] Check buffer usage patterns
- [ ] Validate CloudWatch delivery rates
- [ ] Review security alerts
- [ ] Update configuration if needed

#### Monthly Tasks

- [ ] Review and update resource limits
- [ ] Analyze performance trends
- [ ] Update security patterns
- [ ] Review and rotate secrets
- [ ] Update monitoring dashboards

#### Quarterly Tasks

- [ ] Review and update IAM policies
- [ ] Conduct disaster recovery testing
- [ ] Update documentation
- [ ] Review and update alerting rules
- [ ] Performance optimization review

### Upgrade Procedures

#### Rolling Updates

```yaml
strategy:
  type: RollingUpdate
  rollingUpdate:
    maxSurge: 1
    maxUnavailable: 0
```

#### Blue-Green Deployment

```bash
#!/bin/bash
# Blue-green deployment script
kubectl apply -f deployment-green.yaml
kubectl wait --for=condition=available deployment/my-application-green
kubectl patch service my-application -p '{"spec":{"selector":{"version":"green"}}}'
kubectl delete deployment my-application-blue
```

### Configuration Management

#### GitOps Workflow

```yaml
# ArgoCD Application
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: ucbl-logger
spec:
  source:
    repoURL: https://github.com/your-org/ucbl-logger-config
    path: kubernetes/
    targetRevision: HEAD
  destination:
    server: https://kubernetes.default.svc
    namespace: production
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

This deployment guide provides comprehensive best practices for running the Enhanced UCBLLogger in production EKS environments with high availability, security, and performance.