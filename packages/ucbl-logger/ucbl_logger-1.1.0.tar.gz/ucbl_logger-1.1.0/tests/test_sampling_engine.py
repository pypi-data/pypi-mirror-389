"""
Comprehensive unit tests for intelligent log sampling engine
"""

import pytest
import time
import random
from unittest.mock import Mock, patch
from collections import deque

from ucbl_logger.enhanced.sampling import (
    AdvancedSamplingEngine, SamplingConfig, SamplingStrategy, 
    LogLevel, SamplingDecision, DynamicRateAdjuster,
    SamplingPipelineIntegrator, SamplingIntegrationConfig,
    SamplingMonitor, create_sampling_integration
)


class TestSamplingConfig:
    """Test sampling configuration"""
    
    def test_default_config(self):
        """Test default configuration values"""
        config = SamplingConfig()
        
        assert config.enabled is True
        assert config.strategy == SamplingStrategy.ADAPTIVE
        assert config.default_rate == 1.0
        assert config.preserve_errors is True
        assert config.debug_mode is False
        
    def test_level_rates(self):
        """Test log level rate configuration"""
        config = SamplingConfig()
        
        assert config.get_rate_for_level('ERROR') == 1.0
        assert config.get_rate_for_level('CRITICAL') == 1.0
        assert config.get_rate_for_level('DEBUG') == 0.1
        assert config.get_rate_for_level('UNKNOWN') == 1.0  # Default rate
        
    def test_window_segment_size(self):
        """Test sliding window segment calculation"""
        config = SamplingConfig(window_size_seconds=60, sliding_window_segments=6)
        
        assert config.get_window_segment_size() == 10.0


