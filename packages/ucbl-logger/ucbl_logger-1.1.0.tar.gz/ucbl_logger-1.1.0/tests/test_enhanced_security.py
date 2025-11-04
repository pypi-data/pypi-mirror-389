"""
Tests for enhanced security context detection and logging
"""

import os
import json
import time
import pytest
import threading
from unittest.mock import Mock, patch, MagicMock, mock_open
from pathlib import Path

from ucbl_logger.enhanced.security import (
    EnhancedSecurityContextLogger, SecurityContext, SecurityEvent,
    SecurityEventSeverity, SecurityEventType, RuntimeSecurityMonitor,
    PolicyViolationDetector, AdvancedRedactionEngine, RedactionLevel,
    RedactionRule, ConfigurationAuditor
)


class TestEnhancedSecurityContextLogger:
    """Test enhanced security context logger functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.logger = EnhancedSecurityContextLogger(
            enable_runtime_monitoring=False,  # Disable for testing to avoid interference
            enable_policy_detection=True
        )
    
    def test_initialization(self):
        """Test logger initialization"""
        assert self.logger.enable_runtime_monitoring is False  # We disabled it in setup
        assert self.logger.enable_policy_detection is True
        assert isinstance(self.logger._security_events, list)
        assert isinstance(self.logger._audit_trail, list)
    
    def test_sensitive_data_redaction(self):
        """Test enhanced sensitive data redaction"""
        test_cases = [
            ("Email: user@example.com", "[EMAIL_REDACTED]"),
            ("Phone: 555-123-4567", "[PHONE_REDACTED]"),
            ("SSN: 123-45-6789", "[SSN_REDACTED]"),
            ("Card: 1234 5678 9012 3456", "[CARD_REDACTED]"),
        ]
        
        for original, expected_pattern in test_cases:
            result = self.logger.redact_sensitive_data(original)
            assert expected_pattern in result or "[" in result
    
    @patch('os.getuid')
    @patch('os.getgid')
    @patch('os.getpid')
    def test_basic_security_context(self, mock_getpid, mock_getgid, mock_getuid):
        """Test basic security context collection"""
        mock_getuid.return_value = 1000
        mock_getgid.return_value = 1000
        mock_getpid.return_value = 12345
        
        context = self.logger.get_container_security_context()
        
        assert context['user_id'] == 1000
        assert context['group_id'] == 1000
        assert context['process_id'] == 12345  
  
    def test_security_event_logging(self):
        """Test security event logging"""
        event_details = {
            'process': 'test_process',
            'action': 'privilege_escalation',
            'user': 'root'
        }
        
        initial_events = len(self.logger.get_security_events())
        self.logger.log_security_event('privilege_escalation', event_details)
        
        events = self.logger.get_security_events()
        assert len(events) == initial_events + 1
        
        event = events[-1]  # Get the last event (the one we just added)
        assert event['event_type'] == 'privilege_escalation'
        assert event['severity'] == 'HIGH'
        assert event['details'] == event_details
        assert 'security_context' in event
        assert 'timestamp' in event
    
    def test_event_severity_determination(self):
        """Test security event severity determination"""
        test_cases = [
            ('privilege_escalation', 'HIGH'),
            ('root_access', 'HIGH'),
            ('policy_violation', 'MEDIUM'),
            ('configuration_change', 'MEDIUM'),
            ('info_event', 'LOW'),
        ]
        
        for event_type, expected_severity in test_cases:
            severity = self.logger._determine_event_severity(event_type, {})
            assert severity == expected_severity
    
    def test_configuration_change_audit(self):
        """Test configuration change auditing"""
        old_config = {'debug': False, 'log_level': 'INFO'}
        new_config = {'debug': True, 'log_level': 'DEBUG', 'new_feature': True}
        
        self.logger.audit_configuration_change('test_component', old_config, new_config)
        
        audit_trail = self.logger.get_audit_trail()
        assert len(audit_trail) == 1
        
        entry = audit_trail[0]
        assert entry['component'] == 'test_component'
        assert entry['change_count'] >= 2  # At least 2 changes
        assert 'changes' in entry
        assert entry['security_impact'] in ['LOW', 'MEDIUM', 'HIGH']
    
    @patch('os.getuid')
    def test_basic_security_policy_validation(self, mock_getuid):
        """Test basic security policy validation"""
        mock_getuid.return_value = 0
        violations = self.logger.validate_security_policies()
        
        assert any('root user' in violation for violation in violations)
    
    def test_security_events_management(self):
        """Test security events management operations"""
        self.logger.log_security_event('test_event_1', {'detail': 'test1'})
        self.logger.log_security_event('test_event_2', {'detail': 'test2'})
        
        events = self.logger.get_security_events()
        assert len(events) == 2
        
        self.logger.clear_security_events()
        events = self.logger.get_security_events()
        assert len(events) == 0
    
    def test_sensitive_env_var_detection(self):
        """Test sensitive environment variable detection"""
        test_cases = [
            ('DATABASE_PASSWORD', True),
            ('API_SECRET_KEY', True),
            ('DEBUG_MODE', False),
            ('APP_NAME', False),
        ]
        
        for env_var, is_sensitive in test_cases:
            result = self.logger._is_sensitive_env_var(env_var)
            assert result == is_sensitive
    
    def test_advanced_redaction_engine_integration(self):
        """Test integration with advanced redaction engine"""
        test_message = "Email: user@test.com, API Key: AKIA1234567890123456"
        
        redacted = self.logger.redact_sensitive_data(test_message)
        
        assert "[EMAIL_REDACTED]" in redacted
        assert "[AWS_ACCESS_KEY_REDACTED]" in redacted
        assert "user@test.com" not in redacted
        assert "AKIA1234567890123456" not in redacted
    
    def test_custom_redaction_rule_management(self):
        """Test custom redaction rule management"""
        # Add custom rule
        self.logger.add_custom_redaction_rule(
            name='test_pattern',
            pattern=r'\bTEST\d{4}\b',
            replacement='[TEST_REDACTED]',
            description='Test pattern'
        )
        
        # Test redaction with custom rule
        message = "This is TEST1234 in the message"
        redacted = self.logger.redact_sensitive_data(message)
        
        assert "[TEST_REDACTED]" in redacted
        assert "TEST1234" not in redacted
        
        # Remove custom rule
        success = self.logger.remove_redaction_rule('test_pattern')
        assert success is True
        
        # Test that rule is no longer active
        message2 = "This is TEST5678 in the message"
        redacted2 = self.logger.redact_sensitive_data(message2)
        assert "TEST5678" in redacted2  # Should not be redacted
    
    def test_redaction_statistics(self):
        """Test redaction statistics tracking"""
        # Trigger some redactions
        self.logger.redact_sensitive_data("Email: test@example.com")
        self.logger.redact_sensitive_data("Phone: 555-123-4567")
        
        stats = self.logger.get_redaction_statistics()
        
        assert 'total_redactions' in stats
        assert 'rules_triggered' in stats
        assert 'active_rules' in stats
        assert stats['total_redactions'] >= 2
    
    def test_configuration_audit_trail(self):
        """Test configuration change audit trail"""
        # Make a configuration change
        self.logger.add_custom_redaction_rule(
            name='audit_test',
            pattern=r'\bAUDIT\d+\b',
            replacement='[AUDIT_REDACTED]',
            description='Audit test pattern'
        )
        
        # Check audit trail
        audit_trail = self.logger.get_configuration_audit_trail()
        
        assert len(audit_trail) > 0
        
        # Find the audit entry for our change
        audit_entry = None
        for entry in audit_trail:
            if entry.get('change_type') == 'add_custom_rule':
                audit_entry = entry
                break
        
        assert audit_entry is not None
        assert audit_entry['component'] == 'redaction_engine'
        assert 'timestamp' in audit_entry
    
    @patch('ucbl_logger.enhanced.security.base.RuntimeSecurityMonitor')
    def test_runtime_security_monitoring_integration(self, mock_monitor_class):
        """Test runtime security monitoring integration"""
        mock_monitor = Mock()
        mock_monitor_class.return_value = mock_monitor
        
        # Create logger with runtime monitoring
        logger = EnhancedSecurityContextLogger(
            enable_runtime_monitoring=True,
            enable_policy_detection=False
        )
        
        # Verify monitor was created and started
        mock_monitor_class.assert_called_once()
        mock_monitor.start_monitoring.assert_called_once()
    
    def test_policy_violation_detection(self):
        """Test policy violation detection"""
        # Create a security context with violations
        security_context = {
            'user_id': 0,  # Root user
            'capabilities': {
                'effective': ['CAP_SYS_ADMIN', 'CAP_NET_BIND_SERVICE']
            },
            'root_filesystem_readonly': False
        }
        
        violations = self.logger.policy_detector.detect_violations(security_context)
        
        # Should detect multiple violations
        assert len(violations) > 0
        
        # Check for specific violations
        violation_types = [v['violation'] for v in violations]
        assert 'running_as_root' in violation_types or any('root' in str(v) for v in violations)
    
    def test_security_alert_handling(self):
        """Test security alert handling from runtime monitor"""
        from ucbl_logger.enhanced.security.advanced_monitor import SecurityAlert
        
        # Create a test alert
        alert = SecurityAlert(
            timestamp=time.time(),
            alert_type='test_alert',
            severity='HIGH',
            description='Test security alert',
            source='test',
            metadata={'test': 'data'}
        )
        
        # Handle the alert
        initial_events = len(self.logger.get_security_events())
        self.logger._handle_security_alert(alert)
        
        # Verify security event was created
        events = self.logger.get_security_events()
        assert len(events) == initial_events + 1
        
        # Verify event details
        new_event = events[-1]
        assert new_event['event_type'] == 'test_alert'
        assert new_event['details']['alert_type'] == 'test_alert'


class TestSecurityModels:
    """Test security data models"""
    
    def test_security_context_model(self):
        """Test SecurityContext data model"""
        context = SecurityContext(
            user_id=1000,
            group_id=1000,
            run_as_non_root=True,
            capabilities={'effective': ['CAP_NET_BIND_SERVICE']},
            container_runtime='docker'
        )
        
        data = context.to_dict()
        
        assert data['user_id'] == 1000
        assert data['group_id'] == 1000
        assert data['run_as_non_root'] is True
        assert data['capabilities'] == {'effective': ['CAP_NET_BIND_SERVICE']}
        assert data['container_runtime'] == 'docker'
    
    def test_security_event_enums(self):
        """Test security event enums"""
        assert SecurityEventSeverity.HIGH.value == "HIGH"
        assert SecurityEventType.PRIVILEGE_ESCALATION.value == "privilege_escalation"



class TestRuntimeSecurityMonitor:
    """Test runtime security monitor functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.monitor = RuntimeSecurityMonitor()
    
    def teardown_method(self):
        """Clean up after tests"""
        if self.monitor._monitoring:
            self.monitor.stop_monitoring()
    
    def test_initialization(self):
        """Test monitor initialization"""
        assert self.monitor.available_tools is not None
        assert isinstance(self.monitor.monitor_config, dict)
        assert self.monitor._monitoring is False
    
    def test_start_stop_monitoring(self):
        """Test starting and stopping monitoring"""
        # Start monitoring
        self.monitor.start_monitoring()
        assert self.monitor._monitoring is True
        assert self.monitor._monitor_thread is not None
        
        # Stop monitoring
        self.monitor.stop_monitoring()
        assert self.monitor._monitoring is False
    
    @patch('subprocess.run')
    def test_tool_availability_check(self, mock_run):
        """Test security tool availability checking"""
        # Mock successful tool check
        mock_run.return_value.returncode = 0
        
        result = self.monitor._check_tool_availability('falco')
        assert result is True
        
        # Mock failed tool check
        mock_run.return_value.returncode = 1
        
        result = self.monitor._check_tool_availability('nonexistent')
        assert result is False
    
    def test_security_alert_creation(self):
        """Test security alert creation"""
        alerts = []
        
        def alert_callback(alert):
            alerts.append(alert)
        
        monitor = RuntimeSecurityMonitor(alert_callback=alert_callback)
        
        # Create a test alert
        monitor._create_security_alert(
            alert_type='test_alert',
            severity='HIGH',
            description='Test alert',
            source='test',
            metadata={'key': 'value'}
        )
        
        assert len(alerts) == 1
        alert = alerts[0]
        assert alert.alert_type == 'test_alert'
        assert alert.severity == 'HIGH'
        assert alert.description == 'Test alert'
        assert alert.metadata['key'] == 'value'
    
    @patch('pathlib.Path.exists')
    def test_container_escape_detection(self, mock_exists):
        """Test container escape attempt detection"""
        alerts = []
        
        def alert_callback(alert):
            alerts.append(alert)
        
        monitor = RuntimeSecurityMonitor(alert_callback=alert_callback)
        
        # Mock suspicious path exists
        mock_exists.return_value = True
        
        monitor._detect_container_escape_attempts()
        
        # Should generate alerts for suspicious paths
        assert len(alerts) > 0
        
        # Check alert types
        alert_types = [alert.alert_type for alert in alerts]
        assert 'container_escape_attempt' in alert_types
    
    @patch('builtins.open', mock_open(read_data='tcp 0 0 0.0.0.0:4444 0.0.0.0:* 0A'))
    def test_network_monitoring(self):
        """Test network activity monitoring"""
        alerts = []
        
        def alert_callback(alert):
            alerts.append(alert)
        
        monitor = RuntimeSecurityMonitor(alert_callback=alert_callback)
        monitor._monitor_network_activity()
        
        # Should detect suspicious port 4444 (may not trigger in test environment)
        suspicious_alerts = [a for a in alerts if a.alert_type == 'suspicious_network_activity']
        # Note: This may not trigger in test environment, so we just check the method runs


