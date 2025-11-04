"""
Advanced sensitive data redaction engine with configurable patterns and audit trail
"""

import re
import json
import time
import logging
import hashlib
from typing import Dict, Any, List, Optional, Pattern, Callable
from dataclasses import dataclass, field
from enum import Enum


class RedactionLevel(Enum):
    """Redaction security levels"""
    NONE = "none"
    BASIC = "basic"
    STRICT = "strict"
    PARANOID = "paranoid"


@dataclass
class RedactionRule:
    """Configurable redaction rule"""
    name: str
    pattern: Pattern[str]
    replacement: str
    level: RedactionLevel
    description: str
    enabled: bool = True
    custom: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'pattern': self.pattern.pattern,
            'replacement': self.replacement,
            'level': self.level.value,
            'description': self.description,
            'enabled': self.enabled,
            'custom': self.custom
        }


@dataclass
class RedactionEvent:
    """Redaction audit event"""
    timestamp: float
    rule_name: str
    original_hash: str  # Hash of original content for audit
    redacted_count: int
    context: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp,
            'rule_name': self.rule_name,
            'original_hash': self.original_hash,
            'redacted_count': self.redacted_count,
            'context': self.context
        }


class AdvancedRedactionEngine:
    """Advanced configurable sensitive data redaction engine"""
    
    def __init__(self, redaction_level: RedactionLevel = RedactionLevel.STRICT):
        """
        Initialize advanced redaction engine
        
        Args:
            redaction_level: Default redaction security level
        """
        self.logger = logging.getLogger(__name__)
        self.redaction_level = redaction_level
        self.redaction_rules: Dict[str, RedactionRule] = {}
        self.redaction_events: List[RedactionEvent] = []
        self.custom_processors: Dict[str, Callable[[str], str]] = {}
        
        # Initialize built-in redaction rules
        self._initialize_builtin_rules()
        
        # Statistics
        self.stats = {
            'total_redactions': 0,
            'rules_triggered': {},
            'last_reset': time.time()
        }
    
    def _initialize_builtin_rules(self) -> None:
        """Initialize built-in redaction rules"""
        
        # Basic level rules
        basic_rules = [
            RedactionRule(
                name='email',
                pattern=re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
                replacement='[EMAIL_REDACTED]',
                level=RedactionLevel.BASIC,
                description='Email addresses'
            ),
            RedactionRule(
                name='phone_us',
                pattern=re.compile(r'\b(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})\b'),
                replacement='[PHONE_REDACTED]',
                level=RedactionLevel.BASIC,
                description='US phone numbers'
            ),
            RedactionRule(
                name='ssn',
                pattern=re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
                replacement='[SSN_REDACTED]',
                level=RedactionLevel.BASIC,
                description='Social Security Numbers'
            ),
            RedactionRule(
                name='credit_card',
                pattern=re.compile(r'\b(?:\d{4}[\s-]?){3}\d{4}\b'),
                replacement='[CARD_REDACTED]',
                level=RedactionLevel.BASIC,
                description='Credit card numbers'
            )
        ]
        
        # Strict level rules (includes basic + more)
        strict_rules = [
            RedactionRule(
                name='aws_access_key',
                pattern=re.compile(r'\bAKIA[0-9A-Z]{16}\b'),
                replacement='[AWS_ACCESS_KEY_REDACTED]',
                level=RedactionLevel.STRICT,
                description='AWS Access Keys'
            ),
            RedactionRule(
                name='aws_secret_key',
                pattern=re.compile(r'\b[A-Za-z0-9/+=]{40}\b'),
                replacement='[AWS_SECRET_KEY_REDACTED]',
                level=RedactionLevel.STRICT,
                description='AWS Secret Keys'
            ),
            RedactionRule(
                name='jwt_token',
                pattern=re.compile(r'\beyJ[A-Za-z0-9_/+=]+\.[A-Za-z0-9_/+=]+\.[A-Za-z0-9_/+=]*\b'),
                replacement='[JWT_TOKEN_REDACTED]',
                level=RedactionLevel.STRICT,
                description='JWT tokens'
            ),
            RedactionRule(
                name='api_key_generic',
                pattern=re.compile(r'\b[Aa]pi[_-]?[Kk]ey[:\s]*[\'"]?([A-Za-z0-9_\-]{20,})[\'"]?\b'),
                replacement='[API_KEY_REDACTED]',
                level=RedactionLevel.STRICT,
                description='Generic API keys'
            ),
            RedactionRule(
                name='password_field',
                pattern=re.compile(r'\b[Pp]assword[:\s]*[\'"]?([A-Za-z0-9_\-@#$%^&*!]{8,})[\'"]?\b'),
                replacement='[PASSWORD_REDACTED]',
                level=RedactionLevel.STRICT,
                description='Password fields'
            ),
            RedactionRule(
                name='private_key',
                pattern=re.compile(r'-----BEGIN [A-Z ]+PRIVATE KEY-----.*?-----END [A-Z ]+PRIVATE KEY-----', re.DOTALL),
                replacement='[PRIVATE_KEY_REDACTED]',
                level=RedactionLevel.STRICT,
                description='Private keys'
            ),
            RedactionRule(
                name='certificate',
                pattern=re.compile(r'-----BEGIN CERTIFICATE-----.*?-----END CERTIFICATE-----', re.DOTALL),
                replacement='[CERTIFICATE_REDACTED]',
                level=RedactionLevel.STRICT,
                description='Certificates'
            )
        ]
        
        # Paranoid level rules (includes strict + more aggressive)
        paranoid_rules = [
            RedactionRule(
                name='ip_address',
                pattern=re.compile(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'),
                replacement='[IP_REDACTED]',
                level=RedactionLevel.PARANOID,
                description='IP addresses'
            ),
            RedactionRule(
                name='mac_address',
                pattern=re.compile(r'\b(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}\b'),
                replacement='[MAC_REDACTED]',
                level=RedactionLevel.PARANOID,
                description='MAC addresses'
            ),
            RedactionRule(
                name='uuid',
                pattern=re.compile(r'\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b', re.IGNORECASE),
                replacement='[UUID_REDACTED]',
                level=RedactionLevel.PARANOID,
                description='UUIDs'
            ),
            RedactionRule(
                name='base64_data',
                pattern=re.compile(r'\b[A-Za-z0-9+/]{20,}={0,2}\b'),
                replacement='[BASE64_DATA_REDACTED]',
                level=RedactionLevel.PARANOID,
                description='Base64 encoded data'
            ),
            RedactionRule(
                name='hex_data',
                pattern=re.compile(r'\b0x[0-9A-Fa-f]{16,}\b'),
                replacement='[HEX_DATA_REDACTED]',
                level=RedactionLevel.PARANOID,
                description='Hexadecimal data'
            )
        ]
        
        # Add rules based on redaction level
        all_rules = basic_rules
        
        if self.redaction_level in [RedactionLevel.STRICT, RedactionLevel.PARANOID]:
            all_rules.extend(strict_rules)
        
        if self.redaction_level == RedactionLevel.PARANOID:
            all_rules.extend(paranoid_rules)
        
        # Store rules
        for rule in all_rules:
            self.redaction_rules[rule.name] = rule
    
    def add_custom_rule(self, name: str, pattern: str, replacement: str, 
                       description: str, level: RedactionLevel = RedactionLevel.STRICT) -> None:
        """
        Add a custom redaction rule
        
        Args:
            name: Rule name
            pattern: Regex pattern string
            replacement: Replacement text
            description: Rule description
            level: Redaction level
        """
        try:
            compiled_pattern = re.compile(pattern)
            rule = RedactionRule(
                name=name,
                pattern=compiled_pattern,
                replacement=replacement,
                level=level,
                description=description,
                custom=True
            )
            
            self.redaction_rules[name] = rule
            self.logger.info(f"Added custom redaction rule: {name}")
            
        except re.error as e:
            self.logger.error(f"Invalid regex pattern for rule {name}: {e}")
            raise ValueError(f"Invalid regex pattern: {e}")
    
    def remove_rule(self, name: str) -> bool:
        """
        Remove a redaction rule
        
        Args:
            name: Rule name to remove
            
        Returns:
            True if rule was removed, False if not found
        """
        if name in self.redaction_rules:
            del self.redaction_rules[name]
            self.logger.info(f"Removed redaction rule: {name}")
            return True
        return False
    
    def enable_rule(self, name: str) -> bool:
        """Enable a redaction rule"""
        if name in self.redaction_rules:
            self.redaction_rules[name].enabled = True
            return True
        return False
    
    def disable_rule(self, name: str) -> bool:
        """Disable a redaction rule"""
        if name in self.redaction_rules:
            self.redaction_rules[name].enabled = False
            return True
        return False
    
    def add_custom_processor(self, name: str, processor: Callable[[str], str]) -> None:
        """
        Add a custom redaction processor function
        
        Args:
            name: Processor name
            processor: Function that takes a string and returns redacted string
        """
        self.custom_processors[name] = processor
        self.logger.info(f"Added custom processor: {name}")
    
    def redact_message(self, message: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Redact sensitive data from a message
        
        Args:
            message: Original message
            context: Optional context for audit trail
            
        Returns:
            Redacted message
        """
        if not message:
            return message
        
        redacted_message = message
        total_redactions = 0
        triggered_rules = []
        
        # Apply built-in rules
        for rule_name, rule in self.redaction_rules.items():
            if not rule.enabled:
                continue
            
            # Count matches before redaction
            matches = list(rule.pattern.finditer(redacted_message))
            if matches:
                redacted_message = rule.pattern.sub(rule.replacement, redacted_message)
                redaction_count = len(matches)
                total_redactions += redaction_count
                triggered_rules.append(rule_name)
                
                # Update statistics
                self.stats['rules_triggered'][rule_name] = (
                    self.stats['rules_triggered'].get(rule_name, 0) + redaction_count
                )
        
        # Apply custom processors
        for processor_name, processor in self.custom_processors.items():
            try:
                processed_message = processor(redacted_message)
                if processed_message != redacted_message:
                    redacted_message = processed_message
                    triggered_rules.append(f"custom:{processor_name}")
            except Exception as e:
                self.logger.error(f"Error in custom processor {processor_name}: {e}")
        
        # Apply contextual redaction
        redacted_message = self._apply_contextual_redaction(redacted_message)
        
        # Record redaction event if any redactions occurred
        if total_redactions > 0:
            self._record_redaction_event(message, triggered_rules, total_redactions, context)
            self.stats['total_redactions'] += total_redactions
        
        return redacted_message
    
    def _apply_contextual_redaction(self, message: str) -> str:
        """Apply context-aware redaction"""
        # Redact environment variables that might contain secrets
        env_pattern = re.compile(r'([A-Z_][A-Z0-9_]*)\s*=\s*([^\s]+)')
        
        def redact_env_var(match):
            var_name, var_value = match.groups()
            if self._is_sensitive_env_var(var_name):
                return f"{var_name}=[REDACTED]"
            return match.group(0)
        
        message = env_pattern.sub(redact_env_var, message)
        
        # Redact JSON fields that might contain sensitive data
        json_pattern = re.compile(r'"([^"]*(?:password|secret|key|token|credential)[^"]*)"\s*:\s*"([^"]*)"', re.IGNORECASE)
        message = json_pattern.sub(r'"\1":"[REDACTED]"', message)
        
        # Redact URLs with credentials
        url_pattern = re.compile(r'(https?://)[^:]+:[^@]+@([^\s]+)')
        message = url_pattern.sub(r'\1[CREDENTIALS_REDACTED]@\2', message)
        
        return message
    
    def _is_sensitive_env_var(self, name: str) -> bool:
        """Check if environment variable name indicates sensitive data"""
        sensitive_patterns = [
            'password', 'secret', 'key', 'token', 'credential', 'auth',
            'cert', 'private', 'api_key', 'access_key', 'database_url',
            'connection_string', 'dsn', 'jwt', 'oauth', 'session'
        ]
        name_lower = name.lower()
        return any(pattern in name_lower for pattern in sensitive_patterns)
    
    def _record_redaction_event(self, original_message: str, triggered_rules: List[str], 
                               redaction_count: int, context: Optional[Dict[str, Any]]) -> None:
        """Record a redaction event for audit trail"""
        # Create hash of original message for audit purposes
        original_hash = hashlib.sha256(original_message.encode()).hexdigest()[:16]
        
        event = RedactionEvent(
            timestamp=time.time(),
            rule_name=','.join(triggered_rules),
            original_hash=original_hash,
            redacted_count=redaction_count,
            context=context or {}
        )
        
        self.redaction_events.append(event)
        
        # Limit audit trail size
        if len(self.redaction_events) > 10000:
            self.redaction_events = self.redaction_events[-5000:]  # Keep last 5000
    
    def get_redaction_rules(self) -> Dict[str, Dict[str, Any]]:
        """Get all redaction rules"""
        return {name: rule.to_dict() for name, rule in self.redaction_rules.items()}
    
    def get_audit_trail(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get redaction audit trail"""
        events = self.redaction_events
        if limit:
            events = events[-limit:]
        return [event.to_dict() for event in events]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get redaction statistics"""
        return {
            'total_redactions': self.stats['total_redactions'],
            'rules_triggered': self.stats['rules_triggered'].copy(),
            'active_rules': len([r for r in self.redaction_rules.values() if r.enabled]),
            'total_rules': len(self.redaction_rules),
            'custom_rules': len([r for r in self.redaction_rules.values() if r.custom]),
            'custom_processors': len(self.custom_processors),
            'audit_events': len(self.redaction_events),
            'last_reset': self.stats['last_reset']
        }
    
    def reset_statistics(self) -> None:
        """Reset redaction statistics"""
        self.stats = {
            'total_redactions': 0,
            'rules_triggered': {},
            'last_reset': time.time()
        }
    
    def clear_audit_trail(self) -> None:
        """Clear redaction audit trail"""
        self.redaction_events.clear()
    
    def export_configuration(self) -> Dict[str, Any]:
        """Export redaction configuration"""
        return {
            'redaction_level': self.redaction_level.value,
            'rules': self.get_redaction_rules(),
            'custom_processors': list(self.custom_processors.keys()),
            'statistics': self.get_statistics()
        }
    
    def import_configuration(self, config: Dict[str, Any]) -> None:
        """Import redaction configuration"""
        try:
            # Set redaction level
            if 'redaction_level' in config:
                self.redaction_level = RedactionLevel(config['redaction_level'])
            
            # Import custom rules
            if 'rules' in config:
                for rule_name, rule_data in config['rules'].items():
                    if rule_data.get('custom', False):
                        self.add_custom_rule(
                            name=rule_name,
                            pattern=rule_data['pattern'],
                            replacement=rule_data['replacement'],
                            description=rule_data['description'],
                            level=RedactionLevel(rule_data['level'])
                        )
            
            self.logger.info("Imported redaction configuration")
            
        except Exception as e:
            self.logger.error(f"Error importing redaction configuration: {e}")
            raise ValueError(f"Invalid configuration: {e}")


class ConfigurationAuditor:
    """Auditor for security-related configuration changes"""
    
    def __init__(self):
        """Initialize configuration auditor"""
        self.logger = logging.getLogger(__name__)
        self.audit_events: List[Dict[str, Any]] = []
    
    def audit_redaction_config_change(self, component: str, change_type: str, 
                                    old_value: Any, new_value: Any, 
                                    user_context: Optional[Dict[str, Any]] = None) -> None:
        """Audit redaction configuration changes"""
        timestamp = time.time()
        
        audit_event = {
            'timestamp': timestamp,
            'iso_timestamp': time.strftime('%Y-%m-%dT%H:%M:%S.%fZ', time.gmtime(timestamp)),
            'event_type': 'redaction_config_change',
            'component': component,
            'change_type': change_type,
            'old_value': str(old_value) if old_value is not None else None,
            'new_value': str(new_value) if new_value is not None else None,
            'user_context': user_context or {},
            'security_impact': self._assess_config_security_impact(change_type, old_value, new_value)
        }
        
        self.audit_events.append(audit_event)
        
        # Log high-impact changes
        if audit_event['security_impact'] in ['HIGH', 'CRITICAL']:
            self.logger.warning(f"High-impact redaction config change: {change_type} in {component}")
    
    def _assess_config_security_impact(self, change_type: str, old_value: Any, new_value: Any) -> str:
        """Assess security impact of configuration changes"""
        high_impact_changes = [
            'disable_rule', 'remove_rule', 'lower_redaction_level',
            'add_custom_processor', 'modify_sensitive_pattern'
        ]
        
        medium_impact_changes = [
            'enable_rule', 'add_rule', 'modify_replacement',
            'change_redaction_level'
        ]
        
        if change_type in high_impact_changes:
            return 'HIGH'
        elif change_type in medium_impact_changes:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def get_audit_trail(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get configuration audit trail"""
        events = self.audit_events
        if limit:
            events = events[-limit:]
        return events
    
    def clear_audit_trail(self) -> None:
        """Clear configuration audit trail"""
        self.audit_events.clear()