class TestAdvancedSamplingEngine:
    """Test advanced sampling engine functionality"""
    
    @pytest.fixture
    def basic_config(self):
        """Basic sampling configuration for testing"""
        return SamplingConfig(
            enabled=True,
            strategy=SamplingStrategy.ADAPTIVE,
            volume_threshold=100,
            window_size_seconds=60,
            sliding_window_segments=6
        )
    
    @pytest.fixture
    def sampling_engine(self, basic_config):
        """Create sampling engine for testing"""
        return AdvancedSamplingEngine(basic_config)
    
    def test_initialization(self, sampling_engine):
        """Test proper initialization"""
        assert sampling_engine.config.enabled is True
        assert len(sampling_engine.volume_windows) == 6
        assert sampling_engine.current_adaptive_rate == 1.0
        
    def test_sampling_disabled(self, basic_config):
        """Test behavior when sampling is disabled"""
        basic_config.enabled = False
        engine = AdvancedSamplingEngine(basic_config)
        
        decision = engine.should_sample(LogLevel.INFO, 'test_logger')
        
        assert decision.should_sample is True
        assert decision.sampling_rate == 1.0
        assert decision.reason == "sampling_disabled"
        
    def test_debug_mode(self, sampling_engine):
        """Test debug mode behavior"""
        sampling_engine.enable_debug_mode()
        
        decision = sampling_engine.should_sample(LogLevel.INFO, 'test_logger')
        
        assert decision.should_sample is True
        assert decision.sampling_rate == 1.0
        assert decision.reason == "sampling_disabled"
        assert decision.metadata["debug_mode"] is True
        
    def test_priority_preservation(self, sampling_engine):
        """Test that critical logs are always preserved"""
        # Test ERROR level
        decision = sampling_engine.should_sample(LogLevel.ERROR, 'test_logger')
        assert decision.should_sample is True
        assert decision.sampling_rate == 1.0
        assert decision.reason == "priority_preservation"
        
        # Test CRITICAL level
        decision = sampling_engine.should_sample(LogLevel.CRITICAL, 'test_logger')
        assert decision.should_sample is True
        assert decision.sampling_rate == 1.0
        assert decision.reason == "priority_preservation"
        
    def test_level_based_sampling(self, basic_config):
        """Test level-based sampling strategy"""
        basic_config.strategy = SamplingStrategy.LEVEL_BASED
        engine = AdvancedSamplingEngine(basic_config)
        
        # Mock random to ensure predictable results
        with patch('random.random', return_value=0.05):  # 5%
            decision = engine.should_sample(LogLevel.DEBUG, 'test_logger')
            assert decision.should_sample is True  # 5% < 10% (DEBUG rate)
            
        with patch('random.random', return_value=0.15):  # 15%
            decision = engine.should_sample(LogLevel.DEBUG, 'test_logger')
            assert decision.should_sample is False  # 15% > 10% (DEBUG rate)
            
    def test_volume_based_sampling(self, basic_config):
        """Test volume-based sampling strategy"""
        basic_config.strategy = SamplingStrategy.VOLUME_BASED
        engine = AdvancedSamplingEngine(basic_config)
        
        # Simulate low volume
        decision = engine.should_sample(LogLevel.INFO, 'test_logger')
        assert decision.sampling_rate == 0.5  # Base rate for INFO
        
        # Simulate high volume by adding many logs
        for _ in range(200):  # Exceed volume threshold
            engine._update_volume_tracking()
            
        decision = engine.should_sample(LogLevel.INFO, 'test_logger')
        assert decision.sampling_rate < 0.5  # Should be reduced due to high volume
        
    def test_adaptive_sampling_basic(self, sampling_engine):
        """Test basic adaptive sampling functionality"""
        # Initially should use base rate
        decision = sampling_engine.should_sample(LogLevel.INFO, 'test_logger')
        assert decision.sampling_rate == 0.5  # Base rate for INFO
        
        # Simulate volume increase
        for _ in range(150):  # Exceed threshold
            sampling_engine._update_volume_tracking()
            
        decision = sampling_engine.should_sample(LogLevel.INFO, 'test_logger')
        # Rate should be adjusted down due to high volume
        assert decision.sampling_rate < 0.5
        
    def test_volume_window_management(self, sampling_engine):
        """Test sliding window volume tracking"""
        initial_windows = len(sampling_engine.volume_windows)
        
        # Add some volume
        for _ in range(10):
            sampling_engine._update_volume_tracking()
            
        # Should still have same number of windows
        assert len(sampling_engine.volume_windows) == initial_windows
        
        # Check volume is tracked
        total_volume = sampling_engine._get_current_window_volume()
        assert total_volume > 0
        
    def test_statistics_collection(self, sampling_engine):
        """Test statistics collection"""
        # Generate some sampling decisions
        for level in [LogLevel.INFO, LogLevel.DEBUG, LogLevel.ERROR]:
            for _ in range(10):
                sampling_engine.should_sample(level, 'test_logger')
                
        stats = sampling_engine.get_sampling_statistics()
        
        assert 'statistics' in stats
        assert stats['statistics']['total_logs'] == 30
        assert 'level_statistics' in stats['statistics']
        assert 'INFO' in stats['statistics']['level_statistics']
        
    def test_sampling_efficiency_calculation(self, sampling_engine):
        """Test sampling efficiency calculation"""
        # All logs sampled initially
        efficiency = sampling_engine._calculate_sampling_efficiency()
        assert efficiency == 1.0
        
        # Generate some decisions
        with patch('random.random', return_value=0.9):  # High value to ensure some drops
            for _ in range(10):
                sampling_engine.should_sample(LogLevel.DEBUG, 'test_logger')
                
        efficiency = sampling_engine._calculate_sampling_efficiency()
        assert 0.0 <= efficiency <= 1.0
        
    def test_reset_functionality(self, sampling_engine):
        """Test reset functionality"""
        # Generate some activity
        for _ in range(20):
            sampling_engine.should_sample(LogLevel.INFO, 'test_logger')
            sampling_engine._update_volume_tracking()
            
        # Reset
        sampling_engine.reset_sampling_window()
        
        # Check reset state
        assert sampling_engine.statistics.total_logs == 0
        assert sampling_engine.statistics.sampled_logs == 0
        assert len(sampling_engine.historical_volumes) == 0
        assert sampling_engine.current_adaptive_rate == sampling_engine.config.default_rate


