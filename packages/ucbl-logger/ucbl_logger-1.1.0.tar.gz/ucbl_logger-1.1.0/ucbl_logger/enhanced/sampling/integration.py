"""
Integration of sampling engine with complete logging pipeline
"""

import time
import logging
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from .interfaces import ISamplingEngine, LogLevel
from .advanced_engine import AdvancedSamplingEngine
from .models import SamplingConfig, SamplingDecision


@dataclass
class SamplingIntegrationConfig:
    """Configuration for sampling integration"""
    sampling_config: SamplingConfig
    debug_mode_enabled: bool = False
    statistics_reporting_interval: int = 300  # 5 minutes
    pipeline_integration_points: Dict[str, bool] = field(default_factory=lambda: {
        'pre_format': True,      # Apply sampling before log formatting
        'post_format': False,    # Apply sampling after log formatting
        'pre_output': False,     # Apply sampling before output handlers
        'post_filter': True      # Apply sampling after log filters
    })
    
    # Callback functions for pipeline integration
    on_sample_decision: Optional[Callable[[SamplingDecision, Dict[str, Any]], None]] = None
    on_statistics_update: Optional[Callable[[Dict[str, Any]], None]] = None


class SamplingPipelineIntegrator:
    """
    Integrates sampling engine with the complete logging pipeline
    """
    
    def __init__(self, config: SamplingIntegrationConfig):
        self.config = config
        self.sampling_engine = AdvancedSamplingEngine(config.sampling_config)
        
        # Pipeline state
        self.debug_mode_active = config.debug_mode_enabled
        self.last_statistics_report = time.time()
        
        # Statistics and monitoring
        self.pipeline_statistics = {
            'total_log_entries': 0,
            'pre_format_samples': 0,
            'post_format_samples': 0,
            'pre_output_samples': 0,
            'post_filter_samples': 0,
            'debug_mode_bypasses': 0,
            'sampling_decisions_made': 0
        }
        
        # Integration point handlers
        self.integration_handlers = {
            'pre_format': self._handle_pre_format_sampling,
            'post_format': self._handle_post_format_sampling,
            'pre_output': self._handle_pre_output_sampling,
            'post_filter': self._handle_post_filter_sampling
        }
    
    def process_log_entry(self, log_entry: Dict[str, Any], 
                         integration_point: str) -> tuple[bool, Dict[str, Any]]:
        """
        Process log entry at specified integration point
        
        Returns:
            tuple: (should_continue, updated_log_entry)
        """
        self.pipeline_statistics['total_log_entries'] += 1
        
        # Check if this integration point is enabled
        if not self.config.pipeline_integration_points.get(integration_point, False):
            return True, log_entry
        
        # Handle debug mode
        if self.debug_mode_active:
            self.pipeline_statistics['debug_mode_bypasses'] += 1
            updated_entry = self._add_debug_metadata(log_entry)
            return True, updated_entry
        
        # Get appropriate handler
        handler = self.integration_handlers.get(integration_point)
        if not handler:
            return True, log_entry
        
        # Process through handler
        return handler(log_entry)
    
    def _handle_pre_format_sampling(self, log_entry: Dict[str, Any]) -> tuple[bool, Dict[str, Any]]:
        """Handle sampling before log formatting"""
        log_level = self._extract_log_level(log_entry)
        logger_name = log_entry.get('logger_name', 'unknown')
        
        decision = self.sampling_engine.should_sample(log_level, logger_name)
        self.pipeline_statistics['pre_format_samples'] += 1
        self.pipeline_statistics['sampling_decisions_made'] += 1
        
        # Add sampling metadata to log entry
        updated_entry = self._add_sampling_metadata(log_entry, decision, 'pre_format')
        
        # Trigger callback if configured
        if self.config.on_sample_decision:
            self.config.on_sample_decision(decision, updated_entry)
        
        return decision.should_sample, updated_entry
    
    def _handle_post_format_sampling(self, log_entry: Dict[str, Any]) -> tuple[bool, Dict[str, Any]]:
        """Handle sampling after log formatting"""
        log_level = self._extract_log_level(log_entry)
        logger_name = log_entry.get('logger_name', 'unknown')
        
        decision = self.sampling_engine.should_sample(log_level, logger_name)
        self.pipeline_statistics['post_format_samples'] += 1
        self.pipeline_statistics['sampling_decisions_made'] += 1
        
        # Add sampling metadata
        updated_entry = self._add_sampling_metadata(log_entry, decision, 'post_format')
        
        if self.config.on_sample_decision:
            self.config.on_sample_decision(decision, updated_entry)
        
        return decision.should_sample, updated_entry
    
    def _handle_pre_output_sampling(self, log_entry: Dict[str, Any]) -> tuple[bool, Dict[str, Any]]:
        """Handle sampling before output handlers"""
        log_level = self._extract_log_level(log_entry)
        logger_name = log_entry.get('logger_name', 'unknown')
        
        decision = self.sampling_engine.should_sample(log_level, logger_name)
        self.pipeline_statistics['pre_output_samples'] += 1
        self.pipeline_statistics['sampling_decisions_made'] += 1
        
        # Add sampling metadata
        updated_entry = self._add_sampling_metadata(log_entry, decision, 'pre_output')
        
        if self.config.on_sample_decision:
            self.config.on_sample_decision(decision, updated_entry)
        
        return decision.should_sample, updated_entry
    
    def _handle_post_filter_sampling(self, log_entry: Dict[str, Any]) -> tuple[bool, Dict[str, Any]]:
        """Handle sampling after log filters"""
        log_level = self._extract_log_level(log_entry)
        logger_name = log_entry.get('logger_name', 'unknown')
        
        decision = self.sampling_engine.should_sample(log_level, logger_name)
        self.pipeline_statistics['post_filter_samples'] += 1
        self.pipeline_statistics['sampling_decisions_made'] += 1
        
        # Add sampling metadata
        updated_entry = self._add_sampling_metadata(log_entry, decision, 'post_filter')
        
        if self.config.on_sample_decision:
            self.config.on_sample_decision(decision, updated_entry)
        
        return decision.should_sample, updated_entry
    
    def _extract_log_level(self, log_entry: Dict[str, Any]) -> LogLevel:
        """Extract log level from log entry"""
        level_str = log_entry.get('level', log_entry.get('levelname', 'INFO')).upper()
        
        try:
            return LogLevel(level_str)
        except ValueError:
            # Default to INFO if level is not recognized
            return LogLevel.INFO
    
    def _add_sampling_metadata(self, log_entry: Dict[str, Any], 
                              decision: SamplingDecision, 
                              integration_point: str) -> Dict[str, Any]:
        """Add sampling metadata to log entry"""
        updated_entry = log_entry.copy()
        
        # Add sampling information
        sampling_metadata = {
            'sampling_applied': True,
            'sampling_decision': decision.should_sample,
            'sampling_rate': decision.sampling_rate,
            'sampling_reason': decision.reason,
            'integration_point': integration_point,
            'sampling_metadata': decision.metadata
        }
        
        # Merge with existing metadata or create new
        if 'sampling' in updated_entry:
            updated_entry['sampling'].update(sampling_metadata)
        else:
            updated_entry['sampling'] = sampling_metadata
        
        return updated_entry
    
    def _add_debug_metadata(self, log_entry: Dict[str, Any]) -> Dict[str, Any]:
        """Add debug mode metadata to log entry"""
        updated_entry = log_entry.copy()
        
        debug_metadata = {
            'debug_mode_active': True,
            'sampling_bypassed': True,
            'bypass_reason': 'debug_mode_enabled'
        }
        
        if 'sampling' in updated_entry:
            updated_entry['sampling'].update(debug_metadata)
        else:
            updated_entry['sampling'] = debug_metadata
        
        return updated_entry
    
    def enable_debug_mode(self) -> None:
        """Enable debug mode to disable sampling temporarily"""
        self.debug_mode_active = True
        self.sampling_engine.enable_debug_mode()
    
    def disable_debug_mode(self) -> None:
        """Disable debug mode to re-enable sampling"""
        self.debug_mode_active = False
        self.sampling_engine.disable_debug_mode()
    
    def is_debug_mode_active(self) -> bool:
        """Check if debug mode is currently active"""
        return self.debug_mode_active
    
    def update_sampling_rates(self) -> None:
        """Update sampling rates and trigger statistics reporting if needed"""
        self.sampling_engine.update_sampling_rates()
        
        # Check if we should report statistics
        current_time = time.time()
        if (current_time - self.last_statistics_report >= 
            self.config.statistics_reporting_interval):
            
            self._report_statistics()
            self.last_statistics_report = current_time
    
    def _report_statistics(self) -> None:
        """Report comprehensive sampling statistics"""
        sampling_stats = self.sampling_engine.get_sampling_statistics()
        
        comprehensive_stats = {
            'timestamp': time.time(),
            'pipeline_statistics': self.pipeline_statistics.copy(),
            'sampling_engine_statistics': sampling_stats,
            'debug_mode_active': self.debug_mode_active,
            'integration_points': self.config.pipeline_integration_points.copy()
        }
        
        # Trigger callback if configured
        if self.config.on_statistics_update:
            self.config.on_statistics_update(comprehensive_stats)
    
    def get_pipeline_statistics(self) -> Dict[str, Any]:
        """Get comprehensive pipeline statistics"""
        sampling_stats = self.sampling_engine.get_sampling_statistics()
        
        return {
            'pipeline_statistics': self.pipeline_statistics.copy(),
            'sampling_engine_statistics': sampling_stats,
            'debug_mode_active': self.debug_mode_active,
            'integration_configuration': self.config.pipeline_integration_points.copy(),
            'last_statistics_report': self.last_statistics_report,
            'statistics_reporting_interval': self.config.statistics_reporting_interval
        }
    
    def reset_statistics(self) -> None:
        """Reset all statistics and sampling state"""
        self.pipeline_statistics = {
            'total_log_entries': 0,
            'pre_format_samples': 0,
            'post_format_samples': 0,
            'pre_output_samples': 0,
            'post_filter_samples': 0,
            'debug_mode_bypasses': 0,
            'sampling_decisions_made': 0
        }
        
        self.sampling_engine.reset_sampling_window()
        self.last_statistics_report = time.time()
    
    def configure_integration_points(self, integration_points: Dict[str, bool]) -> None:
        """Update integration point configuration"""
        self.config.pipeline_integration_points.update(integration_points)
    
    def get_sampling_decision_preview(self, log_level: str, logger_name: str = 'preview') -> SamplingDecision:
        """Get a preview of what sampling decision would be made"""
        try:
            level_enum = LogLevel(log_level.upper())
        except ValueError:
            level_enum = LogLevel.INFO
        
        return self.sampling_engine.should_sample(level_enum, logger_name)


