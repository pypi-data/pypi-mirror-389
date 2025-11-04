# UCBLLogger Enhanced EKS Troubleshooting Guide

This guide provides comprehensive troubleshooting procedures for common issues with the Enhanced UCBLLogger in EKS environments.

## Table of Contents

1. [Quick Diagnostics](#quick-diagnostics)
2. [Common Issues](#common-issues)
3. [Performance Issues](#performance-issues)
4. [CloudWatch Issues](#cloudwatch-issues)
5. [Kubernetes Integration Issues](#kubernetes-integration-issues)
6. [Security Issues](#security-issues)
7. [Monitoring Issues](#monitoring-issues)
8. [Debug Tools](#debug-tools)
9. [Log Analysis](#log-analysis)
10. [Recovery Procedures](#recovery-procedures)

## Quick Diagnostics

### Health Check Commands

```bash
# Check pod status
kubectl get pods -l app=my-application

# Check pod health
kubectl exec <pod-name> -- curl -f localhost:8080/health

# Check metrics endpoint
kubectl exec <pod-name> -- curl localhost:9090/metrics | grep ucbl_logger

# Check recent logs
kubectl logs <pod-name> --tail=50

# Check events
kubectl get events --sort-by=.metadata.creationTimestamp
```

### Quick Status Script

```bash
#!/bin/bash
# quick-status.sh - Quick health check script

POD_NAME=$(kubectl get pods -l app=my-application -o jsonpath='{.items[0].metadata.name}')

echo "=== Pod Status ==="
kubectl get pod $POD_NAME

echo "=== Health Check ==="
kubectl exec $POD_NAME -- curl -s localhost:8080/health | jq .

echo "=== Resource Usage ==="
kubectl top pod $POD_NAME

echo "=== Recent Errors ==="
kubectl logs $POD_NAME --tail=20 | grep -i error

echo "=== Buffer Status ==="
kubectl logs $POD_NAME --tail=100 | grep "buffer_usage" | tail -5
```

## Common Issues

### 1. Logger Not Starting

#### Symptoms
- Pod in CrashLoopBackOff state
- Container exits immediately
- Import errors in logs

#### Diagnosis
```bash
# Check pod status and events
kubectl describe pod <pod-name>

# Check container logs
kubectl logs <pod-name> --previous

# Check configuration
kubectl get configmap ucbl-logger-config -o yaml
```

#### Common Causes and Solutions

**Missing Dependencies**
```dockerfile
# Ensure all dependencies are installed
FROM python:3.11-slim
RUN pip install ucbl-logger[eks] psutil kubernetes boto3
```

**Configuration Errors**
```python
# Validate configuration
from ucbl_logger.enhanced.config import validate_config

try:
    config = load_config_from_env()
    validation_result = validate_config(config)
    if not validation_result.is_valid:
        logger.error(f"Invalid configuration: {validation_result.errors}")
except Exception as e:
    logger.error(f"Configuration error: {e}")
```

**Permission Issues**
```yaml
# Check security context
securityContext:
  runAsNonRoot: true
  runAsUser: 1000
  allowPrivilegeEscalation: false
```

### 2. High Memory Usage / OOMKilled

#### Symptoms
- Pods getting OOMKilled
- High memory usage in metrics
- Slow performance

#### Diagnosis
```bash
# Check memory usage
kubectl top pod <pod-name>

# Check memory limits
kubectl describe pod <pod-name> | grep -A 5 "Limits"

# Check buffer usage
kubectl logs <pod-name> | grep "buffer_usage_percent"
```

#### Solutions

**Reduce Buffer Size**
```python
buffer_config = BufferConfig(
    max_size=5000,  # Reduce from default 10000
    flush_interval=2,  # Flush more frequently
    memory_threshold=0.7  # Flush at 70% memory usage
)
```

**Enable Aggressive Sampling**
```python
sampling_config = SamplingConfig(
    enabled=True,
    default_rate=0.05,  # Very aggressive sampling
    volume_threshold=100,  # Lower threshold
    preserve_errors=True
)
```

**Increase Memory Limits**
```yaml
resources:
  limits:
    memory: 4Gi  # Increase from 2Gi
  requests:
    memory: 1Gi  # Increase from 512Mi
```

### 3. Logger Not Collecting Kubernetes Metadata

#### Symptoms
- Missing pod/node information in logs
- Kubernetes API errors
- Empty metadata fields

#### Diagnosis
```bash
# Check RBAC permissions
kubectl auth can-i get pods --as=system:serviceaccount:default:ucbl-logger-service-account

# Check service account
kubectl get serviceaccount ucbl-logger-service-account

# Check if running in Kubernetes
kubectl exec <pod-name> -- ls /var/run/secrets/kubernetes.io/serviceaccount/

# Test Kubernetes API access
kubectl exec <pod-name> -- curl -H "Authorization: Bearer $(cat /var/run/secrets/kubernetes.io/serviceaccount/token)" \
  https://kubernetes.default.svc/api/v1/namespaces/default/pods
```

#### Solutions

**Fix RBAC Permissions**
```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: ucbl-logger-cluster-role
rules:
- apiGroups: [""]
  resources: ["pods", "nodes", "services"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["apps"]
  resources: ["deployments", "replicasets"]
  verbs: ["get", "list", "watch"]
```

**Verify Service Account Mounting**
```yaml
spec:
  serviceAccountName: ucbl-logger-service-account
  automountServiceAccountToken: true
```

**Manual Metadata Configuration**
```python
# Fallback to manual configuration
logger = EnhancedEKSLogger(
    service_name=os.getenv('SERVICE_NAME'),
    namespace=os.getenv('NAMESPACE'),
    pod_name=os.getenv('POD_NAME'),
    node_name=os.getenv('NODE_NAME'),
    enable_k8s_metadata=False  # Disable auto-detection
)
```

### 4. Distributed Tracing Not Working

#### Symptoms
- Missing correlation IDs
- Broken trace chains
- No trace propagation

#### Diagnosis
```bash
# Check trace generation
kubectl logs <pod-name> | grep "correlation_id"

# Check HTTP headers
kubectl logs <pod-name> | grep "X-Correlation-ID"

# Check OpenTelemetry integration
kubectl logs <pod-name> | grep "opentelemetry"
```

#### Solutions

**Manual Correlation ID Handling**
```python
# Extract from request headers
correlation_id = request.headers.get('X-Correlation-ID')
if not correlation_id:
    correlation_id = logger.start_trace("manual_operation")

logger.info("Processing request", correlation_id=correlation_id)

# Propagate to downstream services
headers = {'X-Correlation-ID': correlation_id}
response = requests.get(url, headers=headers)
```

**Configure Header Propagation**
```python
tracing_config = TracingConfig(
    enabled=True,
    header_names=['X-Correlation-ID', 'X-Trace-ID', 'X-Request-ID'],
    generate_if_missing=True
)
```

**Debug Trace Context**
```python
# Enable trace debugging
logger = EnhancedEKSLogger(
    enable_tracing=True,
    trace_debug=True,  # Log trace operations
    log_level=logging.DEBUG
)
```

## Performance Issues

### 1. High CPU Usage

#### Symptoms
- CPU usage consistently above 80%
- Slow response times
- Performance alerts firing

#### Diagnosis
```bash
# Check CPU usage
kubectl top pod <pod-name>

# Check performance metrics
kubectl exec <pod-name> -- curl localhost:9090/metrics | grep cpu

# Profile application
kubectl exec <pod-name> -- python -m cProfile -o profile.stats main.py
```

#### Solutions

**Reduce Monitoring Frequency**
```python
performance_config = PerformanceThresholds(
    collection_interval=300,  # Collect every 5 minutes instead of 1
    enable_detailed_metrics=False
)
```

**Enable Async Processing**
```python
logger = EnhancedEKSLogger(
    async_processing=True,
    worker_threads=2,  # Adjust based on CPU cores
    queue_size=5000
)
```

**Optimize Sampling**
```python
sampling_config = SamplingConfig(
    enabled=True,
    default_rate=0.1,
    adaptive_sampling=True  # Automatically adjust based on load
)
```

### 2. Slow Log Delivery

#### Symptoms
- High latency in log delivery
- Logs appearing delayed in CloudWatch
- Buffer filling up

#### Diagnosis
```bash
# Check buffer flush rates
kubectl logs <pod-name> | grep "buffer_flush"

# Check CloudWatch delivery latency
kubectl logs <pod-name> | grep "cloudwatch_latency"

# Check network connectivity
kubectl exec <pod-name> -- ping logs.us-west-2.amazonaws.com
```

#### Solutions

**Optimize Batching**
```python
cloudwatch_config = CloudWatchConfig(
    batch_size=1000,  # Larger batches
    max_batch_wait_time=30,  # Longer wait time
    parallel_streams=3  # Multiple parallel streams
)
```

**Reduce Buffer Flush Interval**
```python
buffer_config = BufferConfig(
    flush_interval=2,  # Flush every 2 seconds
    max_size=20000,  # Larger buffer to handle bursts
    async_flush=True
)
```

**Enable Compression**
```python
cloudwatch_config = CloudWatchConfig(
    enable_compression=True,
    compression_level=6  # Balance between speed and size
)
```

## CloudWatch Issues

### 1. Logs Not Appearing in CloudWatch

#### Symptoms
- No logs in CloudWatch console
- No delivery errors in application logs
- Health checks passing

#### Diagnosis
```bash
# Check AWS credentials
kubectl exec <pod-name> -- aws sts get-caller-identity

# Check CloudWatch permissions
aws logs describe-log-groups --log-group-name-prefix /aws/eks/

# Check log group existence
aws logs describe-log-groups --log-group-name-prefix /aws/eks/my-application

# Check delivery metrics
kubectl logs <pod-name> | grep "cloudwatch_delivery"
```

#### Solutions

**Verify IAM Permissions**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents",
        "logs:DescribeLogGroups",
        "logs:DescribeLogStreams"
      ],
      "Resource": "arn:aws:logs:*:*:log-group:/aws/eks/my-application*"
    }
  ]
}
```

**Create Log Group Manually**
```bash
aws logs create-log-group \
  --log-group-name /aws/eks/my-application \
  --region us-west-2

aws logs put-retention-policy \
  --log-group-name /aws/eks/my-application \
  --retention-in-days 30
```

**Enable Debug Logging**
```python
cloudwatch_config = CloudWatchConfig(
    debug_mode=True,  # Log all CloudWatch operations
    log_delivery_errors=True
)
```

### 2. CloudWatch Rate Limiting

#### Symptoms
- Rate limit errors in logs
- Delayed log delivery
- Throttling exceptions

#### Diagnosis
```bash
# Check rate limit errors
kubectl logs <pod-name> | grep -i "rate.limit\|throttl"

# Check delivery rates
kubectl logs <pod-name> | grep "delivery_rate"

# Monitor CloudWatch metrics
aws logs describe-metric-filters --log-group-name /aws/eks/my-application
```

#### Solutions

**Implement Exponential Backoff**
```python
cloudwatch_config = CloudWatchConfig(
    retry_backoff_multiplier=2.0,
    max_retry_attempts=5,
    base_retry_delay=1.0
)
```

**Optimize Batch Sizes**
```python
cloudwatch_config = CloudWatchConfig(
    batch_size=500,  # Smaller batches
    max_batch_wait_time=60,  # Longer wait times
    adaptive_batching=True  # Automatically adjust batch size
)
```

**Implement Circuit Breaker**
```python
cloudwatch_config = CloudWatchConfig(
    circuit_breaker_enabled=True,
    failure_threshold=10,
    recovery_timeout=300
)
```

### 3. High CloudWatch Costs

#### Symptoms
- Unexpected CloudWatch charges
- High log ingestion volume
- Large log group sizes

#### Diagnosis
```bash
# Check log volume
aws logs describe-log-groups --query 'logGroups[?logGroupName==`/aws/eks/my-application`].storedBytes'

# Check ingestion rate
kubectl logs <pod-name> | grep "logs_sent_total"

# Analyze log content
aws logs filter-log-events --log-group-name /aws/eks/my-application --limit 10
```

#### Solutions

**Enable Aggressive Sampling**
```python
sampling_config = SamplingConfig(
    enabled=True,
    default_rate=0.05,  # Sample only 5% of logs
    cost_optimization=True
)
```

**Enable Compression and Deduplication**
```python
cloudwatch_config = CloudWatchConfig(
    enable_compression=True,
    enable_deduplication=True,
    deduplication_window=300  # 5 minutes
)
```

**Set Retention Policies**
```bash
aws logs put-retention-policy \
  --log-group-name /aws/eks/my-application \
  --retention-in-days 7  # Reduce from default
```

## Kubernetes Integration Issues

### 1. Pod Security Policy Violations

#### Symptoms
- Pods failing to start
- Security policy errors
- Permission denied errors

#### Diagnosis
```bash
# Check pod security context
kubectl describe pod <pod-name> | grep -A 10 "Security Context"

# Check security policies
kubectl get psp
kubectl describe psp ucbl-logger-psp

# Check events for security violations
kubectl get events | grep -i security
```

#### Solutions

**Update Security Context**
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
```

**Create Compatible PSP**
```yaml
apiVersion: policy/v1beta1
kind: PodSecurityPolicy
metadata:
  name: ucbl-logger-psp
spec:
  privileged: false
  allowPrivilegeEscalation: false
  requiredDropCapabilities:
    - ALL
  volumes:
    - 'configMap'
    - 'emptyDir'
    - 'projected'
    - 'secret'
  runAsUser:
    rule: 'MustRunAsNonRoot'
  seLinux:
    rule: 'RunAsAny'
  fsGroup:
    rule: 'RunAsAny'
```

### 2. Network Policy Issues

#### Symptoms
- Cannot reach Kubernetes API
- CloudWatch delivery failures
- Health check failures

#### Diagnosis
```bash
# Test Kubernetes API connectivity
kubectl exec <pod-name> -- curl -k https://kubernetes.default.svc

# Test external connectivity
kubectl exec <pod-name> -- curl -I https://logs.us-west-2.amazonaws.com

# Check network policies
kubectl get networkpolicy
kubectl describe networkpolicy ucbl-logger-network-policy
```

#### Solutions

**Update Network Policy**
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
  - Egress
  egress:
  - to: []
    ports:
    - protocol: TCP
      port: 443  # HTTPS
    - protocol: UDP
      port: 53   # DNS
  - to:
    - namespaceSelector:
        matchLabels:
          name: kube-system
    ports:
    - protocol: TCP
      port: 443  # Kubernetes API
```

## Security Issues

### 1. Sensitive Data in Logs

#### Symptoms
- PII appearing in logs
- Security audit failures
- Compliance violations

#### Diagnosis
```bash
# Search for potential PII
kubectl logs <pod-name> | grep -E '\b\d{3}-\d{2}-\d{4}\b'  # SSN
kubectl logs <pod-name> | grep -E '\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'  # Email

# Check redaction statistics
kubectl logs <pod-name> | grep "redaction_stats"
```

#### Solutions

**Enable Data Redaction**
```python
security_config = SecurityConfig(
    enable_data_redaction=True,
    redaction_patterns=[
        r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
        r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',  # Credit cards
    ],
    audit_redactions=True
)
```

**Custom Redaction Rules**
```python
# Add application-specific patterns
custom_patterns = [
    r'password["\s]*[:=]["\s]*[^"\s]+',  # Passwords
    r'api[_-]?key["\s]*[:=]["\s]*[^"\s]+',  # API keys
    r'Bearer\s+[A-Za-z0-9\-._~+/]+=*',  # Bearer tokens
]

security_config.redaction_patterns.extend(custom_patterns)
```

### 2. Container Security Violations

#### Symptoms
- Security scanning alerts
- Runtime security violations
- Privilege escalation attempts

#### Diagnosis
```bash
# Check container security context
kubectl describe pod <pod-name> | grep -A 20 "Security Context"

# Check for privilege escalation
kubectl logs <pod-name> | grep -i "privilege"

# Check runtime security events
kubectl get events | grep -i security
```

#### Solutions

**Harden Container Security**
```yaml
securityContext:
  runAsNonRoot: true
  runAsUser: 1000
  allowPrivilegeEscalation: false
  readOnlyRootFilesystem: true
  capabilities:
    drop:
    - ALL
  seccompProfile:
    type: RuntimeDefault
```

**Use Distroless Images**
```dockerfile
FROM gcr.io/distroless/python3
COPY --from=builder /app /app
WORKDIR /app
USER 1000
CMD ["main.py"]
```

## Monitoring Issues

### 1. Metrics Not Being Scraped

#### Symptoms
- Missing metrics in Prometheus
- Empty Grafana dashboards
- No alerting

#### Diagnosis
```bash
# Check metrics endpoint
kubectl exec <pod-name> -- curl localhost:9090/metrics

# Check ServiceMonitor
kubectl get servicemonitor ucbl-logger-metrics -o yaml

# Check Prometheus targets
kubectl port-forward svc/prometheus 9090:9090
# Visit http://localhost:9090/targets
```

#### Solutions

**Fix ServiceMonitor Configuration**
```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: ucbl-logger-metrics
spec:
  selector:
    matchLabels:
      app: my-application
  endpoints:
  - port: metrics
    interval: 30s
    path: /metrics
```

**Verify Service Labels**
```yaml
apiVersion: v1
kind: Service
metadata:
  name: my-application-service
  labels:
    app: my-application  # Must match ServiceMonitor selector
spec:
  ports:
  - name: metrics
    port: 9090
    targetPort: 9090
```

### 2. Alerting Not Working

#### Symptoms
- No alerts firing
- Missing notifications
- Incorrect alert states

#### Diagnosis
```bash
# Check PrometheusRule
kubectl get prometheusrule ucbl-logger-alerts -o yaml

# Check alert states in Prometheus
kubectl port-forward svc/prometheus 9090:9090
# Visit http://localhost:9090/alerts

# Check AlertManager configuration
kubectl get secret alertmanager-main -o yaml
```

#### Solutions

**Fix Alert Rules**
```yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: ucbl-logger-alerts
spec:
  groups:
  - name: ucbl_logger
    rules:
    - alert: UCBLLoggerDown
      expr: up{job="ucbl-logger"} == 0
      for: 1m
      labels:
        severity: critical
      annotations:
        summary: "UCBLLogger is down"
```

**Configure AlertManager**
```yaml
global:
  slack_api_url: 'YOUR_SLACK_WEBHOOK_URL'

route:
  group_by: ['alertname']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'web.hook'

receivers:
- name: 'web.hook'
  slack_configs:
  - channel: '#alerts'
    text: '{{ range .Alerts }}{{ .Annotations.summary }}{{ end }}'
```

## Debug Tools

### 1. Debug Mode

```python
# Enable comprehensive debugging
logger = EnhancedEKSLogger(
    service_name="debug-service",
    debug_mode=True,
    log_level=logging.DEBUG,
    enable_trace_logging=True,
    enable_performance_profiling=True
)
```

### 2. Health Check Script

```python
#!/usr/bin/env python3
# health_check.py - Comprehensive health check script

import requests
import json
import sys

def check_health():
    try:
        response = requests.get('http://localhost:8080/health', timeout=10)
        health_data = response.json()
        
        print(f"Overall Status: {health_data['status']}")
        print(f"Health Score: {health_data.get('health_score', 'N/A')}")
        
        for component, status in health_data.get('components', {}).items():
            print(f"{component}: {status.get('status', 'unknown')}")
            
        return health_data['status'] == 'healthy'
    except Exception as e:
        print(f"Health check failed: {e}")
        return False

if __name__ == "__main__":
    if check_health():
        sys.exit(0)
    else:
        sys.exit(1)
```

### 3. Log Analysis Script

```bash
#!/bin/bash
# analyze_logs.sh - Log analysis script

POD_NAME=$(kubectl get pods -l app=my-application -o jsonpath='{.items[0].metadata.name}')

echo "=== Error Analysis ==="
kubectl logs $POD_NAME | grep -i error | tail -10

echo "=== Performance Metrics ==="
kubectl logs $POD_NAME | grep "cpu_usage\|memory_usage" | tail -5

echo "=== Buffer Statistics ==="
kubectl logs $POD_NAME | grep "buffer_usage" | tail -5

echo "=== CloudWatch Delivery ==="
kubectl logs $POD_NAME | grep "cloudwatch" | tail -5

echo "=== Sampling Statistics ==="
kubectl logs $POD_NAME | grep "sampling" | tail -5
```

## Recovery Procedures

### 1. Emergency Recovery

```bash
#!/bin/bash
# emergency_recovery.sh - Emergency recovery procedures

echo "Starting emergency recovery..."

# Scale down deployment
kubectl scale deployment my-application --replicas=0

# Wait for pods to terminate
kubectl wait --for=delete pod -l app=my-application --timeout=60s

# Clear any stuck resources
kubectl delete pod -l app=my-application --force --grace-period=0

# Scale back up
kubectl scale deployment my-application --replicas=3

# Wait for pods to be ready
kubectl wait --for=condition=ready pod -l app=my-application --timeout=300s

echo "Emergency recovery completed"
```

### 2. Configuration Reset

```bash
#!/bin/bash
# reset_config.sh - Reset configuration to defaults

# Backup current configuration
kubectl get configmap ucbl-logger-config -o yaml > backup-config-$(date +%Y%m%d-%H%M%S).yaml

# Apply default configuration
kubectl apply -f deployment/kubernetes/configmap.yaml

# Restart deployment
kubectl rollout restart deployment my-application

# Wait for rollout to complete
kubectl rollout status deployment my-application
```

### 3. Data Recovery

```python
#!/usr/bin/env python3
# recover_logs.py - Recover logs from buffer files

import os
import json
import gzip
from datetime import datetime

def recover_buffer_logs(buffer_path="/var/log/ucbl-buffer"):
    """Recover logs from buffer files"""
    recovered_logs = []
    
    for filename in os.listdir(buffer_path):
        if filename.endswith('.log') or filename.endswith('.log.gz'):
            filepath = os.path.join(buffer_path, filename)
            
            try:
                if filename.endswith('.gz'):
                    with gzip.open(filepath, 'rt') as f:
                        logs = f.readlines()
                else:
                    with open(filepath, 'r') as f:
                        logs = f.readlines()
                
                for log_line in logs:
                    try:
                        log_entry = json.loads(log_line.strip())
                        recovered_logs.append(log_entry)
                    except json.JSONDecodeError:
                        continue
                        
            except Exception as e:
                print(f"Error reading {filepath}: {e}")
    
    return recovered_logs

if __name__ == "__main__":
    logs = recover_buffer_logs()
    print(f"Recovered {len(logs)} log entries")
    
    # Save to recovery file
    recovery_file = f"recovered_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(recovery_file, 'w') as f:
        json.dump(logs, f, indent=2)
    
    print(f"Logs saved to {recovery_file}")
```

This troubleshooting guide provides comprehensive procedures for diagnosing and resolving common issues with the Enhanced UCBLLogger in EKS environments.