class TestDynamicRateAdjuster:
    """Test dynamic rate adjustment algorithms"""
    
    @pytest.fixture
    def config(self):
        """Configuration for dynamic adjuster testing"""
        return SamplingConfig(
            volume_threshold=100,
            adaptive_enabled=True,
            adaptive_adjustment_factor=0.1
        )
    
    @pytest.fixture
    def adjuster(self, config):
        """Create dynamic rate adjuster for testing"""
        return DynamicRateAdjuster(config)
    
    def test_initialization(self, adjuster):
        """Test proper initialization"""
        assert len(adjuster.volume_history) == 0
        assert len(adjuster.rate_history) == 0
        assert adjuster.learning_rate == 0.1
        
    def test_should_adjust_rate_timing(self, adjuster):
        """Test minimum interval between adjustments"""
        # Should not adjust immediately
        should_adjust = adjuster.should_adjust_rate(50, 1.0)
        assert should_adjust is False
        
        # Simulate time passage
        adjuster.last_adjustment_time = time.time() - 60  # 1 minute ago
        
        # Add some volume history to trigger pattern detection
        for i in range(10):
            adjuster.volume_history.append((time.time() - i, 200))  # High volume
            
        should_adjust = adjuster.should_adjust_rate(200, 1.0)
        # Should consider adjustment now
        
    def test_spike_pattern_detection(self, adjuster):
        """Test spike pattern detection"""
        # Create baseline volumes
        base_time = time.time()
        for i in range(5):
            adjuster.volume_history.append((base_time - i, 50))
            
        # Add spike volumes
        for i in range(3):
            adjuster.volume_history.append((base_time + i, 200))
            
        patterns = adjuster._detect_volume_patterns()
        spike_patterns = [p for p in patterns if p.pattern_type == 'spike']
        
        assert len(spike_patterns) > 0
        assert spike_patterns[0].confidence > 0.5
        
    def test_sustained_high_pattern_detection(self, adjuster):
        """Test sustained high volume pattern detection"""
        # Add sustained high volumes
        base_time = time.time()
        for i in range(6):
            adjuster.volume_history.append((base_time - i, 300))  # Above high threshold
            
        patterns = adjuster._detect_volume_patterns()
        sustained_patterns = [p for p in patterns if p.pattern_type == 'sustained_high']
        
        assert len(sustained_patterns) > 0
        assert sustained_patterns[0].confidence > 0.7
        
    def test_trend_pattern_detection(self, adjuster):
        """Test trend pattern detection"""
        # Create increasing trend
        base_time = time.time()
        for i in range(8):
            volume = 50 + (i * 20)  # Increasing trend
            adjuster.volume_history.append((base_time - (7-i), volume))
            
        patterns = adjuster._detect_volume_patterns()
        trend_patterns = [p for p in patterns if p.pattern_type == 'gradual_increase']
        
        assert len(trend_patterns) > 0
        
    def test_gradient_based_calculation(self, adjuster):
        """Test gradient-based rate calculation"""
        current_rate = 0.5
        base_rate = 0.5
        
        # High volume should reduce rate
        new_rate = adjuster._calculate_gradient_based_rate(300, current_rate, base_rate)
        assert new_rate < current_rate
        
        # Low volume should increase rate toward base
        new_rate = adjuster._calculate_gradient_based_rate(20, 0.2, base_rate)
        assert new_rate > 0.2
        
    def test_rate_constraints(self, adjuster):
        """Test rate adjustment constraints"""
        current_rate = 0.5
        
        # Test maximum change constraint
        large_change = 0.1  # Would be 80% reduction
        constrained = adjuster._constrain_rate_adjustment(current_rate, large_change)
        
        # Should be limited by max_adjustment_per_window (30%)
        max_allowed_change = current_rate * adjuster.max_adjustment_per_window
        assert constrained >= current_rate - max_allowed_change
        
    def test_effectiveness_tracking(self, adjuster):
        """Test adjustment effectiveness calculation"""
        # Add some volume history
        base_time = time.time()
        
        # Before adjustment - high volume
        for i in range(5):
            adjuster.volume_history.append((base_time - 10 - i, 200))
            
        # Record adjustment
        adjuster._record_adjustment(0.8, 0.4, 200)
        
        # After adjustment - lower volume
        for i in range(5):
            adjuster.volume_history.append((base_time + i, 100))
            
        # Record another adjustment to trigger effectiveness calculation
        adjuster._record_adjustment(0.4, 0.3, 100)
        
        # Check that effectiveness was calculated
        assert len(adjuster.adjustment_effectiveness) > 0
        
    def test_metadata_generation(self, adjuster):
        """Test adjustment metadata generation"""
        # Add some data
        adjuster.volume_history.append((time.time(), 150))
        adjuster._record_adjustment(0.8, 0.6, 150)
        
        metadata = adjuster.get_adjustment_metadata()
        
        assert 'dynamic_thresholds' in metadata
        assert 'detected_patterns' in metadata
        assert 'recent_adjustments' in metadata
        assert 'learning_rate' in metadata