class SamplingAwareLogHandler(logging.Handler):
    """
    Log handler that integrates with sampling pipeline
    """
    
    def __init__(self, integrator: SamplingPipelineIntegrator, 
                 integration_point: str = 'pre_output'):
        super().__init__()
        self.integrator = integrator
        self.integration_point = integration_point
    
    def emit(self, record: logging.LogRecord) -> None:
        """Emit log record through sampling pipeline"""
        try:
            # Convert LogRecord to dictionary
            log_entry = {
                'timestamp': record.created,
                'level': record.levelname,
                'levelname': record.levelname,
                'message': record.getMessage(),
                'logger_name': record.name,
                'module': record.module,
                'funcName': record.funcName,
                'lineno': record.lineno,
                'pathname': record.pathname,
                'thread': record.thread,
                'threadName': record.threadName,
                'process': record.process,
                'processName': record.processName
            }
            
            # Add any extra fields
            if hasattr(record, '__dict__'):
                for key, value in record.__dict__.items():
                    if key not in log_entry and not key.startswith('_'):
                        log_entry[key] = value
            
            # Process through sampling pipeline
            should_continue, updated_entry = self.integrator.process_log_entry(
                log_entry, self.integration_point
            )
            
            if should_continue:
                # Update the record with sampling metadata
                if 'sampling' in updated_entry:
                    record.sampling = updated_entry['sampling']
                
                # Continue with normal handler processing
                self._emit_sampled_record(record, updated_entry)
        
        except Exception:
            self.handleError(record)
    
    def _emit_sampled_record(self, record: logging.LogRecord, 
                           updated_entry: Dict[str, Any]) -> None:
        """Emit the sampled record - override in subclasses"""
        # Default implementation - just print
        formatted = self.format(record)
        print(formatted)


def create_sampling_integration(sampling_config: SamplingConfig,
                              debug_mode: bool = False,
                              statistics_callback: Optional[Callable] = None) -> SamplingPipelineIntegrator:
    """
    Factory function to create a sampling integration with sensible defaults
    """
    integration_config = SamplingIntegrationConfig(
        sampling_config=sampling_config,
        debug_mode_enabled=debug_mode,
        on_statistics_update=statistics_callback
    )
    
    return SamplingPipelineIntegrator(integration_config)