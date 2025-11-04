"""
Enhanced UCBLLogger implementation with EKS integration

This module provides the enhanced UCBLLogger that seamlessly integrates
enhanced EKS features while maintaining complete backward compatibility.
The logger automatically detects EKS environments and enables enhanced
features with feature flags and gradual rollout capabilities.
"""

import os
import logging
from typing import Optional, Dict, Any, Union
from .interfaces import LogLevel
from .logger_factory import UCBLLoggerFactory

# Enhanced EKS integration (optional import for backward compatibility)
try:
    from .enhanced import (
        EnhancedEKSLogger, 
        initialize_enhanced_logger, 
        quick_setup,
        EnhancedEKSConfig,
        ConfigurationManager
    )
    _enhanced_available = True
except ImportError:
    _enhanced_available = False


class UCBLLogger:
    """
    Enhanced UCBLLogger with seamless EKS integration
    
    This class maintains complete backward compatibility while automatically
    enabling enhanced EKS features when running in Kubernetes environments.
    Feature flags and gradual rollout capabilities allow for safe adoption.
    """
    
    def __init__(self, 
                 log_level=None, 
                 timezone_str='UTC',
                 service_name: Optional[str] = None,
                 enable_eks_features: Optional[bool] = None,
                 eks_config: Optional[Dict[str, Any]] = None):
        """
        Initialize UCBLLogger with optional EKS enhancements
        
        Args:
            log_level: Legacy log level (for backward compatibility)
            timezone_str: Timezone string (for backward compatibility)
            service_name: Service name for enhanced logging (optional)
            enable_eks_features: Explicitly enable/disable EKS features (None = auto-detect)
            eks_config: Enhanced EKS configuration dictionary (optional)
        """
        # Convert old logging levels to new enum
        if log_level is None:
            level = LogLevel.INFO
        else:
            import logging
            level_mapping = {
                logging.DEBUG: LogLevel.DEBUG,
                logging.INFO: LogLevel.INFO,
                logging.WARNING: LogLevel.WARNING,
                logging.ERROR: LogLevel.ERROR,
                logging.CRITICAL: LogLevel.CRITICAL
            }
            level = level_mapping.get(log_level, LogLevel.INFO)
        
        # Store configuration
        self._log_level = level
        self._timezone = timezone_str
        self._service_name = service_name or self._detect_service_name()
        self._eks_config = eks_config or {}
        
        # Determine if EKS features should be enabled
        self._eks_features_enabled = self._should_enable_eks_features(enable_eks_features)
        
        # Initialize appropriate logger implementation
        if self._eks_features_enabled and _enhanced_available:
            self._initialize_enhanced_logger()
        else:
            self._initialize_standard_logger()
    
    def _detect_service_name(self) -> str:
        """Auto-detect service name from environment"""
        return (
            os.getenv('UCBL_SERVICE_NAME') or
            os.getenv('SERVICE_NAME') or
            os.getenv('OTEL_SERVICE_NAME') or
            'graphrag-toolkit'
        )
    
    def _should_enable_eks_features(self, explicit_setting: Optional[bool]) -> bool:
        """
        Determine if EKS features should be enabled based on environment
        and explicit settings with feature flags support.
        """
        # Explicit setting takes precedence
        if explicit_setting is not None:
            return explicit_setting and _enhanced_available
        
        # Check feature flag environment variables
        if os.getenv('UCBL_DISABLE_EKS_FEATURES', '').lower() in ('true', '1', 'yes'):
            return False
        
        if os.getenv('UCBL_ENABLE_EKS_FEATURES', '').lower() in ('true', '1', 'yes'):
            return _enhanced_available
        
        # Auto-detection based on environment
        if not _enhanced_available:
            return False
        
        # Check if running in Kubernetes
        kubernetes_indicators = [
            os.path.exists('/var/run/secrets/kubernetes.io/serviceaccount'),
            os.getenv('KUBERNETES_SERVICE_HOST') is not None,
            os.getenv('KUBERNETES_NAMESPACE') is not None,
            os.getenv('POD_NAME') is not None
        ]
        
        if any(kubernetes_indicators):
            return True
        
        # Check for EKS-specific indicators
        eks_indicators = [
            os.getenv('AWS_REGION') is not None,
            os.getenv('EKS_CLUSTER_NAME') is not None,
            'eks' in os.getenv('KUBERNETES_SERVICE_HOST', '').lower()
        ]
        
        return any(eks_indicators)
    
    def _initialize_enhanced_logger(self) -> None:
        """Initialize enhanced EKS logger"""
        try:
            # Create enhanced configuration
            if self._eks_config:
                # Use provided configuration
                config = EnhancedEKSConfig.from_dict(self._eks_config)
                config.service_name = self._service_name
            else:
                # Auto-detect environment and create appropriate config
                environment = os.getenv('ENVIRONMENT', 'auto')
                config = ConfigurationManager.create_for_environment(environment)
                config.service_name = self._service_name
            
            # Set log level from legacy parameter
            config.log_level = self._log_level.value if hasattr(self._log_level, 'value') else str(self._log_level)
            
            # Initialize enhanced logger
            self._enhanced_logger, self._initialization_report = initialize_enhanced_logger(
                service_name=self._service_name,
                environment='auto',
                validate_config=False  # Skip validation for backward compatibility
            )
            
            # Create standard logger as fallback
            self._standard_logger = UCBLLoggerFactory.create_complete_logger(
                logger_name=self._service_name,
                log_level=self._log_level,
                timezone=self._timezone
            )
            
            self._logger_type = 'enhanced'
            
        except Exception as e:
            # Fallback to standard logger on any error
            self._initialize_standard_logger()
            self._initialization_error = str(e)
    
    def _initialize_standard_logger(self) -> None:
        """Initialize standard logger (fallback)"""
        self._standard_logger = UCBLLoggerFactory.create_complete_logger(
            logger_name=self._service_name,
            log_level=self._log_level,
            timezone=self._timezone
        )
        self._enhanced_logger = None
        self._logger_type = 'standard'
        self._initialization_report = None
    
    # Basic logging methods with enhanced EKS integration
    def info(self, msg: str, **kwargs) -> None:
        """Log info message with optional enhanced context"""
        if self._enhanced_logger:
            self._enhanced_logger.info(msg, **kwargs)
        else:
            self._standard_logger.info(msg)
    
    def debug(self, msg: str, **kwargs) -> None:
        """Log debug message with optional enhanced context"""
        if self._enhanced_logger:
            self._enhanced_logger.debug(msg, **kwargs)
        else:
            self._standard_logger.debug(msg)
    
    def warning(self, msg: str, **kwargs) -> None:
        """Log warning message with optional enhanced context"""
        if self._enhanced_logger:
            self._enhanced_logger.warning(msg, **kwargs)
        else:
            self._standard_logger.warning(msg)
    
    def warn(self, msg: str, **kwargs) -> None:
        """Alias for warning method"""
        self.warning(msg, **kwargs)
    
    def error(self, msg: str, **kwargs) -> None:
        """Log error message with optional enhanced context"""
        if self._enhanced_logger:
            self._enhanced_logger.error(msg, **kwargs)
        else:
            self._standard_logger.error(msg)
    
    def critical(self, msg: str, **kwargs) -> None:
        """Log critical message with optional enhanced context"""
        if self._enhanced_logger:
            self._enhanced_logger.critical(msg, **kwargs)
        else:
            self._standard_logger.critical(msg)
    
    # Enhanced task logging methods
    def log_task_start(self, task_name: str, task_type: str = "System", **kwargs) -> Optional[str]:
        """
        Log task start with optional enhanced tracing
        
        Returns:
            Correlation ID if enhanced features are enabled, None otherwise
        """
        if self._enhanced_logger:
            return self._enhanced_logger.log_task_start_enhanced(task_name, task_type, **kwargs)
        else:
            self._standard_logger.log_task_start(task_name, task_type)
            return None
    
    def log_task_stop(self, task_name: str, correlation_id: Optional[str] = None, 
                     success: bool = True, **kwargs) -> None:
        """Log task stop with optional enhanced tracing"""
        if self._enhanced_logger:
            self._enhanced_logger.log_task_stop_enhanced(task_name, correlation_id, success, **kwargs)
        else:
            self._standard_logger.log_task_stop(task_name)
    
    # Enhanced risk logging methods
    def log_risk(self, msg: str, critical=False, minor=False, 
                correlation_id: Optional[str] = None, **kwargs) -> None:
        """Log risk with optional enhanced security context"""
        if self._enhanced_logger:
            self._enhanced_logger.log_risk_enhanced(msg, critical, minor, correlation_id, **kwargs)
        else:
            self._standard_logger.log_risk(msg, critical, minor)
    
    def log_anomaly(self, msg: str, correlation_id: Optional[str] = None, **kwargs) -> None:
        """Log anomaly with optional enhanced performance context"""
        if self._enhanced_logger:
            self._enhanced_logger.log_anomaly_enhanced(msg, correlation_id, **kwargs)
        else:
            self._standard_logger.log_anomaly(msg)
    
    # Backward compatibility methods (simplified versions)
    def log_suspicious_activity(self, msg: str, **kwargs) -> None:
        """Log suspicious activity (backward compatibility)"""
        self.log_anomaly(f"Suspicious: {msg}", **kwargs)
    
    def log_step_start(self, step_name: str, **kwargs) -> Optional[str]:
        """Log step start (backward compatibility)"""
        return self.log_task_start(f"Step: {step_name}", **kwargs)
    
    def log_step_stop(self, step_name: str, correlation_id: Optional[str] = None, **kwargs) -> None:
        """Log step stop (backward compatibility)"""
        self.log_task_stop(f"Step: {step_name}", correlation_id, **kwargs)
    
    # Enhanced-only methods (gracefully degrade if enhanced features not available)
    def start_trace(self, operation_name: str) -> Optional[str]:
        """
        Start distributed trace (enhanced feature)
        
        Returns:
            Correlation ID if enhanced features are enabled, None otherwise
        """
        if self._enhanced_logger:
            return self._enhanced_logger.start_trace(operation_name)
        return None
    
    def end_trace(self, correlation_id: str, success: bool = True, metadata: Optional[Dict[str, Any]] = None) -> None:
        """End distributed trace (enhanced feature)"""
        if self._enhanced_logger:
            self._enhanced_logger.end_trace(correlation_id, success, metadata)
    
    def log_performance_metrics(self) -> None:
        """Log current performance metrics (enhanced feature)"""
        if self._enhanced_logger:
            self._enhanced_logger.log_performance_metrics()
    
    def get_health_status(self) -> Optional[Dict[str, Any]]:
        """
        Get logging system health status (enhanced feature)
        
        Returns:
            Health status dictionary if enhanced features are enabled, None otherwise
        """
        if self._enhanced_logger:
            health_status = self._enhanced_logger.get_health_status()
            return health_status.__dict__ if hasattr(health_status, '__dict__') else {'status': str(health_status)}
        return None
    
    # Configuration and feature management
    def is_enhanced_mode(self) -> bool:
        """Check if enhanced EKS features are enabled"""
        return self._enhanced_logger is not None
    
    def get_logger_info(self) -> Dict[str, Any]:
        """Get information about the current logger configuration"""
        info = {
            'logger_type': self._logger_type,
            'service_name': self._service_name,
            'eks_features_enabled': self._eks_features_enabled,
            'enhanced_available': _enhanced_available
        }
        
        if hasattr(self, '_initialization_error'):
            info['initialization_error'] = self._initialization_error
        
        if self._initialization_report:
            info['initialization_report'] = self._initialization_report
        
        if self._enhanced_logger:
            info['component_status'] = self._enhanced_logger.get_component_status()
        
        return info
    
    def configure_sampling(self, config: Dict[str, Any]) -> bool:
        """
        Configure log sampling (enhanced feature)
        
        Returns:
            True if configuration was applied, False if enhanced features not available
        """
        if self._enhanced_logger:
            self._enhanced_logger.configure_sampling(config)
            return True
        return False
    
    def flush_logs(self) -> None:
        """Flush all buffered logs"""
        if self._enhanced_logger:
            self._enhanced_logger.flush_logs()
    
    # Context manager support
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        if self._enhanced_logger:
            self._enhanced_logger.shutdown()
    
    # Feature flag methods for gradual rollout
    @classmethod
    def create_with_feature_flags(cls, 
                                 service_name: str,
                                 feature_flags: Dict[str, bool],
                                 **kwargs) -> 'UCBLLogger':
        """
        Create logger with specific feature flags for gradual rollout
        
        Args:
            service_name: Service name
            feature_flags: Dictionary of feature flags
            **kwargs: Additional arguments for UCBLLogger
            
        Returns:
            UCBLLogger instance with specified features
        """
        # Convert feature flags to EKS config
        eks_config = {
            'service_name': service_name,
            'features': feature_flags
        }
        
        return cls(
            service_name=service_name,
            enable_eks_features=any(feature_flags.values()),
            eks_config=eks_config,
            **kwargs
        )
    
    @classmethod
    def create_for_environment(cls, 
                              service_name: str,
                              environment: str = 'auto',
                              **kwargs) -> 'UCBLLogger':
        """
        Create logger optimized for specific environment
        
        Args:
            service_name: Service name
            environment: Target environment ('development', 'staging', 'production', 'auto')
            **kwargs: Additional arguments for UCBLLogger
            
        Returns:
            UCBLLogger instance optimized for the environment
        """
        if _enhanced_available:
            try:
                from .enhanced import ConfigurationManager
                config = ConfigurationManager.create_for_environment(environment)
                config.service_name = service_name
                
                return cls(
                    service_name=service_name,
                    enable_eks_features=True,
                    eks_config=config.to_dict(),
                    **kwargs
                )
            except Exception:
                pass  # Fallback to standard logger
        
        return cls(service_name=service_name, enable_eks_features=False, **kwargs)

# Export the main class
__all__ = ['UCBLLogger', 'UCBLLoggerFactory', 'LogLevel']