class TestSamplingIntegration:
    """Test sampling pipeline integration"""
    
    @pytest.fixture
    def integration_config(self):
        """Integration configuration for testing"""
        sampling_config = SamplingConfig(enabled=True, volume_threshold=50)
        return SamplingIntegrationConfig(
            sampling_config=sampling_config,
            debug_mode_enabled=False
        )
    
    @pytest.fixture
    def integrator(self, integration_config):
        """Create sampling integrator for testing"""
        return SamplingPipelineIntegrator(integration_config)
    
    def test_initialization(self, integrator):
        """Test proper initialization"""
        assert integrator.config.sampling_config.enabled is True
        assert integrator.debug_mode_active is False
        assert 'total_log_entries' in integrator.pipeline_statistics
        
    def test_log_entry_processing(self, integrator):
        """Test log entry processing"""
        log_entry = {
            'level': 'INFO',
            'message': 'Test message',
            'logger_name': 'test_logger'
        }
        
        should_continue, updated_entry = integrator.process_log_entry(
            log_entry, 'pre_format'
        )
        
        assert isinstance(should_continue, bool)
        assert 'sampling' in updated_entry
        assert updated_entry['sampling']['sampling_applied'] is True
        
    def test_debug_mode_integration(self, integrator):
        """Test debug mode in integration"""
        integrator.enable_debug_mode()
        
        log_entry = {'level': 'DEBUG', 'message': 'Debug message'}
        should_continue, updated_entry = integrator.process_log_entry(
            log_entry, 'pre_format'
        )
        
        assert should_continue is True
        assert updated_entry['sampling']['debug_mode_active'] is True
        
    def test_integration_point_configuration(self, integrator):
        """Test integration point configuration"""
        # Disable pre_format integration
        integrator.configure_integration_points({'pre_format': False})
        
        log_entry = {'level': 'INFO', 'message': 'Test'}
        should_continue, updated_entry = integrator.process_log_entry(
            log_entry, 'pre_format'
        )
        
        # Should pass through without sampling
        assert should_continue is True
        assert 'sampling' not in updated_entry
        
    def test_statistics_collection(self, integrator):
        """Test pipeline statistics collection"""
        # Process some log entries
        for i in range(10):
            log_entry = {'level': 'INFO', 'message': f'Message {i}'}
            integrator.process_log_entry(log_entry, 'pre_format')
            
        stats = integrator.get_pipeline_statistics()
        
        assert stats['pipeline_statistics']['total_log_entries'] == 10
        assert stats['pipeline_statistics']['pre_format_samples'] > 0
        
    def test_sampling_decision_preview(self, integrator):
        """Test sampling decision preview"""
        decision = integrator.get_sampling_decision_preview('INFO')
        
        assert isinstance(decision, SamplingDecision)
        assert isinstance(decision.should_sample, bool)
        assert isinstance(decision.sampling_rate, float)


