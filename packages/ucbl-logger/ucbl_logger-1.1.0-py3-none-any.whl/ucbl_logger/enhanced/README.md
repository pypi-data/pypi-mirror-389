# Enhanced EKS Logger Components

This directory contains the enhanced logging components optimized for EKS (Elastic Kubernetes Service) container deployments. These components provide advanced features like distributed tracing, Kubernetes metadata collection, performance monitoring, and intelligent log sampling.

## Directory Structure

```
enhanced/
├── __init__.py                 # Main exports for enhanced components
├── README.md                   # This file
├── interfaces.py               # Core interfaces for all enhanced components
├── models.py                   # Data models and configuration classes
├── enhanced_eks_logger.py      # Main enhanced logger base class
├── config.py                   # Configuration management
├── factory.py                  # Factory for creating logger instances
├── tracing/                    # Distributed tracing components
├── metadata/                   # Kubernetes metadata collection
├── performance/                # Performance monitoring components
├── sampling/                   # Intelligent log sampling
├── buffering/                  # Log buffering and delivery management
├── health/                     # Health monitoring components
└── security/                   # Security context logging and data protection
```

## Core Components

### 1. Enhanced EKS Logger Base (`enhanced_eks_logger.py`)
The main logger class that orchestrates all enhanced components while maintaining backward compatibility with the existing UCBLLogger API.

### 2. Interfaces (`interfaces.py`)
Defines the contracts for all enhanced components:
- `ITracingManager`: Distributed tracing management
- `IMetadataCollector`: Kubernetes metadata collection
- `IPerformanceMonitor`: System performance monitoring
- `ISamplingEngine`: Intelligent log sampling
- `IBufferManager`: Log buffering and delivery
- `IHealthMonitor`: Logging system health monitoring
- `ISecurityContextLogger`: Security context logging

### 3. Data Models (`models.py`)
Core data structures used throughout the enhanced logging system:
- `EnhancedLogEntry`: Complete log entry with all metadata
- `TraceContext`: Distributed tracing context information
- `SystemMetrics`: Performance metrics data
- `SamplingConfig`: Log sampling configuration
- `BufferConfig`: Log buffering configuration
- `PerformanceThresholds`: Performance monitoring thresholds
- `HealthStatus`: Logging system health status

### 4. Configuration Management (`config.py`)
Provides configuration classes and environment variable support:
- `EnhancedEKSConfig`: Complete configuration for enhanced logger
- Environment variable mapping for container deployment
- Configuration validation

### 5. Factory (`factory.py`)
Factory methods for creating enhanced loggers:
- `create_logger()`: Create with custom configuration
- `create_minimal_logger()`: Minimal features for basic use
- `create_development_logger()`: Optimized for development
- `create_production_logger()`: Optimized for production
- `create_from_dict()`: Create from dictionary configuration

## Component Directories

Each component directory contains:
- `__init__.py`: Component exports
- `interfaces.py`: Component-specific interfaces (if needed)
- `models.py`: Component-specific data models (if needed)

### Tracing (`tracing/`)
Distributed tracing capabilities for tracking requests across microservices.

### Metadata (`metadata/`)
Kubernetes metadata collection including pod, node, and cluster information.

### Performance (`performance/`)
System performance monitoring including CPU, memory, disk, and network metrics.

### Sampling (`sampling/`)
Intelligent log sampling to control log volume while preserving critical information.

### Buffering (`buffering/`)
Log buffering and delivery management with retry logic and failure handling.

### Health (`health/`)
Health monitoring for the logging system itself.

### Security (`security/`)
Security context logging and sensitive data protection.

## Backward Compatibility

The enhanced components are designed to maintain full backward compatibility with the existing UCBLLogger API. Existing applications can continue to use the standard logger without any changes, while new applications can opt into enhanced features.

## Usage Examples

### Basic Enhanced Logger
```python
from ucbl_logger.enhanced import EnhancedEKSLoggerFactory

# Create with default configuration
logger = EnhancedEKSLoggerFactory.create_logger(
    service_name="my-service",
    namespace="production"
)

# Use enhanced logging with correlation ID
correlation_id = logger.start_trace("user_request")
logger.info("Processing user request", correlation_id=correlation_id, user_id="12345")
logger.end_trace(correlation_id, success=True)
```

