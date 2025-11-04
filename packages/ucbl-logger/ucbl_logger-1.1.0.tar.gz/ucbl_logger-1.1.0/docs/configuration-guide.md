# UCBLLogger Enhanced EKS Configuration Guide

This guide provides comprehensive configuration options for the Enhanced UCBLLogger in EKS environments.

## Table of Contents

1. [Environment Variables](#environment-variables)
2. [Configuration Classes](#configuration-classes)
3. [Kubernetes Configuration](#kubernetes-configuration)
4. [CloudWatch Configuration](#cloudwatch-configuration)
5. [Performance Tuning](#performance-tuning)
6. [Security Configuration](#security-configuration)
7. [Monitoring Configuration](#monitoring-configuration)
8. [Best Practices](#best-practices)

## Environment Variables

### Core Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `SERVICE_NAME` | `"ucbl-logger"` | Service identifier for logs and metrics |
| `NAMESPACE` | `"default"` | Kubernetes namespace |
| `ENVIRONMENT` | `"production"` | Environment identifier |
| `UCBL_LOG_LEVEL` | `"INFO"` | Logging level (DEBUG, INFO, WARN, ERROR, CRITICAL) |

### Tracing Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `UCBL_ENABLE_TRACING` | `"true"` | Enable distributed tracing |
| `UCBL_ENABLE_OPENTELEMETRY` | `"false"` | Enable OpenTelemetry integration |
| `UCBL_TRACE_HEADER_NAME` | `"X-Correlation-ID"` | HTTP header for correlation ID |

### Performance Monitoring

| Variable | Default | Description |
|----------|---------|-------------|
| `UCBL_ENABLE_PERFORMANCE_MONITORING` | `"true"` | Enable performance metrics collection |
| `UCBL_PERFORMANCE_COLLECTION_INTERVAL` | `"60"` | Metrics collection interval (seconds) |
| `UCBL_CPU_WARNING_THRESHOLD` | `"80.0"` | CPU usage warning threshold (%) |
| `UCBL_CPU_CRITICAL_THRESHOLD` | `"95.0"` | CPU usage critical threshold (%) |
| `UCBL_MEMORY_WARNING_THRESHOLD` | `"80.0"` | Memory usage warning threshold (%) |
| `UCBL_MEMORY_CRITICAL_THRESHOLD` | `"95.0"` | Memory usage critical threshold (%) |
| `UCBL_DISK_IO_WARNING_THRESHOLD` | `"80.0"` | Disk I/O warning threshold (%) |
| `UCBL_NETWORK_LATENCY_WARNING` | `"100.0"` | Network latency warning threshold (ms) |

### Sampling Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `UCBL_ENABLE_SAMPLING` | `"true"` | Enable intelligent log sampling |
| `UCBL_DEFAULT_SAMPLING_RATE` | `"1.0"` | Default sampling rate (0.0-1.0) |
| `UCBL_VOLUME_THRESHOLD` | `"1000"` | Log volume threshold for sampling activation |
| `UCBL_SAMPLING_WINDOW_SIZE` | `"60"` | Sampling window size (seconds) |
| `UCBL_PRESERVE_ERRORS` | `"true"` | Always preserve error and critical logs |
| `UCBL_DEBUG_SAMPLING_RATE` | `"0.01"` | Sampling rate for DEBUG logs |
| `UCBL_INFO_SAMPLING_RATE` | `"0.1"` | Sampling rate for INFO logs |
| `UCBL_WARNING_SAMPLING_RATE` | `"0.5"` | Sampling rate for WARNING logs |

### Buffer Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `UCBL_BUFFER_MAX_SIZE` | `"10000"` | Maximum buffer size (number of log entries) |
| `UCBL_BUFFER_FLUSH_INTERVAL` | `"5"` | Buffer flush interval (seconds) |
| `UCBL_MAX_RETRY_ATTEMPTS` | `"3"` | Maximum retry attempts for failed deliveries |
| `UCBL_RETRY_BACKOFF_MULTIPLIER` | `"2.0"` | Exponential backoff multiplier |
| `UCBL_FAILED_LOG_RETENTION` | `"1000"` | Number of failed logs to retain |

### CloudWatch Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `UCBL_ENABLE_CLOUDWATCH` | `"true"` | Enable CloudWatch log delivery |
| `UCBL_CLOUDWATCH_LOG_GROUP` | `"/aws/eks/ucbl-logger"` | CloudWatch log group name |
| `UCBL_CLOUDWATCH_REGION` | `"us-west-2"` | AWS region for CloudWatch |
| `UCBL_ENABLE_COMPRESSION` | `"true"` | Enable log compression |
| `UCBL_BATCH_SIZE` | `"100"` | CloudWatch batch size |
| `UCBL_MAX_BATCH_WAIT_TIME` | `"10"` | Maximum batch wait time (seconds) |
| `UCBL_ENABLE_DEDUPLICATION` | `"false"` | Enable log deduplication |

### Security Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `UCBL_ENABLE_SECURITY_MONITORING` | `"true"` | Enable security context monitoring |
| `UCBL_ENABLE_DATA_REDACTION` | `"true"` | Enable sensitive data redaction |
| `UCBL_REDACTION_REPLACEMENT` | `"[REDACTED]"` | Replacement text for redacted data |

### Health Monitoring

| Variable | Default | Description |
|----------|---------|-------------|
| `UCBL_ENABLE_HEALTH_MONITORING` | `"true"` | Enable health monitoring |
| `UCBL_HEALTH_CHECK_PORT` | `"8080"` | Health check endpoint port |
| `UCBL_HEALTH_CHECK_PATH` | `"/health"` | Health check endpoint path |
| `UCBL_METRICS_PORT` | `"9090"` | Prometheus metrics port |
| `UCBL_METRICS_PATH` | `"/metrics"` | Prometheus metrics path |

## Configuration Classes

### SamplingConfig

```python
from ucbl_logger.enhanced.config import SamplingConfig

# Basic sampling configuration
sampling_config = SamplingConfig(
    enabled=True,
    default_rate=0.1,
    volume_threshold=1000,
    window_size=60,
    preserve_errors=True
)

# Advanced sampling with per-level rates
sampling_config = SamplingConfig(
    enabled=True,
    default_rate=0.1,
    level_rates={
        'DEBUG': 0.01,
        'INFO': 0.1,
        'WARNING': 0.5,
        'ERROR': 1.0,
        'CRITICAL': 1.0
    },
    volume_threshold=1000,
    window_size=60,
    preserve_errors=True
)
```

### BufferConfig

```python
from ucbl_logger.enhanced.config import BufferConfig

# Production buffer configuration
buffer_config = BufferConfig(
    max_size=50000,
    flush_interval=10,
    max_retry_attempts=5,
    retry_backoff_multiplier=1.5,
    failed_log_retention=5000
)

# Development buffer configuration
buffer_config = BufferConfig(
    max_size=5000,
    flush_interval=2,
    max_retry_attempts=3,
    retry_backoff_multiplier=2.0,
    failed_log_retention=1000
)
```

### PerformanceThresholds

```python
from ucbl_logger.enhanced.config import PerformanceThresholds

# Conservative thresholds for production
performance_config = PerformanceThresholds(
    cpu_warning=70.0,
    cpu_critical=90.0,
    memory_warning=75.0,
    memory_critical=90.0,
    disk_io_warning=80.0,
    network_latency_warning=100.0
)

# Aggressive thresholds for development
performance_config = PerformanceThresholds(
    cpu_warning=85.0,
    cpu_critical=95.0,
    memory_warning=85.0,
    memory_critical=95.0,
    disk_io_warning=90.0,
    network_latency_warning=200.0
)
```

### CloudWatchConfig

```python
from ucbl_logger.enhanced.config import CloudWatchConfig

# Cost-optimized CloudWatch configuration
cloudwatch_config = CloudWatchConfig(
    log_group="/aws/eks/my-application",
    region="us-west-2",
    enable_compression=True,
    batch_size=1000,
    max_batch_wait_time=30,
    enable_deduplication=True,
    retention_days=30
)

# High-throughput CloudWatch configuration
cloudwatch_config = CloudWatchConfig(
    log_group="/aws/eks/my-application",
    region="us-west-2",
    enable_compression=False,
    batch_size=100,
    max_batch_wait_time=5,
    enable_deduplication=False,
    retention_days=7
)
```

## Kubernetes Configuration

### ConfigMap Example

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: ucbl-logger-config-production
  namespace: production
data:
  # Service Configuration
  SERVICE_NAME: "my-application"
  ENVIRONMENT: "production"
  UCBL_LOG_LEVEL: "WARN"
  
  # Tracing Configuration
  UCBL_ENABLE_TRACING: "true"
  UCBL_ENABLE_OPENTELEMETRY: "true"
  
  # Performance Monitoring (reduced frequency for production)
  UCBL_ENABLE_PERFORMANCE_MONITORING: "true"
  UCBL_PERFORMANCE_COLLECTION_INTERVAL: "300"
  UCBL_CPU_WARNING_THRESHOLD: "70.0"
  UCBL_CPU_CRITICAL_THRESHOLD: "90.0"
  
  # Aggressive sampling for production
  UCBL_ENABLE_SAMPLING: "true"
  UCBL_DEFAULT_SAMPLING_RATE: "0.05"
  UCBL_VOLUME_THRESHOLD: "500"
  
  # Larger buffers for production
  UCBL_BUFFER_MAX_SIZE: "50000"
  UCBL_BUFFER_FLUSH_INTERVAL: "10"
  
  # CloudWatch optimization
  UCBL_ENABLE_CLOUDWATCH: "true"
  UCBL_CLOUDWATCH_LOG_GROUP: "/aws/eks/my-application-prod"
  UCBL_ENABLE_COMPRESSION: "true"
  UCBL_BATCH_SIZE: "1000"
```

### Deployment Configuration

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-application
spec:
  template:
    spec:
      containers:
      - name: app
        env:
        # Load configuration from ConfigMap
        - name: SERVICE_NAME
          valueFrom:
            configMapKeyRef:
              name: ucbl-logger-config-production
              key: SERVICE_NAME
        # ... (other environment variables)
        
        # Kubernetes metadata
        - name: NAMESPACE
          valueFrom:
            fieldRef:
              fieldPath: metadata.namespace
        - name: POD_NAME
          valueFrom:
            fieldRef:
              fieldPath: metadata.name
        - name: NODE_NAME
          valueFrom:
            fieldRef:
              fieldPath: spec.nodeName
```

## CloudWatch Configuration

### IAM Role for Service Accounts (IRSA)

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: ucbl-logger-service-account
  annotations:
    eks.amazonaws.com/role-arn: arn:aws:iam::ACCOUNT_ID:role/UCBLLoggerRole
```

### IAM Policy

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
      "Resource": [
        "arn:aws:logs:*:*:log-group:/aws/eks/*",
        "arn:aws:logs:*:*:log-group:/aws/eks/*:*"
      ]
    }
  ]
}
```

### CloudWatch Log Group Configuration

```python
import boto3

# Create log group with retention
logs_client = boto3.client('logs', region_name='us-west-2')

logs_client.create_log_group(
    logGroupName='/aws/eks/my-application',
    tags={
        'Environment': 'production',
        'Application': 'my-application',
        'ManagedBy': 'ucbl-logger'
    }
)

logs_client.put_retention_policy(
    logGroupName='/aws/eks/my-application',
    retentionInDays=30
)
```

## Performance Tuning

### High-Volume Scenarios

```python
# Configuration for high log volume (>10,000 logs/sec)
sampling_config = SamplingConfig(
    enabled=True,
    default_rate=0.01,  # Very aggressive sampling
    level_rates={
        'DEBUG': 0.001,
        'INFO': 0.01,
        'WARNING': 0.1,
        'ERROR': 1.0,
        'CRITICAL': 1.0
    },
    volume_threshold=100,  # Low threshold
    window_size=30
)

buffer_config = BufferConfig(
    max_size=100000,  # Large buffer
    flush_interval=1,  # Frequent flushes
    max_retry_attempts=2,  # Fewer retries
    retry_backoff_multiplier=1.2
)

performance_config = PerformanceThresholds(
    collection_interval=600  # Collect every 10 minutes
)
```

### Low-Resource Scenarios

```python
# Configuration for resource-constrained environments
sampling_config = SamplingConfig(
    enabled=True,
    default_rate=0.1,
    volume_threshold=100,
    window_size=60
)

buffer_config = BufferConfig(
    max_size=1000,  # Small buffer
    flush_interval=5,
    max_retry_attempts=2,
    retry_backoff_multiplier=1.5
)

performance_config = PerformanceThresholds(
    collection_interval=300,  # Less frequent collection
    cpu_warning=90.0,  # Higher thresholds
    memory_warning=90.0
)
```

### Development Scenarios

```python
# Configuration for development environments
sampling_config = SamplingConfig(
    enabled=False  # No sampling in development
)

buffer_config = BufferConfig(
    max_size=5000,
    flush_interval=2,  # Quick flushes for immediate feedback
    max_retry_attempts=1
)

performance_config = PerformanceThresholds(
    collection_interval=30,  # Frequent collection for debugging
    cpu_warning=95.0,
    memory_warning=95.0
)
```

## Security Configuration

### Data Redaction Patterns

```python
from ucbl_logger.enhanced.config import SecurityConfig

security_config = SecurityConfig(
    enable_security_monitoring=True,
    enable_data_redaction=True,
    redaction_patterns=[
        # Credit card numbers
        r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
        
        # Email addresses
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        
        # Social Security Numbers
        r'\b\d{3}-\d{2}-\d{4}\b',
        
        # Phone numbers
        r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
        
        # IP addresses (optional)
        r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',
        
        # API keys (generic pattern)
        r'\b[A-Za-z0-9]{32,}\b',
        
        # JWT tokens
        r'\beyJ[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.?[A-Za-z0-9-_.+/=]*\b'
    ],
    redaction_replacement="[REDACTED]",
    audit_redactions=True
)
```

### Container Security Context

```yaml
apiVersion: apps/v1
kind: Deployment
spec:
  template:
    spec:
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        runAsGroup: 1000
        fsGroup: 1000
      containers:
      - name: app
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          capabilities:
            drop:
            - ALL
```

## Monitoring Configuration

### Prometheus Metrics Configuration

```yaml
# ServiceMonitor for Prometheus Operator
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

### Custom Metrics

```python
from ucbl_logger.enhanced.metrics import CustomMetrics

# Define custom metrics
custom_metrics = CustomMetrics()
custom_metrics.define_counter(
    name="business_events_total",
    description="Total business events processed",
    labels=["event_type", "status"]
)

custom_metrics.define_histogram(
    name="request_duration_seconds",
    description="Request duration in seconds",
    buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0]
)

# Use in logger
logger = EnhancedEKSLogger(
    service_name="my-application",
    custom_metrics=custom_metrics
)

# Increment custom metrics
logger.increment_counter("business_events_total", 
                        labels={"event_type": "query", "status": "success"})
logger.observe_histogram("request_duration_seconds", 1.23)
```

## Best Practices

### 1. Environment-Specific Configuration

```python
import os

def get_logger_config():
    environment = os.getenv('ENVIRONMENT', 'development')
    
    if environment == 'production':
        return {
            'sampling_config': SamplingConfig(
                enabled=True,
                default_rate=0.05,
                volume_threshold=500
            ),
            'buffer_config': BufferConfig(
                max_size=50000,
                flush_interval=10
            ),
            'performance_config': PerformanceThresholds(
                collection_interval=300,
                cpu_warning=70.0
            )
        }
    elif environment == 'staging':
        return {
            'sampling_config': SamplingConfig(
                enabled=True,
                default_rate=0.2,
                volume_threshold=1000
            ),
            'buffer_config': BufferConfig(
                max_size=20000,
                flush_interval=5
            )
        }
    else:  # development
        return {
            'sampling_config': SamplingConfig(enabled=False),
            'buffer_config': BufferConfig(
                max_size=5000,
                flush_interval=2
            )
        }
```

### 2. Gradual Feature Rollout

```python
# Use feature flags for gradual rollout
logger = EnhancedEKSLogger(
    service_name="my-application",
    enable_tracing=os.getenv('FEATURE_TRACING', 'false').lower() == 'true',
    enable_performance_monitoring=os.getenv('FEATURE_PERF_MON', 'false').lower() == 'true',
    enable_sampling=os.getenv('FEATURE_SAMPLING', 'false').lower() == 'true'
)
```

### 3. Configuration Validation

```python
from ucbl_logger.enhanced.config import validate_config

# Validate configuration before initialization
config = {
    'sampling_config': sampling_config,
    'buffer_config': buffer_config,
    'performance_config': performance_config
}

validation_result = validate_config(config)
if not validation_result.is_valid:
    raise ValueError(f"Invalid configuration: {validation_result.errors}")

logger = EnhancedEKSLogger(**config)
```

### 4. Configuration Hot Reloading

```python
import signal
import json

class ConfigurableLogger:
    def __init__(self):
        self.logger = None
        self.reload_config()
        signal.signal(signal.SIGUSR1, self._reload_handler)
    
    def _reload_handler(self, signum, frame):
        self.reload_config()
    
    def reload_config(self):
        # Load configuration from file or ConfigMap
        with open('/etc/ucbl-logger/config.json', 'r') as f:
            config = json.load(f)
        
        # Reinitialize logger with new configuration
        self.logger = EnhancedEKSLogger(**config)

# Usage: Send SIGUSR1 to reload configuration
# kubectl exec <pod-name> -- kill -USR1 1
```

### 5. Monitoring Configuration Health

```python
# Monitor configuration effectiveness
def monitor_config_health(logger):
    health = logger.get_health_status()
    
    # Check if sampling is too aggressive
    if health.metrics.get('sampling_efficiency', 0) < 0.01:
        logger.warning("Sampling may be too aggressive", 
                      metadata={"sampling_rate": health.components['sampling']['current_rate']})
    
    # Check buffer usage
    buffer_usage = health.components['buffer']['usage_percent']
    if buffer_usage > 80:
        logger.warning("Buffer usage high", 
                      metadata={"buffer_usage": buffer_usage})
    
    # Check CloudWatch delivery
    cw_error_rate = health.components['cloudwatch'].get('error_rate', 0)
    if cw_error_rate > 0.05:
        logger.error("CloudWatch delivery issues", 
                    metadata={"error_rate": cw_error_rate})
```

This configuration guide provides comprehensive options for tuning the Enhanced UCBLLogger for various deployment scenarios and requirements.