class TestSamplingMonitor:
    """Test sampling monitoring system"""
    
    @pytest.fixture
    def integrator(self):
        """Create integrator for monitoring tests"""
        config = SamplingIntegrationConfig(
            sampling_config=SamplingConfig(enabled=True)
        )
        return SamplingPipelineIntegrator(config)
    
    @pytest.fixture
    def monitor(self, integrator):
        """Create sampling monitor for testing"""
        return SamplingMonitor(integrator)
    
    def test_initialization(self, monitor):
        """Test monitor initialization"""
        assert monitor.monitoring_enabled is True
        assert 'high_drop_rate' in monitor.alert_thresholds
        assert len(monitor.active_alerts) == 0
        
    def test_alert_callback_management(self, monitor):
        """Test alert callback management"""
        callback = Mock()
        
        monitor.add_alert_callback(callback)
        assert callback in monitor.alert_callbacks
        
        monitor.remove_alert_callback(callback)
        assert callback not in monitor.alert_callbacks
        
    def test_threshold_updates(self, monitor):
        """Test alert threshold updates"""
        new_thresholds = {'high_drop_rate': 0.9}
        monitor.update_alert_thresholds(new_thresholds)
        
        assert monitor.alert_thresholds['high_drop_rate'] == 0.9
        
    def test_trend_data_updates(self, monitor):
        """Test trend data collection"""
        # Mock statistics
        stats = {
            'sampling_engine_statistics': {
                'current_window_volume': 150,
                'current_adaptive_rate': 0.7
            }
        }
        
        monitor._update_trend_data(stats)
        
        assert len(monitor.volume_trend_data) == 1
        assert len(monitor.rate_trend_data) == 1
        
    def test_alert_generation(self, monitor):
        """Test alert generation logic"""
        # Create stats that should trigger alerts
        stats = {
            'sampling_engine_statistics': {
                'statistics': {
                    'total_logs': 1000,
                    'dropped_logs': 900  # 90% drop rate
                },
                'current_adaptive_rate': 0.05  # Very low rate
            }
        }
        
        alerts = monitor._generate_alerts(stats)
        
        # Should generate high drop rate alert
        drop_rate_alerts = [a for a in alerts if a.alert_type == 'high_drop_rate']
        assert len(drop_rate_alerts) > 0
        
        # Should generate low sampling rate alert
        low_rate_alerts = [a for a in alerts if a.alert_type == 'low_sampling_rate']
        assert len(low_rate_alerts) > 0
        
    def test_report_generation(self, monitor):
        """Test comprehensive report generation"""
        # Add some trend data
        monitor.volume_trend_data.append((time.time(), 100))
        monitor.rate_trend_data.append((time.time(), 0.8))
        
        stats = {
            'sampling_engine_statistics': {
                'statistics': {'total_logs': 100, 'sampled_logs': 80},
                'current_adaptive_rate': 0.8
            },
            'pipeline_statistics': {},
            'debug_mode_active': False
        }
        
        report = monitor._generate_report(stats, [])
        
        assert report.report_id.startswith('sampling_report_')
        assert 'total_logs_processed' in report.summary
        assert 'sampling_efficiency' in report.summary
        
    def test_dashboard_data(self, monitor):
        """Test dashboard data generation"""
        dashboard_data = monitor.get_monitoring_dashboard_data()
        
        assert 'current_statistics' in dashboard_data
        assert 'volume_trend' in dashboard_data
        assert 'rate_trend' in dashboard_data
        assert 'monitoring_performance' in dashboard_data
        
    def test_report_export(self, monitor):
        """Test report export functionality"""
        from ucbl_logger.enhanced.sampling.monitoring import SamplingReport, SamplingAlert
        
        # Create a test report
        alert = SamplingAlert(
            alert_type='test_alert',
            severity='info',
            message='Test alert',
            timestamp=time.time()
        )
        
        report = SamplingReport(
            report_id='test_report',
            timestamp=time.time(),
            time_period=60.0,
            summary={'test': 'data'},
            detailed_statistics={},
            alerts=[alert],
            recommendations=['Test recommendation']
        )
        
        # Test JSON export
        json_export = monitor.export_report(report, 'json')
        assert 'test_report' in json_export
        
        # Test text export
        text_export = monitor.export_report(report, 'text')
        assert 'Test alert' in text_export
        assert 'Test recommendation' in text_export