### Production Logger
```python
# Create production-optimized logger
logger = EnhancedEKSLoggerFactory.create_production_logger(
    service_name="my-service",
    namespace="production"
)

# Automatic performance monitoring and sampling
logger.info("High-volume operation completed")
logger.log_performance_metrics()
```

### Development Logger
```python
# Create development-optimized logger (no sampling, faster feedback)
logger = EnhancedEKSLoggerFactory.create_development_logger(
    service_name="my-service",
    namespace="development"
)
```

## Environment Variables

The enhanced logger supports configuration via environment variables:

### Basic Configuration
- `UCBL_SERVICE_NAME`: Service name for logging context
- `UCBL_NAMESPACE` or `KUBERNETES_NAMESPACE`: Kubernetes namespace

### Feature Flags
- `UCBL_ENABLE_TRACING`: Enable distributed tracing (true/false)
- `UCBL_ENABLE_PERFORMANCE`: Enable performance monitoring (true/false)
- `UCBL_ENABLE_K8S_METADATA`: Enable Kubernetes metadata collection (true/false)
- `UCBL_ENABLE_SAMPLING`: Enable log sampling (true/false)
- `UCBL_ENABLE_SECURITY`: Enable security logging (true/false)
- `UCBL_ENABLE_HEALTH`: Enable health monitoring (true/false)

### Sampling Configuration
- `UCBL_SAMPLING_DEFAULT_RATE`: Default sampling rate (0.0-1.0)
- `UCBL_SAMPLING_VOLUME_THRESHOLD`: Log volume threshold for sampling activation
- `UCBL_SAMPLING_WINDOW_SIZE`: Sampling window size in seconds
- `UCBL_SAMPLING_DEBUG_MODE`: Disable sampling for debugging (true/false)

### Buffer Configuration
- `UCBL_BUFFER_MAX_SIZE`: Maximum buffer size
- `UCBL_BUFFER_FLUSH_INTERVAL`: Buffer flush interval in seconds
- `UCBL_BUFFER_MAX_RETRIES`: Maximum retry attempts for failed deliveries
- `UCBL_BUFFER_COMPRESSION`: Enable log compression (true/false)

### Performance Thresholds
- `UCBL_CPU_WARNING_THRESHOLD`: CPU warning threshold percentage
- `UCBL_CPU_CRITICAL_THRESHOLD`: CPU critical threshold percentage
- `UCBL_MEMORY_WARNING_THRESHOLD`: Memory warning threshold percentage
- `UCBL_MEMORY_CRITICAL_THRESHOLD`: Memory critical threshold percentage

### CloudWatch Configuration
- `UCBL_CLOUDWATCH_LOG_GROUP`: CloudWatch log group name
- `UCBL_CLOUDWATCH_LOG_STREAM`: CloudWatch log stream name
- `UCBL_CLOUDWATCH_REGION` or `AWS_REGION`: AWS region

### OpenTelemetry Configuration
- `OTEL_EXPORTER_OTLP_ENDPOINT` or `UCBL_OTEL_ENDPOINT`: OpenTelemetry endpoint
- `OTEL_SERVICE_NAME` or `UCBL_OTEL_SERVICE_NAME`: Service name for tracing
- `OTEL_SERVICE_VERSION` or `UCBL_OTEL_SERVICE_VERSION`: Service version

## Implementation Status

This is the initial structure and interface definition. Concrete implementations for each component will be added in subsequent tasks:

- Task 2: Distributed tracing implementation
- Task 3: Kubernetes metadata collection implementation
- Task 4: Performance monitoring implementation
- Task 5: Log sampling engine implementation
- Task 6: Buffer management implementation
- Task 7: Security enhancements implementation
- Task 8: Health monitoring implementation
- Task 9: CloudWatch integration implementation
- Task 10: Complete enhanced logger implementation

## Requirements Mapping

This structure addresses the following requirements:
- **Requirement 1.1**: Distributed tracing interfaces and models
- **Requirement 2.1**: Kubernetes metadata collection interfaces
- **Requirement 3.1**: Performance monitoring interfaces and thresholds
- **Requirement 4.1**: Log sampling interfaces and configuration
- **Requirement 5.1**: Buffer management interfaces
- **Requirement 6.1**: Security context logging interfaces
- **Requirement 7.1**: Health monitoring interfaces
- **Requirement 8.1**: CloudWatch integration configuration