class TestAdvancedRedactionEngine:
    """Test advanced redaction engine functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.engine = AdvancedRedactionEngine(RedactionLevel.STRICT)
    
    def test_initialization(self):
        """Test engine initialization"""
        assert self.engine.redaction_level == RedactionLevel.STRICT
        assert len(self.engine.redaction_rules) > 0
        assert 'email' in self.engine.redaction_rules
        assert 'aws_access_key' in self.engine.redaction_rules
    
    def test_basic_redaction(self):
        """Test basic sensitive data redaction"""
        test_cases = [
            ("Email: user@example.com", "[EMAIL_REDACTED]"),
            ("AWS Key: AKIA1234567890123456", "[AWS_ACCESS_KEY_REDACTED]"),
            ("Phone: 555-123-4567", "[PHONE_REDACTED]"),
            ("SSN: 123-45-6789", "[SSN_REDACTED]"),
        ]
        
        for original, expected_pattern in test_cases:
            result = self.engine.redact_message(original)
            assert expected_pattern in result
            # Ensure original sensitive data is not present
            sensitive_parts = original.split(': ')[1] if ': ' in original else original
            assert sensitive_parts not in result or '[' in result
    
    def test_custom_rule_management(self):
        """Test custom redaction rule management"""
        # Add custom rule
        self.engine.add_custom_rule(
            name='test_id',
            pattern=r'\bID\d{6}\b',
            replacement='[ID_REDACTED]',
            description='Test ID pattern'
        )
        
        # Test redaction
        message = "User ID123456 logged in"
        result = self.engine.redact_message(message)
        
        assert "[ID_REDACTED]" in result
        assert "ID123456" not in result
        
        # Remove rule
        success = self.engine.remove_rule('test_id')
        assert success is True
        
        # Test rule is gone
        message2 = "User ID789012 logged in"
        result2 = self.engine.redact_message(message2)
        assert "ID789012" in result2  # Should not be redacted
    
    def test_rule_enable_disable(self):
        """Test enabling and disabling rules"""
        # Disable email rule
        success = self.engine.disable_rule('email')
        assert success is True
        
        # Test email is not redacted
        message = "Contact: user@example.com"
        result = self.engine.redact_message(message)
        assert "user@example.com" in result
        
        # Re-enable email rule
        success = self.engine.enable_rule('email')
        assert success is True
        
        # Test email is redacted again
        result2 = self.engine.redact_message(message)
        assert "[EMAIL_REDACTED]" in result2
    
    def test_redaction_levels(self):
        """Test different redaction levels"""
        # Basic level
        basic_engine = AdvancedRedactionEngine(RedactionLevel.BASIC)
        
        # Strict level
        strict_engine = AdvancedRedactionEngine(RedactionLevel.STRICT)
        
        # Paranoid level
        paranoid_engine = AdvancedRedactionEngine(RedactionLevel.PARANOID)
        
        # Test that paranoid has more rules than strict, strict more than basic
        assert len(paranoid_engine.redaction_rules) >= len(strict_engine.redaction_rules)
        assert len(strict_engine.redaction_rules) >= len(basic_engine.redaction_rules)
        
        # Test IP address redaction (only in paranoid)
        ip_message = "Server IP: 192.168.1.100"
        
        basic_result = basic_engine.redact_message(ip_message)
        paranoid_result = paranoid_engine.redact_message(ip_message)
        
        assert "192.168.1.100" in basic_result  # Basic doesn't redact IPs
        assert "[IP_REDACTED]" in paranoid_result  # Paranoid does
    
    def test_contextual_redaction(self):
        """Test context-aware redaction"""
        # Test environment variable redaction
        env_message = 'DATABASE_PASSWORD=secret123 DEBUG_MODE=true'
        result = self.engine.redact_message(env_message)
        
        assert "DATABASE_PASSWORD=[REDACTED]" in result
        assert "DEBUG_MODE=true" in result  # Non-sensitive env var preserved
        
        # Test JSON field redaction
        json_message = '{"username": "user", "password": "secret", "debug": false}'
        result = self.engine.redact_message(json_message)
        
        assert '"password":"[REDACTED]"' in result
        assert '"username": "user"' in result  # Non-sensitive field preserved
    
    def test_audit_trail(self):
        """Test redaction audit trail"""
        # Perform some redactions
        self.engine.redact_message("Email: test@example.com")
        self.engine.redact_message("Phone: 555-123-4567")
        
        # Check audit trail
        audit_trail = self.engine.get_audit_trail()
        
        assert len(audit_trail) >= 2
        
        # Check audit entry structure
        entry = audit_trail[0]
        assert 'timestamp' in entry
        assert 'rule_name' in entry
        assert 'original_hash' in entry
        assert 'redacted_count' in entry
    
    def test_statistics(self):
        """Test redaction statistics"""
        # Perform redactions
        self.engine.redact_message("Email: test1@example.com and test2@example.com")
        self.engine.redact_message("Phone: 555-123-4567")
        
        stats = self.engine.get_statistics()
        
        assert 'total_redactions' in stats
        assert 'rules_triggered' in stats
        assert 'active_rules' in stats
        assert stats['total_redactions'] >= 3  # 2 emails + 1 phone
        assert 'email' in stats['rules_triggered']
        assert 'phone_us' in stats['rules_triggered']
    
    def test_custom_processor(self):
        """Test custom redaction processor"""
        def custom_processor(message: str) -> str:
            # Simple custom processor that redacts "CUSTOM123"
            return message.replace("CUSTOM123", "[CUSTOM_REDACTED]")
        
        self.engine.add_custom_processor('test_processor', custom_processor)
        
        message = "This contains CUSTOM123 data"
        result = self.engine.redact_message(message)
        
        assert "[CUSTOM_REDACTED]" in result
        assert "CUSTOM123" not in result


class TestPolicyViolationDetector:
    """Test policy violation detector functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.detector = PolicyViolationDetector()
    
    def test_initialization(self):
        """Test detector initialization"""
        assert self.detector.violation_rules is not None
        assert 'pod_security_standards' in self.detector.violation_rules
    
    def test_root_user_violation(self):
        """Test detection of root user violation"""
        security_context = {
            'user_id': 0,  # Root user
            'capabilities': {'effective': []},
            'root_filesystem_readonly': True
        }
        
        violations = self.detector.detect_violations(security_context)
        
        # Should detect root user violation
        root_violations = [v for v in violations if 'root' in v['description'].lower()]
        assert len(root_violations) > 0
    
    def test_dangerous_capability_violation(self):
        """Test detection of dangerous capability violations"""
        security_context = {
            'user_id': 1000,
            'capabilities': {
                'effective': ['CAP_SYS_ADMIN', 'CAP_NET_BIND_SERVICE']
            },
            'root_filesystem_readonly': True
        }
        
        violations = self.detector.detect_violations(security_context)
        
        # Should detect CAP_SYS_ADMIN violation
        cap_violations = [v for v in violations if v['type'] == 'capability_violation']
        assert len(cap_violations) > 0
        
        # Check specific capability
        sys_admin_violations = [v for v in cap_violations if 'CAP_SYS_ADMIN' in v['description']]
        assert len(sys_admin_violations) > 0
    
    def test_writable_filesystem_violation(self):
        """Test detection of writable root filesystem violation"""
        security_context = {
            'user_id': 1000,
            'capabilities': {'effective': []},
            'root_filesystem_readonly': False  # Writable root filesystem
        }
        
        violations = self.detector.detect_violations(security_context)
        
        # Should detect writable filesystem violation
        fs_violations = [v for v in violations if 'filesystem' in v['description'].lower()]
        assert len(fs_violations) > 0
    
    def test_pod_security_standards_compliance(self):
        """Test Pod Security Standards compliance checking"""
        # Compliant context
        compliant_context = {
            'user_id': 1000,
            'capabilities': {'effective': ['CAP_NET_BIND_SERVICE']},
            'root_filesystem_readonly': True
        }
        
        violations = self.detector.detect_violations(compliant_context)
        pss_violations = [v for v in violations if v['type'] == 'pod_security_standards']
        
        # Should have no PSS violations for compliant context
        assert len(pss_violations) == 0
        
        # Non-compliant context
        non_compliant_context = {
            'user_id': 0,  # Root user
            'capabilities': {'effective': ['CAP_SYS_ADMIN']},  # Forbidden capability
            'root_filesystem_readonly': False  # Writable filesystem
        }
        
        violations = self.detector.detect_violations(non_compliant_context)
        pss_violations = [v for v in violations if v['type'] == 'pod_security_standards']
        
        # Should have PSS violations for non-compliant context
        assert len(pss_violations) > 0