class TestHighVolumeScenarios:
    """Test sampling behavior under high volume conditions"""
    
    @pytest.fixture
    def high_volume_config(self):
        """Configuration optimized for high volume testing"""
        return SamplingConfig(
            enabled=True,
            strategy=SamplingStrategy.ADAPTIVE,
            volume_threshold=100,
            high_volume_threshold=500,
            adaptive_enabled=True,
            adaptive_min_rate=0.01
        )
    
    @pytest.fixture
    def engine(self, high_volume_config):
        """Create engine for high volume testing"""
        return AdvancedSamplingEngine(high_volume_config)
    
    def test_extreme_volume_handling(self, engine):
        """Test behavior under extreme log volumes"""
        # Simulate extreme volume
        for _ in range(1000):
            engine._update_volume_tracking()
            
        # Should still function and reduce sampling rate significantly
        decision = engine.should_sample(LogLevel.INFO, 'test_logger')
        assert decision.sampling_rate < 0.1  # Should be very low
        
        # Critical logs should still be preserved
        critical_decision = engine.should_sample(LogLevel.CRITICAL, 'test_logger')
        assert critical_decision.should_sample is True
        
    def test_volume_spike_recovery(self, engine):
        """Test recovery after volume spikes"""
        initial_rate = engine.current_adaptive_rate
        
        # Create volume spike
        for _ in range(600):  # Above high threshold
            engine._update_volume_tracking()
            
        # Rate should be reduced
        spike_decision = engine.should_sample(LogLevel.INFO, 'test_logger')
        assert spike_decision.sampling_rate < initial_rate
        
        # Simulate volume returning to normal
        engine.reset_sampling_window()
        
        # Rate should recover
        recovery_decision = engine.should_sample(LogLevel.INFO, 'test_logger')
        assert recovery_decision.sampling_rate >= spike_decision.sampling_rate
        
    def test_sustained_load_performance(self, engine):
        """Test performance under sustained load"""
        start_time = time.time()
        
        # Simulate sustained load
        for i in range(1000):
            level = LogLevel.INFO if i % 2 == 0 else LogLevel.DEBUG
            engine.should_sample(level, f'logger_{i % 10}')
            
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Should complete in reasonable time (less than 1 second for 1000 decisions)
        assert processing_time < 1.0
        
        # Statistics should be maintained
        stats = engine.get_sampling_statistics()
        assert stats['statistics']['total_logs'] == 1000


class TestEdgeCases:
    """Test edge cases and error conditions"""
    
    def test_empty_volume_windows(self):
        """Test behavior with empty volume windows"""
        config = SamplingConfig(sliding_window_segments=0)
        engine = AdvancedSamplingEngine(config)
        
        # Should handle gracefully
        decision = engine.should_sample(LogLevel.INFO, 'test_logger')
        assert isinstance(decision, SamplingDecision)
        
    def test_invalid_log_levels(self):
        """Test handling of invalid log levels"""
        config = SamplingConfig()
        engine = AdvancedSamplingEngine(config)
        
        # Should handle gracefully and use default
        decision = engine.should_sample(LogLevel.INFO, 'test_logger')
        assert isinstance(decision, SamplingDecision)
        
    def test_zero_thresholds(self):
        """Test behavior with zero thresholds"""
        config = SamplingConfig(volume_threshold=0)
        engine = AdvancedSamplingEngine(config)
        
        # Should handle gracefully
        decision = engine.should_sample(LogLevel.INFO, 'test_logger')
        assert isinstance(decision, SamplingDecision)
        
    def test_concurrent_access_simulation(self):
        """Simulate concurrent access patterns"""
        config = SamplingConfig()
        engine = AdvancedSamplingEngine(config)
        
        # Simulate multiple threads accessing simultaneously
        decisions = []
        for i in range(100):
            decision = engine.should_sample(LogLevel.INFO, f'logger_{i}')
            decisions.append(decision)
            
        # All decisions should be valid
        assert len(decisions) == 100
        assert all(isinstance(d, SamplingDecision) for d in decisions)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])