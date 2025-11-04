"""
Advanced buffer monitoring and statistics with trend analysis
"""

import time
import threading
from collections import deque, defaultdict
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum


class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class TrendDirection(Enum):
    """Trend direction indicators"""
    INCREASING = "increasing"
    DECREASING = "decreasing"
    STABLE = "stable"
    VOLATILE = "volatile"


@dataclass
class MetricPoint:
    """Single metric measurement point"""
    timestamp: float
    value: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TrendAnalysis:
    """Trend analysis result"""
    direction: TrendDirection
    rate_of_change: float
    confidence: float
    prediction_next_5min: Optional[float] = None
    prediction_next_15min: Optional[float] = None


@dataclass
class BufferAlert:
    """Buffer monitoring alert"""
    alert_id: str
    severity: AlertSeverity
    message: str
    timestamp: float
    metric_name: str
    current_value: float
    threshold_value: float
    trend_info: Optional[TrendAnalysis] = None
    recommendations: List[str] = field(default_factory=list)


class MetricCollector:
    """Collects and stores time-series metrics"""
    
    def __init__(self, max_history_points: int = 1000):
        self.max_history_points = max_history_points
        self.metrics = defaultdict(lambda: deque(maxlen=max_history_points))
        self._lock = threading.Lock()
    
    def record_metric(self, name: str, value: float, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Record a metric value"""
        point = MetricPoint(
            timestamp=time.time(),
            value=value,
            metadata=metadata or {}
        )
        
        with self._lock:
            self.metrics[name].append(point)
    
    def get_metric_history(self, name: str, duration_seconds: Optional[float] = None) -> List[MetricPoint]:
        """Get metric history for specified duration"""
        with self._lock:
            if name not in self.metrics:
                return []
            
            points = list(self.metrics[name])
        
        if duration_seconds is None:
            return points
        
        cutoff_time = time.time() - duration_seconds
        return [p for p in points if p.timestamp >= cutoff_time]
    
    def get_latest_value(self, name: str) -> Optional[float]:
        """Get the latest value for a metric"""
        with self._lock:
            if name not in self.metrics or not self.metrics[name]:
                return None
            return self.metrics[name][-1].value
    
    def get_metric_names(self) -> List[str]:
        """Get all available metric names"""
        with self._lock:
            return list(self.metrics.keys())


class TrendAnalyzer:
    """Analyzes trends in time-series data"""
    
    def __init__(self):
        self.min_points_for_analysis = 10
    
    def analyze_trend(self, points: List[MetricPoint]) -> TrendAnalysis:
        """Analyze trend in metric points"""
        if len(points) < self.min_points_for_analysis:
            return TrendAnalysis(
                direction=TrendDirection.STABLE,
                rate_of_change=0.0,
                confidence=0.0
            )
        
        # Calculate linear regression for trend
        x_values = [p.timestamp for p in points]
        y_values = [p.value for p in points]
        
        slope, confidence = self._calculate_linear_regression(x_values, y_values)
        
        # Determine trend direction
        if abs(slope) < 0.001:  # Very small slope
            direction = TrendDirection.STABLE
        elif slope > 0:
            direction = TrendDirection.INCREASING
        else:
            direction = TrendDirection.DECREASING
        
        # Check for volatility
        volatility = self._calculate_volatility(y_values)
        if volatility > 0.5:  # High volatility threshold
            direction = TrendDirection.VOLATILE
        
        # Make predictions
        latest_time = points[-1].timestamp
        prediction_5min = self._predict_value(slope, points[-1].value, 300)  # 5 minutes
        prediction_15min = self._predict_value(slope, points[-1].value, 900)  # 15 minutes
        
        return TrendAnalysis(
            direction=direction,
            rate_of_change=slope,
            confidence=confidence,
            prediction_next_5min=prediction_5min,
            prediction_next_15min=prediction_15min
        )
    
    def _calculate_linear_regression(self, x_values: List[float], y_values: List[float]) -> tuple[float, float]:
        """Calculate linear regression slope and confidence"""
        n = len(x_values)
        if n < 2:
            return 0.0, 0.0
        
        # Normalize x values to prevent numerical issues
        x_min = min(x_values)
        x_norm = [(x - x_min) for x in x_values]
        
        sum_x = sum(x_norm)
        sum_y = sum(y_values)
        sum_xy = sum(x * y for x, y in zip(x_norm, y_values))
        sum_x2 = sum(x * x for x in x_norm)
        
        # Calculate slope
        denominator = n * sum_x2 - sum_x * sum_x
        if abs(denominator) < 1e-10:
            return 0.0, 0.0
        
        slope = (n * sum_xy - sum_x * sum_y) / denominator
        
        # Calculate R-squared for confidence
        y_mean = sum_y / n
        ss_tot = sum((y - y_mean) ** 2 for y in y_values)
        
        if ss_tot == 0:
            confidence = 1.0
        else:
            intercept = (sum_y - slope * sum_x) / n
            ss_res = sum((y - (slope * x + intercept)) ** 2 for x, y in zip(x_norm, y_values))
            confidence = max(0.0, 1.0 - (ss_res / ss_tot))
        
        return slope, confidence
    
    def _calculate_volatility(self, values: List[float]) -> float:
        """Calculate volatility (coefficient of variation)"""
        if len(values) < 2:
            return 0.0
        
        mean_val = sum(values) / len(values)
        if mean_val == 0:
            return 0.0
        
        variance = sum((v - mean_val) ** 2 for v in values) / len(values)
        std_dev = variance ** 0.5
        
        return std_dev / abs(mean_val)
    
    def _predict_value(self, slope: float, current_value: float, time_delta_seconds: float) -> float:
        """Predict future value based on trend"""
        return current_value + (slope * time_delta_seconds)


class ThresholdMonitor:
    """Monitors metrics against configurable thresholds"""
    
    def __init__(self):
        self.thresholds = {}
        self.alert_history = deque(maxlen=1000)
        self._alert_counter = 0
        self._lock = threading.Lock()
    
    def set_threshold(self, metric_name: str, warning_threshold: float, 
                     critical_threshold: float, check_direction: str = "above") -> None:
        """Set thresholds for a metric"""
        self.thresholds[metric_name] = {
            'warning': warning_threshold,
            'critical': critical_threshold,
            'direction': check_direction  # "above" or "below"
        }
    
    def check_thresholds(self, metric_name: str, current_value: float, 
                        trend_analysis: Optional[TrendAnalysis] = None) -> List[BufferAlert]:
        """Check if metric value exceeds thresholds"""
        if metric_name not in self.thresholds:
            return []
        
        threshold_config = self.thresholds[metric_name]
        alerts = []
        
        # Check current value against thresholds
        if threshold_config['direction'] == "above":
            if current_value >= threshold_config['critical']:
                alerts.append(self._create_alert(
                    metric_name, current_value, threshold_config['critical'],
                    AlertSeverity.CRITICAL, "above", trend_analysis
                ))
            elif current_value >= threshold_config['warning']:
                alerts.append(self._create_alert(
                    metric_name, current_value, threshold_config['warning'],
                    AlertSeverity.WARNING, "above", trend_analysis
                ))
        else:  # "below"
            if current_value <= threshold_config['critical']:
                alerts.append(self._create_alert(
                    metric_name, current_value, threshold_config['critical'],
                    AlertSeverity.CRITICAL, "below", trend_analysis
                ))
            elif current_value <= threshold_config['warning']:
                alerts.append(self._create_alert(
                    metric_name, current_value, threshold_config['warning'],
                    AlertSeverity.WARNING, "below", trend_analysis
                ))
        
        # Check trend-based predictions
        if trend_analysis and trend_analysis.prediction_next_5min is not None:
            predicted_alerts = self._check_predicted_thresholds(
                metric_name, trend_analysis.prediction_next_5min, threshold_config, trend_analysis
            )
            alerts.extend(predicted_alerts)
        
        # Store alerts
        with self._lock:
            for alert in alerts:
                self.alert_history.append(alert)
        
        return alerts
    
    def _create_alert(self, metric_name: str, current_value: float, threshold_value: float,
                     severity: AlertSeverity, direction: str, trend_analysis: Optional[TrendAnalysis]) -> BufferAlert:
        """Create a buffer alert"""
        with self._lock:
            self._alert_counter += 1
            alert_id = f"alert_{self._alert_counter}_{int(time.time())}"
        
        message = f"{metric_name} is {direction} {direction} threshold: {current_value:.2f} vs {threshold_value:.2f}"
        
        recommendations = self._get_recommendations(metric_name, severity, trend_analysis)
        
        return BufferAlert(
            alert_id=alert_id,
            severity=severity,
            message=message,
            timestamp=time.time(),
            metric_name=metric_name,
            current_value=current_value,
            threshold_value=threshold_value,
            trend_info=trend_analysis,
            recommendations=recommendations
        )
    
    def _check_predicted_thresholds(self, metric_name: str, predicted_value: float,
                                   threshold_config: Dict[str, Any], trend_analysis: TrendAnalysis) -> List[BufferAlert]:
        """Check if predicted values will exceed thresholds"""
        alerts = []
        
        if threshold_config['direction'] == "above":
            if predicted_value >= threshold_config['critical']:
                alert = self._create_predictive_alert(
                    metric_name, predicted_value, threshold_config['critical'],
                    AlertSeverity.WARNING, "predicted to exceed", trend_analysis
                )
                alerts.append(alert)
        
        return alerts
    
    def _create_predictive_alert(self, metric_name: str, predicted_value: float, threshold_value: float,
                               severity: AlertSeverity, message_type: str, trend_analysis: TrendAnalysis) -> BufferAlert:
        """Create a predictive alert"""
        with self._lock:
            self._alert_counter += 1
            alert_id = f"predictive_alert_{self._alert_counter}_{int(time.time())}"
        
        message = f"{metric_name} {message_type} critical threshold in 5 minutes: {predicted_value:.2f} vs {threshold_value:.2f}"
        
        recommendations = [
            "Take proactive action to prevent threshold breach",
            "Monitor trend closely",
            "Consider scaling resources if applicable"
        ]
        
        return BufferAlert(
            alert_id=alert_id,
            severity=severity,
            message=message,
            timestamp=time.time(),
            metric_name=metric_name,
            current_value=predicted_value,
            threshold_value=threshold_value,
            trend_info=trend_analysis,
            recommendations=recommendations
        )
    
    def _get_recommendations(self, metric_name: str, severity: AlertSeverity, 
                           trend_analysis: Optional[TrendAnalysis]) -> List[str]:
        """Get recommendations based on metric and severity"""
        recommendations = []
        
        if metric_name == "buffer_usage_percent":
            if severity == AlertSeverity.CRITICAL:
                recommendations.extend([
                    "Immediately flush buffer to prevent data loss",
                    "Check log delivery destinations for issues",
                    "Consider dropping non-critical logs temporarily"
                ])
            else:
                recommendations.extend([
                    "Monitor buffer usage closely",
                    "Check for delivery delays",
                    "Consider increasing flush frequency"
                ])
        
        elif metric_name == "memory_usage_percent":
            if severity == AlertSeverity.CRITICAL:
                recommendations.extend([
                    "Clear non-essential buffers immediately",
                    "Reduce log verbosity",
                    "Check for memory leaks"
                ])
            else:
                recommendations.extend([
                    "Monitor memory usage trend",
                    "Consider reducing buffer sizes",
                    "Check for gradual memory increases"
                ])
        
        elif metric_name == "failure_rate":
            recommendations.extend([
                "Check network connectivity",
                "Verify authentication credentials",
                "Check destination service status"
            ])
        
        # Add trend-based recommendations
        if trend_analysis:
            if trend_analysis.direction == TrendDirection.INCREASING:
                recommendations.append("Trend is increasing - take action soon")
            elif trend_analysis.direction == TrendDirection.VOLATILE:
                recommendations.append("Metric is volatile - investigate root cause")
        
        return recommendations
    
    def get_recent_alerts(self, duration_seconds: float = 3600) -> List[BufferAlert]:
        """Get recent alerts within specified duration"""
        cutoff_time = time.time() - duration_seconds
        
        with self._lock:
            return [alert for alert in self.alert_history if alert.timestamp >= cutoff_time]


class BufferMonitor:
    """Comprehensive buffer monitoring with trend analysis and proactive alerting"""
    
    def __init__(self):
        self.metric_collector = MetricCollector()
        self.trend_analyzer = TrendAnalyzer()
        self.threshold_monitor = ThresholdMonitor()
        
        # Set default thresholds
        self._setup_default_thresholds()
        
        # Monitoring state
        self._monitoring_active = False
        self._monitoring_thread = None
        self._monitoring_interval = 30.0  # 30 seconds
        
    def _setup_default_thresholds(self) -> None:
        """Setup default monitoring thresholds"""
        self.threshold_monitor.set_threshold("buffer_usage_percent", 80.0, 95.0, "above")
        self.threshold_monitor.set_threshold("memory_usage_percent", 80.0, 95.0, "above")
        self.threshold_monitor.set_threshold("failure_rate", 5.0, 10.0, "above")
        self.threshold_monitor.set_threshold("retry_queue_size", 100.0, 500.0, "above")
        self.threshold_monitor.set_threshold("delivery_success_rate", 90.0, 80.0, "below")
    
    def record_buffer_metrics(self, buffer_stats: Dict[str, Any]) -> None:
        """Record buffer metrics for monitoring"""
        current_time = time.time()
        
        # Extract and record key metrics
        if 'buffer_usage_percent' in buffer_stats:
            self.metric_collector.record_metric("buffer_usage_percent", buffer_stats['buffer_usage_percent'])
        
        if 'memory_pressure' in buffer_stats and 'usage' in buffer_stats['memory_pressure']:
            memory_usage = buffer_stats['memory_pressure']['usage'] * 100
            self.metric_collector.record_metric("memory_usage_percent", memory_usage)
        
        if 'delivery_stats' in buffer_stats:
            delivery_stats = buffer_stats['delivery_stats']
            total_deliveries = delivery_stats.get('successful_deliveries', 0) + delivery_stats.get('failed_deliveries', 0)
            
            if total_deliveries > 0:
                success_rate = (delivery_stats.get('successful_deliveries', 0) / total_deliveries) * 100
                self.metric_collector.record_metric("delivery_success_rate", success_rate)
            
            self.metric_collector.record_metric("failure_rate", delivery_stats.get('failed_deliveries', 0))
        
        if 'retry_queue' in buffer_stats:
            retry_size = buffer_stats['retry_queue'].get('queue_size', 0)
            self.metric_collector.record_metric("retry_queue_size", retry_size)
    
    def analyze_trends_and_check_thresholds(self) -> Dict[str, Any]:
        """Analyze trends and check thresholds for all metrics"""
        results = {
            'trends': {},
            'alerts': [],
            'summary': {}
        }
        
        metric_names = self.metric_collector.get_metric_names()
        
        for metric_name in metric_names:
            # Get recent history for trend analysis
            history = self.metric_collector.get_metric_history(metric_name, 3600)  # Last hour
            
            if len(history) >= 2:
                # Analyze trend
                trend_analysis = self.trend_analyzer.analyze_trend(history)
                results['trends'][metric_name] = {
                    'direction': trend_analysis.direction.value,
                    'rate_of_change': trend_analysis.rate_of_change,
                    'confidence': trend_analysis.confidence,
                    'prediction_5min': trend_analysis.prediction_next_5min,
                    'prediction_15min': trend_analysis.prediction_next_15min
                }
                
                # Check thresholds
                current_value = history[-1].value
                alerts = self.threshold_monitor.check_thresholds(metric_name, current_value, trend_analysis)
                results['alerts'].extend(alerts)
        
        # Generate summary
        results['summary'] = self._generate_monitoring_summary(results)
        
        return results
    
    def _generate_monitoring_summary(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate monitoring summary"""
        critical_alerts = [a for a in analysis_results['alerts'] if a.severity == AlertSeverity.CRITICAL]
        warning_alerts = [a for a in analysis_results['alerts'] if a.severity == AlertSeverity.WARNING]
        
        increasing_trends = [
            name for name, trend in analysis_results['trends'].items()
            if trend['direction'] == TrendDirection.INCREASING.value
        ]
        
        return {
            'total_alerts': len(analysis_results['alerts']),
            'critical_alerts': len(critical_alerts),
            'warning_alerts': len(warning_alerts),
            'metrics_with_increasing_trends': len(increasing_trends),
            'overall_health': self._calculate_overall_health(critical_alerts, warning_alerts, increasing_trends),
            'top_concerns': self._identify_top_concerns(analysis_results)
        }
    
    def _calculate_overall_health(self, critical_alerts: List[BufferAlert], 
                                warning_alerts: List[BufferAlert], increasing_trends: List[str]) -> str:
        """Calculate overall health status"""
        if len(critical_alerts) > 0:
            return "critical"
        elif len(warning_alerts) > 2 or len(increasing_trends) > 3:
            return "warning"
        elif len(warning_alerts) > 0 or len(increasing_trends) > 0:
            return "attention"
        else:
            return "healthy"
    
    def _identify_top_concerns(self, analysis_results: Dict[str, Any]) -> List[str]:
        """Identify top concerns from analysis"""
        concerns = []
        
        # Check for critical alerts
        critical_alerts = [a for a in analysis_results['alerts'] if a.severity == AlertSeverity.CRITICAL]
        for alert in critical_alerts[:3]:  # Top 3 critical alerts
            concerns.append(f"CRITICAL: {alert.message}")
        
        # Check for concerning trends
        for metric_name, trend in analysis_results['trends'].items():
            if trend['direction'] == TrendDirection.INCREASING.value and trend['confidence'] > 0.7:
                if trend.get('prediction_5min', 0) > self.metric_collector.get_latest_value(metric_name) * 1.2:
                    concerns.append(f"TREND: {metric_name} increasing rapidly")
        
        return concerns[:5]  # Return top 5 concerns
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive data for monitoring dashboard"""
        analysis = self.analyze_trends_and_check_thresholds()
        recent_alerts = self.threshold_monitor.get_recent_alerts(3600)  # Last hour
        
        # Get current values for key metrics
        current_metrics = {}
        for metric_name in self.metric_collector.get_metric_names():
            current_metrics[metric_name] = self.metric_collector.get_latest_value(metric_name)
        
        return {
            'current_metrics': current_metrics,
            'trend_analysis': analysis['trends'],
            'active_alerts': [
                {
                    'id': alert.alert_id,
                    'severity': alert.severity.value,
                    'message': alert.message,
                    'metric': alert.metric_name,
                    'timestamp': alert.timestamp,
                    'recommendations': alert.recommendations
                }
                for alert in analysis['alerts']
            ],
            'recent_alerts_count': len(recent_alerts),
            'summary': analysis['summary'],
            'health_status': analysis['summary']['overall_health']
        }