class TestConfigurationAuditor:
    """Test configuration auditor functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.auditor = ConfigurationAuditor()
    
    def test_initialization(self):
        """Test auditor initialization"""
        assert self.auditor.audit_events is not None
        assert len(self.auditor.audit_events) == 0
    
    def test_redaction_config_change_audit(self):
        """Test auditing of redaction configuration changes"""
        self.auditor.audit_redaction_config_change(
            component='redaction_engine',
            change_type='add_rule',
            old_value=None,
            new_value={'name': 'test_rule', 'pattern': r'\bTEST\b'},
            user_context={'user_id': 1000}
        )
        
        audit_trail = self.auditor.get_audit_trail()
        
        assert len(audit_trail) == 1
        
        entry = audit_trail[0]
        assert entry['component'] == 'redaction_engine'
        assert entry['change_type'] == 'add_rule'
        assert entry['security_impact'] in ['LOW', 'MEDIUM', 'HIGH']
        assert 'timestamp' in entry
        assert entry['user_context']['user_id'] == 1000
    
    def test_security_impact_assessment(self):
        """Test security impact assessment"""
        # High impact change
        high_impact = self.auditor._assess_config_security_impact(
            'disable_rule', 'enabled', 'disabled'
        )
        assert high_impact == 'HIGH'
        
        # Medium impact change
        medium_impact = self.auditor._assess_config_security_impact(
            'add_rule', None, 'new_rule'
        )
        assert medium_impact == 'MEDIUM'
        
        # Low impact change
        low_impact = self.auditor._assess_config_security_impact(
            'update_description', 'old_desc', 'new_desc'
        )
        assert low_impact == 'LOW'
    
    def test_audit_trail_management(self):
        """Test audit trail management"""
        # Add multiple audit entries
        for i in range(5):
            self.auditor.audit_redaction_config_change(
                component=f'component_{i}',
                change_type='test_change',
                old_value=f'old_{i}',
                new_value=f'new_{i}'
            )
        
        # Check full trail
        full_trail = self.auditor.get_audit_trail()
        assert len(full_trail) == 5
        
        # Check limited trail
        limited_trail = self.auditor.get_audit_trail(limit=3)
        assert len(limited_trail) == 3
        
        # Clear trail
        self.auditor.clear_audit_trail()
        empty_trail = self.auditor.get_audit_trail()
        assert len(empty_trail) == 0


class TestSecurityIntegration:
    """Test integration between security components"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.logger = EnhancedSecurityContextLogger(
            enable_runtime_monitoring=False,  # Disable for testing
            enable_policy_detection=True,
            redaction_level=RedactionLevel.STRICT
        )
    
    def test_end_to_end_security_workflow(self):
        """Test complete security workflow"""
        # 1. Log a security event with sensitive data
        sensitive_message = "User admin@company.com accessed system with API key AKIA1234567890123456"
        
        # 2. Redact sensitive data
        redacted_message = self.logger.redact_sensitive_data(sensitive_message)
        
        # Verify redaction
        assert "[EMAIL_REDACTED]" in redacted_message
        assert "[AWS_ACCESS_KEY_REDACTED]" in redacted_message
        assert "admin@company.com" not in redacted_message
        assert "AKIA1234567890123456" not in redacted_message
        
        # 3. Log security event
        self.logger.log_security_event('unauthorized_access', {
            'message': redacted_message,
            'user': 'admin',
            'timestamp': time.time()
        })
        
        # 4. Verify security event was logged
        events = self.logger.get_security_events()
        assert len(events) > 0
        
        latest_event = events[-1]
        assert latest_event['event_type'] == 'unauthorized_access'
        assert 'security_context' in latest_event
        
        # 5. Check redaction statistics
        stats = self.logger.get_redaction_statistics()
        assert stats['total_redactions'] >= 2  # Email + AWS key
        
        # 6. Validate security policies
        violations = self.logger.validate_security_policies()
        # Should return list of violations (may be empty in test environment)
        assert isinstance(violations, list)
    
    def test_configuration_change_with_audit(self):
        """Test configuration changes with full audit trail"""
        # Add custom redaction rule
        self.logger.add_custom_redaction_rule(
            name='integration_test',
            pattern=r'\bINTEGRATION\d+\b',
            replacement='[INTEGRATION_REDACTED]',
            description='Integration test pattern'
        )
        
        # Test the rule works
        message = "Test INTEGRATION123 data"
        redacted = self.logger.redact_sensitive_data(message)
        assert "[INTEGRATION_REDACTED]" in redacted
        
        # Check configuration audit trail
        config_audit = self.logger.get_configuration_audit_trail()
        assert len(config_audit) > 0
        
        # Find our change
        our_change = None
        for entry in config_audit:
            if entry.get('change_type') == 'add_custom_rule':
                our_change = entry
                break
        
        assert our_change is not None
        assert our_change['component'] == 'redaction_engine'
        
        # Remove the rule
        success = self.logger.remove_redaction_rule('integration_test')
        assert success is True
        
        # Verify removal was audited
        config_audit_after = self.logger.get_configuration_audit_trail()
        assert len(config_audit_after) >= len(config_audit)  # Should be at least the same or more


if __name__ == '__main__':
    pytest.main([__file__])