"""
CloudWatch Auto-Configuration

Automatic log group and stream creation with intelligent tagging strategies.
"""

import os
import time
import logging
from typing import Dict, Optional, List, Any
from datetime import datetime

try:
    import boto3
    from botocore.exceptions import ClientError, BotoCoreError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False
    boto3 = None
    ClientError = Exception
    BotoCoreError = Exception

from .models import CloudWatchConfig, CloudWatchDestination


class CloudWatchAutoConfigurator:
    """Handles automatic CloudWatch configuration and setup."""
    
    def __init__(self, region: str = None):
        if not BOTO3_AVAILABLE:
            raise ImportError("boto3 is required for CloudWatch auto-configuration")
        
        self.region = region or os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')
        self.client = boto3.client('logs', region_name=self.region)
        
        # Cache for existing resources
        self._log_groups_cache: Dict[str, Dict] = {}
        self._log_streams_cache: Dict[str, List[str]] = {}
        self._cache_ttl = 300  # 5 minutes
        self._last_cache_update = 0
    
    def auto_configure(self, 
                      service_name: str,
                      environment: str = None,
                      namespace: str = None,
                      additional_tags: Dict[str, str] = None) -> CloudWatchConfig:
        """Auto-configure CloudWatch settings for a service."""
        
        # Detect environment if not provided
        if not environment:
            environment = self._detect_environment()
        
        # Detect namespace if not provided
        if not namespace:
            namespace = self._detect_kubernetes_namespace()
        
        # Generate log group and stream names
        log_group_name = self._generate_log_group_name(service_name, environment, namespace)
        log_stream_name = self._generate_log_stream_name(service_name)
        
        # Generate tags
        tags = self._generate_tags(service_name, environment, namespace, additional_tags)
        
        # Create CloudWatch configuration
        config = CloudWatchConfig(
            region=self.region,
            log_group_name=log_group_name,
            log_stream_name=log_stream_name,
            auto_create_group=True,
            auto_create_stream=True,
            default_tags=tags
        )
        
        # Ensure resources exist
        self._ensure_log_group(log_group_name, tags)
        self._ensure_log_stream(log_group_name, log_stream_name)
        
        return config
    
    def create_multi_destination_config(self,
                                      service_name: str,
                                      environments: List[str] = None,
                                      regions: List[str] = None) -> List[CloudWatchDestination]:
        """Create multi-destination configuration."""
        
        destinations = []
        
        # Default environments and regions
        if not environments:
            environments = [self._detect_environment()]
        
        if not regions:
            regions = [self.region]
        
        priority = 1
        
        for env in environments:
            for region in regions:
                # Create destination config
                config = CloudWatchConfig(
                    region=region,
                    log_group_name=self._generate_log_group_name(service_name, env),
                    log_stream_name=self._generate_log_stream_name(service_name),
                    auto_create_group=True,
                    auto_create_stream=True,
                    default_tags=self._generate_tags(service_name, env)
                )
                
                destination = CloudWatchDestination(
                    name=f"{service_name}-{env}-{region}",
                    region=region,
                    log_group=config.log_group_name,
                    log_stream=config.log_stream_name,
                    config=config,
                    priority=priority,
                    enabled=True
                )
                
                destinations.append(destination)
                priority += 1
        
        return destinations
    
    def _detect_environment(self) -> str:
        """Detect the current environment."""
        # Check environment variables
        env = os.environ.get('ENVIRONMENT') or os.environ.get('ENV')
        if env:
            return env.lower()
        
        # Check for common environment indicators
        if os.environ.get('AWS_EXECUTION_ENV'):
            return 'aws'
        
        # Check Kubernetes environment
        if os.path.exists('/var/run/secrets/kubernetes.io'):
            # Try to determine from namespace or labels
            namespace = self._detect_kubernetes_namespace()
            if 'prod' in namespace.lower():
                return 'production'
            elif 'stag' in namespace.lower():
                return 'staging'
            elif 'dev' in namespace.lower():
                return 'development'
            else:
                return 'kubernetes'
        
        # Default
        return 'development'
    
    def _detect_kubernetes_namespace(self) -> str:
        """Detect Kubernetes namespace."""
        # Try to read from service account
        try:
            with open('/var/run/secrets/kubernetes.io/serviceaccount/namespace', 'r') as f:
                return f.read().strip()
        except (FileNotFoundError, PermissionError):
            pass
        
        # Check environment variable
        namespace = os.environ.get('KUBERNETES_NAMESPACE') or os.environ.get('K8S_NAMESPACE')
        if namespace:
            return namespace
        
        # Default
        return 'default'
    
    def _generate_log_group_name(self, 
                                service_name: str, 
                                environment: str = None,
                                namespace: str = None) -> str:
        """Generate a log group name following AWS best practices."""
        
        parts = ['/aws/eks']
        
        if namespace and namespace != 'default':
            parts.append(namespace)
        
        if environment:
            parts.append(environment)
        
        parts.append(service_name)
        
        return '/'.join(parts)
    
    def _generate_log_stream_name(self, service_name: str) -> str:
        """Generate a log stream name."""
        
        # Include hostname/pod name for uniqueness
        hostname = os.environ.get('HOSTNAME', 'unknown')
        
        # Include timestamp for additional uniqueness
        timestamp = datetime.utcnow().strftime('%Y%m%d')
        
        return f"{service_name}-{hostname}-{timestamp}"
    
    def _generate_tags(self, 
                      service_name: str,
                      environment: str = None,
                      namespace: str = None,
                      additional_tags: Dict[str, str] = None) -> Dict[str, str]:
        """Generate tags for CloudWatch resources."""
        
        tags = {
            'Service': service_name,
            'ManagedBy': 'ucbl-logger',
            'CreatedAt': datetime.utcnow().isoformat()
        }
        
        if environment:
            tags['Environment'] = environment
        
        if namespace:
            tags['Namespace'] = namespace
        
        # Add Kubernetes-specific tags if available
        pod_name = os.environ.get('HOSTNAME')
        if pod_name:
            tags['PodName'] = pod_name
        
        node_name = os.environ.get('NODE_NAME')
        if node_name:
            tags['NodeName'] = node_name
        
        cluster_name = os.environ.get('CLUSTER_NAME')
        if cluster_name:
            tags['ClusterName'] = cluster_name
        
        # Add additional tags
        if additional_tags:
            tags.update(additional_tags)
        
        return tags
    
    def _ensure_log_group(self, log_group_name: str, tags: Dict[str, str]) -> None:
        """Ensure log group exists."""
        try:
            # Check if log group exists
            if self._log_group_exists(log_group_name):
                return
            
            # Create log group
            self.client.create_log_group(
                logGroupName=log_group_name,
                tags=tags
            )
            
            # Set retention policy (default to 30 days)
            retention_days = int(os.environ.get('LOG_RETENTION_DAYS', '30'))
            if retention_days > 0:
                self.client.put_retention_policy(
                    logGroupName=log_group_name,
                    retentionInDays=retention_days
                )
            
            logging.info(f"Created CloudWatch log group: {log_group_name}")
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code == 'ResourceAlreadyExistsException':
                # Log group already exists, that's fine
                pass
            else:
                logging.error(f"Failed to create log group {log_group_name}: {e}")
                raise
    
    def _ensure_log_stream(self, log_group_name: str, log_stream_name: str) -> None:
        """Ensure log stream exists."""
        try:
            # Check if log stream exists
            if self._log_stream_exists(log_group_name, log_stream_name):
                return
            
            # Create log stream
            self.client.create_log_stream(
                logGroupName=log_group_name,
                logStreamName=log_stream_name
            )
            
            logging.info(f"Created CloudWatch log stream: {log_stream_name}")
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code == 'ResourceAlreadyExistsException':
                # Log stream already exists, that's fine
                pass
            else:
                logging.error(f"Failed to create log stream {log_stream_name}: {e}")
                raise
    
    def _log_group_exists(self, log_group_name: str) -> bool:
        """Check if log group exists."""
        try:
            self._refresh_cache_if_needed()
            
            if log_group_name in self._log_groups_cache:
                return True
            
            # Query CloudWatch
            response = self.client.describe_log_groups(
                logGroupNamePrefix=log_group_name,
                limit=1
            )
            
            for group in response.get('logGroups', []):
                if group['logGroupName'] == log_group_name:
                    self._log_groups_cache[log_group_name] = group
                    return True
            
            return False
            
        except Exception as e:
            logging.error(f"Error checking log group existence: {e}")
            return False
    
    def _log_stream_exists(self, log_group_name: str, log_stream_name: str) -> bool:
        """Check if log stream exists."""
        try:
            self._refresh_cache_if_needed()
            
            cache_key = log_group_name
            if cache_key in self._log_streams_cache:
                return log_stream_name in self._log_streams_cache[cache_key]
            
            # Query CloudWatch
            response = self.client.describe_log_streams(
                logGroupName=log_group_name,
                logStreamNamePrefix=log_stream_name,
                limit=1
            )
            
            stream_names = [stream['logStreamName'] for stream in response.get('logStreams', [])]
            self._log_streams_cache[cache_key] = stream_names
            
            return log_stream_name in stream_names
            
        except Exception as e:
            logging.error(f"Error checking log stream existence: {e}")
            return False
    
    def _refresh_cache_if_needed(self) -> None:
        """Refresh cache if TTL expired."""
        current_time = time.time()
        if current_time - self._last_cache_update > self._cache_ttl:
            self._log_groups_cache.clear()
            self._log_streams_cache.clear()
            self._last_cache_update = current_time
    
    def get_existing_log_groups(self, prefix: str = None) -> List[Dict[str, Any]]:
        """Get existing log groups."""
        try:
            kwargs = {}
            if prefix:
                kwargs['logGroupNamePrefix'] = prefix
            
            response = self.client.describe_log_groups(**kwargs)
            return response.get('logGroups', [])
            
        except Exception as e:
            logging.error(f"Error getting log groups: {e}")
            return []
    
    def cleanup_old_log_streams(self, 
                               log_group_name: str, 
                               retention_hours: int = 24) -> int:
        """Clean up old log streams."""
        try:
            cutoff_time = int((time.time() - (retention_hours * 3600)) * 1000)
            
            response = self.client.describe_log_streams(
                logGroupName=log_group_name,
                orderBy='LastEventTime',
                descending=False
            )
            
            deleted_count = 0
            
            for stream in response.get('logStreams', []):
                last_event_time = stream.get('lastEventTime', 0)
                
                if last_event_time < cutoff_time:
                    try:
                        self.client.delete_log_stream(
                            logGroupName=log_group_name,
                            logStreamName=stream['logStreamName']
                        )
                        deleted_count += 1
                    except ClientError as e:
                        logging.warning(f"Could not delete log stream {stream['logStreamName']}: {e}")
            
            return deleted_count
            
        except Exception as e:
            logging.error(f"Error cleaning up log streams: {e}")
            return 0