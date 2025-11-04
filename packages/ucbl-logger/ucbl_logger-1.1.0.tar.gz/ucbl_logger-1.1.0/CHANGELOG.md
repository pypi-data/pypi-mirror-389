# Changelog

All notable changes to UCBLLogger will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2024-12-19

### Added
- Added missing `warn()` method aliases to all logger classes for full Python logging compatibility
- Enhanced logger compatibility with standard logging conventions

### Fixed
- Fixed missing `warn()` and `warning()` methods in `ucbl_logger/eks_logger.py`
- Added `warn()` aliases to all enhanced logger implementations
- Improved consistency across all logger interfaces

### Changed
- Anonymized all documentation to remove specific application references
- Updated README.md, EXAMPLES.md, and docs/ to use generic application names
- Improved documentation consistency and reusability

## [1.0.29] - 2024-12-19

### Fixed
- Fixed `end_trace()` method to accept `metadata` parameter as documented
- Resolved runtime error: "EnhancedEKSLogger.end_trace() got an unexpected keyword argument 'metadata'"
- Enhanced tracing manager compatibility with metadata support

### Changed
- Improved error handling in tracing operations
- Added graceful fallback when tracing manager doesn't support metadata

## [1.0.22] - 2024-12-19

### Added
- Enhanced EKS Logger implementation with comprehensive component orchestration
- Distributed tracing with correlation ID generation and propagation
- Kubernetes metadata collection for pod, node, and cluster information
- Performance monitoring with real-time system metrics
- Intelligent log sampling with adaptive volume control
- CloudWatch integration with batching and compression
- Security context monitoring and data redaction
- Health monitoring with comprehensive status reporting
- Advanced buffering with retry mechanisms

### Changed
- Updated Python requirement to >=3.11
- Improved GitHub Actions workflow with proper artifact handling
- Enhanced test coverage with mock support for EKS environments

### Fixed
- Resolved GitHub Actions workflow deprecation warnings
- Fixed PyPI publishing with proper permissions and API token handling

## [1.0.0] - 2024-12-18

### Added
- Initial release of UCBLLogger
- Core logging functionality with structured logging
- Task tracking and retry monitoring
- Risk and anomaly logging capabilities
- GOMS model integration for behavioral analysis
- Timezone-aware logging
- Customizable task types and metadata support
- Advanced markup methods for log formatting
- Exception handling with detailed stack traces

### Features
- Multiple task types (USER_TASK, SYSTEM_TASK, etc.)
- Configurable retry thresholds and slow step detection
- Dynamic property getters and setters
- Context manager support
- Comprehensive documentation and examples

---

## Release Notes

### Version 1.0.29
This version resolves a critical runtime error in the enhanced EKS logger where the `end_trace()` method was being called with a `metadata` parameter that wasn't properly handled. The fix ensures backward compatibility while adding support for trace metadata.

### Version 1.0.22
Major release introducing the Enhanced EKS Logger with enterprise-grade features for Kubernetes deployments. This version provides comprehensive observability, performance monitoring, and cost optimization features specifically designed for containerized applications.

### Version 1.0.0
Initial stable release providing core user-centric behavior logging capabilities with structured logging, task tracking, and behavioral analysis features.

---

## Migration Guide

### From 1.0.22 to 1.0.29
No breaking changes. The `end_trace()` method now properly supports the `metadata` parameter as documented.

### From 1.0.0 to 1.0.22
The enhanced EKS features are optional and backward compatible. Existing code will continue to work unchanged. To use enhanced features:

```python
# Old way (still works)
from ucbl_logger import UCBLLogger
logger = UCBLLogger()

# New enhanced way
from ucbl_logger.enhanced import EnhancedEKSLogger
logger = EnhancedEKSLogger(service_name="my-service")
```

---

## Support

For questions, issues, or contributions:
- **GitHub Issues**: [Report bugs or request features](https://github.com/your-org/ucbl-logger/issues)
- **Documentation**: [README.md](README.md) and [EXAMPLES.md](EXAMPLES.md)
- **Email**: evan@erwee.com