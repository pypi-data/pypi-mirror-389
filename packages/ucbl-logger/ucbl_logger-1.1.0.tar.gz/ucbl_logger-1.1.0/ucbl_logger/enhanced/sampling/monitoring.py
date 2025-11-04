"""
Comprehensive monitoring and reporting for sampling system
"""

import time
import json
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from collections import defaultdict, deque
from .integration import SamplingPipelineIntegrator


@dataclass
class SamplingAlert:
    """Represents a sampling-related alert"""
    alert_type: str  # 'high_drop_rate', 'sampling_ineffective', 'volume_spike', etc.
    severity: str    # 'info', 'warning', 'critical'
    message: str
    timestamp: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SamplingReport:
    """Comprehensive sampling report"""
    report_id: str
    timestamp: float
    time_period: float  # seconds
    summary: Dict[str, Any]
    detailed_statistics: Dict[str, Any]
    alerts: List[SamplingAlert]
    recommendations: List[str]


class SamplingMonitor:
    """
    Comprehensive monitoring system for sampling operations
    """
    
    def __init__(self, integrator: SamplingPipelineIntegrator):
        self.integrator = integrator
        
        # Monitoring configuration
        self.monitoring_enabled = True
        self.alert_thresholds = {
            'high_drop_rate': 0.8,      # Alert if >80% logs are dropped
            'low_sampling_rate': 0.1,    # Alert if sampling rate <10%
            'volume_spike_factor': 5.0,  # Alert if volume >5x normal
            'ineffective_adjustment': 3  # Alert after 3 ineffective adjustments
        }
        
        # Historical data for trend analysis
        self.historical_reports: deque[SamplingReport] = deque(maxlen=100)
        self.volume_trend_data: deque[tuple[float, int]] = deque(maxlen=1000)
        self.rate_trend_data: deque[tuple[float, float]] = deque(maxlen=1000)
        
        # Alert management
        self.active_alerts: List[SamplingAlert] = []
        self.alert_history: deque[SamplingAlert] = deque(maxlen=500)
        self.alert_callbacks: List[Callable[[SamplingAlert], None]] = []
        
        # Performance tracking
        self.performance_metrics = {
            'monitoring_overhead_ms': deque(maxlen=100),
            'report_generation_time_ms': deque(maxlen=50),
            'alert_processing_time_ms': deque(maxlen=100)
        }
        
        # Last monitoring cycle
        self.last_monitoring_cycle = time.time()
        self.monitoring_interval = 60.0  # 1 minute
    
    def add_alert_callback(self, callback: Callable[[SamplingAlert], None]) -> None:
        """Add callback function for alert notifications"""
        self.alert_callbacks.append(callback)
    
    def remove_alert_callback(self, callback: Callable[[SamplingAlert], None]) -> None:
        """Remove alert callback function"""
        if callback in self.alert_callbacks:
            self.alert_callbacks.remove(callback)
    
    def update_alert_thresholds(self, thresholds: Dict[str, float]) -> None:
        """Update alert threshold configuration"""
        self.alert_thresholds.update(thresholds)
    
    def run_monitoring_cycle(self) -> Optional[SamplingReport]:
        """Run a complete monitoring cycle"""
        if not self.monitoring_enabled:
            return None
        
        start_time = time.time()
        current_time = time.time()
        
        # Check if it's time for monitoring cycle
        if current_time - self.last_monitoring_cycle < self.monitoring_interval:
            return None
        
        try:
            # Collect current statistics
            stats = self.integrator.get_pipeline_statistics()
            
            # Update trend data
            self._update_trend_data(stats)
            
            # Generate alerts
            alerts = self._generate_alerts(stats)
            
            # Process alerts
            for alert in alerts:
                self._process_alert(alert)
            
            # Generate comprehensive report
            report = self._generate_report(stats, alerts)
            
            # Store report
            self.historical_reports.append(report)
            
            # Update last monitoring cycle
            self.last_monitoring_cycle = current_time
            
            # Track performance
            monitoring_time = (time.time() - start_time) * 1000
            self.performance_metrics['monitoring_overhead_ms'].append(monitoring_time)
            
            return report
        
        except Exception as e:
            # Create error alert
            error_alert = SamplingAlert(
                alert_type='monitoring_error',
                severity='critical',
                message=f"Monitoring cycle failed: {str(e)}",
                timestamp=current_time,
                metadata={'error_type': type(e).__name__}
            )
            self._process_alert(error_alert)
            return None
    
    def _update_trend_data(self, stats: Dict[str, Any]) -> None:
        """Update trend data for analysis"""
        current_time = time.time()
        
        # Extract volume data
        sampling_stats = stats.get('sampling_engine_statistics', {})
        current_volume = sampling_stats.get('current_window_volume', 0)
        current_rate = sampling_stats.get('current_adaptive_rate', 1.0)
        
        # Update trend data
        self.volume_trend_data.append((current_time, current_volume))
        self.rate_trend_data.append((current_time, current_rate))
    
    def _generate_alerts(self, stats: Dict[str, Any]) -> List[SamplingAlert]:
        """Generate alerts based on current statistics"""
        alerts = []
        current_time = time.time()
        
        sampling_stats = stats.get('sampling_engine_statistics', {})
        pipeline_stats = stats.get('pipeline_statistics', {})
        
        # Check drop rate
        total_logs = sampling_stats.get('statistics', {}).get('total_logs', 0)
        dropped_logs = sampling_stats.get('statistics', {}).get('dropped_logs', 0)
        
        if total_logs > 0:
            drop_rate = dropped_logs / total_logs
            if drop_rate > self.alert_thresholds['high_drop_rate']:
                alerts.append(SamplingAlert(
                    alert_type='high_drop_rate',
                    severity='warning' if drop_rate < 0.9 else 'critical',
                    message=f"High log drop rate detected: {drop_rate:.2%}",
                    timestamp=current_time,
                    metadata={'drop_rate': drop_rate, 'total_logs': total_logs}
                ))
        
        # Check sampling rate
        current_rate = sampling_stats.get('current_adaptive_rate', 1.0)
        if current_rate < self.alert_thresholds['low_sampling_rate']:
            alerts.append(SamplingAlert(
                alert_type='low_sampling_rate',
                severity='info',
                message=f"Low sampling rate: {current_rate:.2%}",
                timestamp=current_time,
                metadata={'sampling_rate': current_rate}
            ))
        
        # Check volume spikes
        current_volume = sampling_stats.get('current_window_volume', 0)
        if len(self.volume_trend_data) > 10:
            recent_volumes = [vol for _, vol in list(self.volume_trend_data)[-10:]]
            avg_volume = sum(recent_volumes[:-1]) / max(1, len(recent_volumes) - 1)
            
            if avg_volume > 0 and current_volume > avg_volume * self.alert_thresholds['volume_spike_factor']:
                alerts.append(SamplingAlert(
                    alert_type='volume_spike',
                    severity='warning',
                    message=f"Volume spike detected: {current_volume} (avg: {avg_volume:.0f})",
                    timestamp=current_time,
                    metadata={
                        'current_volume': current_volume,
                        'average_volume': avg_volume,
                        'spike_factor': current_volume / avg_volume
                    }
                ))
        
        # Check adjustment effectiveness
        dynamic_stats = sampling_stats.get('dynamic_adjustment', {})
        avg_effectiveness = dynamic_stats.get('average_effectiveness', 1.0)
        
        if avg_effectiveness < 0.3:  # Less than 30% effective
            alerts.append(SamplingAlert(
                alert_type='ineffective_adjustment',
                severity='warning',
                message=f"Low adjustment effectiveness: {avg_effectiveness:.2%}",
                timestamp=current_time,
                metadata={'effectiveness': avg_effectiveness}
            ))
        
        return alerts
    
    def _process_alert(self, alert: SamplingAlert) -> None:
        """Process and distribute alert"""
        # Add to active alerts if not already present
        if not any(a.alert_type == alert.alert_type and 
                  abs(a.timestamp - alert.timestamp) < 300  # 5 minutes
                  for a in self.active_alerts):
            self.active_alerts.append(alert)
        
        # Add to history
        self.alert_history.append(alert)
        
        # Trigger callbacks
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception:
                pass  # Don't let callback errors break monitoring
    
    def _generate_report(self, stats: Dict[str, Any], alerts: List[SamplingAlert]) -> SamplingReport:
        """Generate comprehensive sampling report"""
        start_time = time.time()
        current_time = time.time()
        
        # Calculate time period
        time_period = current_time - self.last_monitoring_cycle
        
        # Generate summary
        summary = self._generate_summary(stats, time_period)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(stats, alerts)
        
        # Create report
        report = SamplingReport(
            report_id=f"sampling_report_{int(current_time)}",
            timestamp=current_time,
            time_period=time_period,
            summary=summary,
            detailed_statistics=stats,
            alerts=alerts,
            recommendations=recommendations
        )
        
        # Track performance
        report_time = (time.time() - start_time) * 1000
        self.performance_metrics['report_generation_time_ms'].append(report_time)
        
        return report
    
    def _generate_summary(self, stats: Dict[str, Any], time_period: float) -> Dict[str, Any]:
        """Generate summary statistics"""
        sampling_stats = stats.get('sampling_engine_statistics', {})
        pipeline_stats = stats.get('pipeline_statistics', {})
        
        # Calculate rates and efficiency
        total_logs = sampling_stats.get('statistics', {}).get('total_logs', 0)
        sampled_logs = sampling_stats.get('statistics', {}).get('sampled_logs', 0)
        dropped_logs = sampling_stats.get('statistics', {}).get('dropped_logs', 0)
        
        sampling_efficiency = sampled_logs / max(1, total_logs)
        drop_rate = dropped_logs / max(1, total_logs)
        
        # Calculate throughput
        logs_per_second = total_logs / max(1, time_period)
        
        return {
            'time_period_seconds': time_period,
            'total_logs_processed': total_logs,
            'logs_per_second': logs_per_second,
            'sampling_efficiency': sampling_efficiency,
            'drop_rate': drop_rate,
            'current_sampling_rate': sampling_stats.get('current_adaptive_rate', 1.0),
            'current_volume': sampling_stats.get('current_window_volume', 0),
            'debug_mode_active': stats.get('debug_mode_active', False),
            'alerts_generated': len(self.active_alerts)
        }
    
    def _generate_recommendations(self, stats: Dict[str, Any], 
                                alerts: List[SamplingAlert]) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        sampling_stats = stats.get('sampling_engine_statistics', {})
        
        # Check if sampling is too aggressive
        drop_rate = (sampling_stats.get('statistics', {}).get('dropped_logs', 0) / 
                    max(1, sampling_stats.get('statistics', {}).get('total_logs', 1)))
        
        if drop_rate > 0.9:
            recommendations.append(
                "Consider increasing minimum sampling rate - current drop rate is very high"
            )
        
        # Check volume patterns
        current_volume = sampling_stats.get('current_window_volume', 0)
        volume_threshold = sampling_stats.get('volume_threshold', 1000)
        
        if current_volume > volume_threshold * 3:
            recommendations.append(
                "Consider increasing volume thresholds or implementing more aggressive sampling"
            )
        
        # Check adjustment effectiveness
        dynamic_stats = sampling_stats.get('dynamic_adjustment', {})
        effectiveness = dynamic_stats.get('average_effectiveness', 1.0)
        
        if effectiveness < 0.3:
            recommendations.append(
                "Sampling adjustments appear ineffective - consider tuning adjustment parameters"
            )
        
        # Check for debug mode
        if stats.get('debug_mode_active', False):
            recommendations.append(
                "Debug mode is active - sampling is disabled"
            )
        
        # Alert-based recommendations
        for alert in alerts:
            if alert.alert_type == 'volume_spike':
                recommendations.append(
                    "Volume spike detected - consider implementing spike detection patterns"
                )
            elif alert.alert_type == 'high_drop_rate':
                recommendations.append(
                    "High drop rate - consider adjusting sampling strategy or thresholds"
                )
        
        return recommendations
    
    def get_monitoring_dashboard_data(self) -> Dict[str, Any]:
        """Get data for monitoring dashboard"""
        current_stats = self.integrator.get_pipeline_statistics()
        
        # Calculate trend data
        volume_trend = list(self.volume_trend_data)[-50:]  # Last 50 data points
        rate_trend = list(self.rate_trend_data)[-50:]
        
        # Get recent alerts
        recent_alerts = [
            {
                'type': alert.alert_type,
                'severity': alert.severity,
                'message': alert.message,
                'timestamp': alert.timestamp
            }
            for alert in list(self.alert_history)[-10:]  # Last 10 alerts
        ]
        
        # Performance metrics
        avg_monitoring_overhead = (
            sum(self.performance_metrics['monitoring_overhead_ms']) / 
            max(1, len(self.performance_metrics['monitoring_overhead_ms']))
        )
        
        return {
            'current_statistics': current_stats,
            'volume_trend': [{'timestamp': t, 'volume': v} for t, v in volume_trend],
            'rate_trend': [{'timestamp': t, 'rate': r} for t, r in rate_trend],
            'recent_alerts': recent_alerts,
            'active_alerts_count': len(self.active_alerts),
            'monitoring_performance': {
                'average_overhead_ms': avg_monitoring_overhead,
                'monitoring_enabled': self.monitoring_enabled,
                'monitoring_interval': self.monitoring_interval
            },
            'alert_thresholds': self.alert_thresholds.copy()
        }
    
    def export_report(self, report: SamplingReport, format_type: str = 'json') -> str:
        """Export report in specified format"""
        if format_type == 'json':
            return json.dumps({
                'report_id': report.report_id,
                'timestamp': report.timestamp,
                'time_period': report.time_period,
                'summary': report.summary,
                'alerts': [
                    {
                        'type': alert.alert_type,
                        'severity': alert.severity,
                        'message': alert.message,
                        'timestamp': alert.timestamp,
                        'metadata': alert.metadata
                    }
                    for alert in report.alerts
                ],
                'recommendations': report.recommendations
            }, indent=2)
        
        elif format_type == 'text':
            lines = [
                f"Sampling Report - {report.report_id}",
                f"Generated: {time.ctime(report.timestamp)}",
                f"Time Period: {report.time_period:.1f} seconds",
                "",
                "SUMMARY:",
                f"  Total Logs: {report.summary.get('total_logs_processed', 0)}",
                f"  Sampling Efficiency: {report.summary.get('sampling_efficiency', 0):.2%}",
                f"  Drop Rate: {report.summary.get('drop_rate', 0):.2%}",
                f"  Current Rate: {report.summary.get('current_sampling_rate', 0):.2%}",
                "",
                "ALERTS:",
            ]
            
            for alert in report.alerts:
                lines.append(f"  [{alert.severity.upper()}] {alert.message}")
            
            if report.recommendations:
                lines.extend(["", "RECOMMENDATIONS:"])
                for rec in report.recommendations:
                    lines.append(f"  - {rec}")
            
            return "\n".join(lines)
        
        else:
            raise ValueError(f"Unsupported format: {format_type}")
    
    def clear_active_alerts(self) -> None:
        """Clear all active alerts"""
        self.active_alerts.clear()
    
    def enable_monitoring(self) -> None:
        """Enable monitoring system"""
        self.monitoring_enabled = True
    
    def disable_monitoring(self) -> None:
        """Disable monitoring system"""
        self.monitoring_enabled = False