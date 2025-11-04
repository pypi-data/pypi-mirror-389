"""
Enhanced Kubernetes metadata collector with real API integration
"""

import os
import time
import logging
from typing import Dict, Any, Optional
from .interfaces import IMetadataCollector
from .models import KubernetesMetadata, SecurityContext

# Optional kubernetes imports
try:
    from kubernetes import client, config
    from kubernetes.client.rest import ApiException
    KUBERNETES_AVAILABLE = True
except ImportError:
    KUBERNETES_AVAILABLE = False
    # Create dummy classes for when kubernetes is not available
    class client:
        class CoreV1Api:
            pass
    class config:
        @staticmethod
        def load_incluster_config():
            pass
        @staticmethod
        def load_kube_config():
            pass
    class ApiException(Exception):
        pass


class KubernetesMetadataCollector(IMetadataCollector):
    """Enhanced Kubernetes metadata collector with real API integration"""
    
    def __init__(self, cache_ttl: int = 300, max_retries: int = 3):
        """
        Initialize the Kubernetes metadata collector
        
        Args:
            cache_ttl: Cache time-to-live in seconds (default: 5 minutes)
            max_retries: Maximum number of API retry attempts
        """
        self.cache_ttl = cache_ttl
        self.max_retries = max_retries
        self.logger = logging.getLogger(__name__)
        
        # Cache storage
        self._metadata_cache: Dict[str, Any] = {}
        self._cache_timestamps: Dict[str, float] = {}
        
        # Kubernetes client
        self._k8s_client: Optional[client.CoreV1Api] = None
        self._apps_client: Optional[client.AppsV1Api] = None
        
        # Pod information
        self._pod_name = os.getenv('HOSTNAME', '')
        self._namespace = self._get_namespace()
        
        # Initialize Kubernetes client
        self._initialize_k8s_client()
    
    def _get_namespace(self) -> str:
        """Get the current namespace"""
        # Try environment variable first
        namespace = os.getenv('KUBERNETES_NAMESPACE')
        if namespace:
            return namespace
        
        # Try reading from service account token
        try:
            with open('/var/run/secrets/kubernetes.io/serviceaccount/namespace', 'r') as f:
                return f.read().strip()
        except (FileNotFoundError, IOError):
            return 'default'
    
    def _initialize_k8s_client(self) -> None:
        """Initialize Kubernetes API client"""
        if not KUBERNETES_AVAILABLE:
            self.logger.warning("Kubernetes client library not available")
            self._k8s_client = None
            self._apps_client = None
            return
            
        try:
            # Try in-cluster configuration first
            if self.is_kubernetes_environment():
                config.load_incluster_config()
                self.logger.info("Loaded in-cluster Kubernetes configuration")
            else:
                # Fall back to kubeconfig for local development
                config.load_kube_config()
                self.logger.info("Loaded kubeconfig configuration")
            
            self._k8s_client = client.CoreV1Api()
            self._apps_client = client.AppsV1Api()
            
        except Exception as e:
            self.logger.warning(f"Failed to initialize Kubernetes client: {e}")
            self._k8s_client = None
            self._apps_client = None
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached data is still valid"""
        if cache_key not in self._cache_timestamps:
            return False
        
        return (time.time() - self._cache_timestamps[cache_key]) < self.cache_ttl
    
    def _get_cached_or_fetch(self, cache_key: str, fetch_func) -> Dict[str, Any]:
        """Get data from cache or fetch if expired"""
        if self._is_cache_valid(cache_key):
            return self._metadata_cache.get(cache_key, {})
        
        try:
            data = fetch_func()
            self._metadata_cache[cache_key] = data
            self._cache_timestamps[cache_key] = time.time()
            return data
        except Exception as e:
            self.logger.error(f"Failed to fetch {cache_key}: {e}")
            # Return cached data even if expired, or empty dict
            return self._metadata_cache.get(cache_key, {})
    
    def _retry_api_call(self, api_call, *args, **kwargs):
        """Retry API call with exponential backoff"""
        for attempt in range(self.max_retries):
            try:
                return api_call(*args, **kwargs)
            except ApiException as e:
                if attempt == self.max_retries - 1:
                    raise
                
                # Exponential backoff: 1s, 2s, 4s
                wait_time = 2 ** attempt
                self.logger.warning(f"API call failed (attempt {attempt + 1}), retrying in {wait_time}s: {e}")
                time.sleep(wait_time)
            except Exception as e:
                self.logger.error(f"Unexpected error in API call: {e}")
                raise
    
    def collect_pod_metadata(self) -> Dict[str, Any]:
        """Collect comprehensive pod metadata from Kubernetes API"""
        def _fetch_pod_metadata():
            if not self._k8s_client or not self._pod_name:
                return self._get_fallback_pod_metadata()
            
            try:
                pod = self._retry_api_call(
                    self._k8s_client.read_namespaced_pod,
                    name=self._pod_name,
                    namespace=self._namespace
                )
                
                metadata = {
                    'pod_name': pod.metadata.name,
                    'namespace': pod.metadata.namespace,
                    'labels': pod.metadata.labels or {},
                    'annotations': pod.metadata.annotations or {},
                    'service_account': pod.spec.service_account_name or 'default',
                    'node_name': pod.spec.node_name or 'unknown',
                    'pod_ip': pod.status.pod_ip or '',
                    'host_ip': pod.status.host_ip or '',
                    'phase': pod.status.phase or 'Unknown',
                    'creation_timestamp': pod.metadata.creation_timestamp.isoformat() if pod.metadata.creation_timestamp else '',
                    'uid': pod.metadata.uid or '',
                    'restart_policy': pod.spec.restart_policy or 'Always',
                    'dns_policy': pod.spec.dns_policy or 'ClusterFirst',
                    'priority_class_name': pod.spec.priority_class_name or '',
                    'scheduler_name': pod.spec.scheduler_name or 'default-scheduler',
                }
                
                # Add owner references for tracing back to controllers
                if pod.metadata.owner_references:
                    metadata['owner_references'] = [
                        {
                            'kind': owner.kind,
                            'name': owner.name,
                            'uid': owner.uid,
                            'controller': owner.controller or False,
                            'block_owner_deletion': owner.block_owner_deletion or False
                        }
                        for owner in pod.metadata.owner_references
                    ]
                else:
                    metadata['owner_references'] = []
                
                # Extract comprehensive container information
                if pod.spec.containers:
                    containers_info = []
                    total_limits = {'cpu': '0', 'memory': '0'}
                    total_requests = {'cpu': '0', 'memory': '0'}
                    
                    for container in pod.spec.containers:
                        container_info = {
                            'name': container.name,
                            'image': container.image,
                            'image_pull_policy': container.image_pull_policy or 'IfNotPresent',
                            'ports': [],
                            'env_vars': [],
                            'volume_mounts': [],
                            'resource_limits': {},
                            'resource_requests': {},
                            'working_dir': container.working_dir or '',
                            'command': container.command or [],
                            'args': container.args or []
                        }
                        
                        # Container ports
                        if container.ports:
                            container_info['ports'] = [
                                {
                                    'name': port.name or '',
                                    'container_port': port.container_port,
                                    'protocol': port.protocol or 'TCP',
                                    'host_port': port.host_port or None
                                }
                                for port in container.ports
                            ]
                        
                        # Environment variables (excluding sensitive ones)
                        if container.env:
                            for env_var in container.env:
                                if not self._is_sensitive_env_var(env_var.name):
                                    env_info = {'name': env_var.name}
                                    if env_var.value:
                                        env_info['value'] = env_var.value
                                    elif env_var.value_from:
                                        env_info['value_from'] = 'reference'
                                    container_info['env_vars'].append(env_info)
                        
                        # Volume mounts
                        if container.volume_mounts:
                            container_info['volume_mounts'] = [
                                {
                                    'name': mount.name,
                                    'mount_path': mount.mount_path,
                                    'read_only': mount.read_only or False,
                                    'sub_path': mount.sub_path or ''
                                }
                                for mount in container.volume_mounts
                            ]
                        
                        # Resource specifications
                        if container.resources:
                            if container.resources.limits:
                                container_info['resource_limits'] = dict(container.resources.limits)
                                # Aggregate limits
                                for resource, value in container.resources.limits.items():
                                    if resource in ['cpu', 'memory']:
                                        total_limits[resource] = self._add_resource_values(
                                            total_limits.get(resource, '0'), value
                                        )
                            
                            if container.resources.requests:
                                container_info['resource_requests'] = dict(container.resources.requests)
                                # Aggregate requests
                                for resource, value in container.resources.requests.items():
                                    if resource in ['cpu', 'memory']:
                                        total_requests[resource] = self._add_resource_values(
                                            total_requests.get(resource, '0'), value
                                        )
                        
                        containers_info.append(container_info)
                    
                    metadata['containers'] = containers_info
                    metadata['resource_limits'] = total_limits
                    metadata['resource_requests'] = total_requests
                else:
                    metadata['containers'] = []
                    metadata['resource_limits'] = {}
                    metadata['resource_requests'] = {}
                
                # Pod volumes
                if pod.spec.volumes:
                    metadata['volumes'] = [
                        {
                            'name': volume.name,
                            'type': self._get_volume_type(volume)
                        }
                        for volume in pod.spec.volumes
                    ]
                else:
                    metadata['volumes'] = []
                
                # Pod conditions
                if pod.status.conditions:
                    metadata['conditions'] = [
                        {
                            'type': condition.type,
                            'status': condition.status,
                            'reason': condition.reason or '',
                            'message': condition.message or '',
                            'last_transition_time': condition.last_transition_time.isoformat() if condition.last_transition_time else ''
                        }
                        for condition in pod.status.conditions
                    ]
                else:
                    metadata['conditions'] = []
                
                # Container statuses
                if pod.status.container_statuses:
                    metadata['container_statuses'] = [
                        {
                            'name': status.name,
                            'ready': status.ready,
                            'restart_count': status.restart_count,
                            'image': status.image,
                            'image_id': status.image_id or '',
                            'container_id': status.container_id or '',
                            'started': status.started or False
                        }
                        for status in pod.status.container_statuses
                    ]
                else:
                    metadata['container_statuses'] = []
                
                # Quality of Service class
                metadata['qos_class'] = pod.status.qos_class or 'BestEffort'
                
                return metadata
                
            except Exception as e:
                self.logger.error(f"Failed to collect pod metadata: {e}")
                return self._get_fallback_pod_metadata()
        
        return self._get_cached_or_fetch('pod_metadata', _fetch_pod_metadata)
    
    def collect_node_metadata(self) -> Dict[str, Any]:
        """Collect comprehensive node metadata from Kubernetes API"""
        def _fetch_node_metadata():
            if not self._k8s_client:
                return self._get_fallback_node_metadata()
            
            try:
                # First get pod to find node name
                pod_metadata = self.collect_pod_metadata()
                node_name = pod_metadata.get('node_name', 'unknown')
                
                if node_name == 'unknown':
                    return self._get_fallback_node_metadata()
                
                node = self._retry_api_call(
                    self._k8s_client.read_node,
                    name=node_name
                )
                
                metadata = {
                    'node_name': node.metadata.name,
                    'labels': node.metadata.labels or {},
                    'annotations': node.metadata.annotations or {},
                    'creation_timestamp': node.metadata.creation_timestamp.isoformat() if node.metadata.creation_timestamp else '',
                    'uid': node.metadata.uid or '',
                }
                
                # Extract comprehensive node information
                if node.status:
                    if node.status.node_info:
                        info = node.status.node_info
                        metadata.update({
                            'architecture': info.architecture or '',
                            'boot_id': info.boot_id or '',
                            'container_runtime_version': info.container_runtime_version or '',
                            'kernel_version': info.kernel_version or '',
                            'kube_proxy_version': info.kube_proxy_version or '',
                            'kubelet_version': info.kubelet_version or '',
                            'machine_id': info.machine_id or '',
                            'operating_system': info.operating_system or '',
                            'os_image': info.os_image or '',
                            'system_uuid': info.system_uuid or '',
                        })
                    
                    # Extract detailed capacity and allocatable resources
                    if node.status.capacity:
                        capacity = dict(node.status.capacity)
                        metadata['capacity'] = capacity
                        # Parse resource values for better understanding
                        metadata['capacity_parsed'] = self._parse_node_resources(capacity)
                    
                    if node.status.allocatable:
                        allocatable = dict(node.status.allocatable)
                        metadata['allocatable'] = allocatable
                        # Parse resource values for better understanding
                        metadata['allocatable_parsed'] = self._parse_node_resources(allocatable)
                    
                    # Calculate resource utilization if both capacity and allocatable are available
                    if node.status.capacity and node.status.allocatable:
                        metadata['resource_utilization'] = self._calculate_node_utilization(
                            dict(node.status.capacity), 
                            dict(node.status.allocatable)
                        )
                    
                    # Extract detailed conditions with timestamps
                    if node.status.conditions:
                        metadata['conditions'] = [
                            {
                                'type': condition.type,
                                'status': condition.status,
                                'reason': condition.reason or '',
                                'message': condition.message or '',
                                'last_heartbeat_time': condition.last_heartbeat_time.isoformat() if condition.last_heartbeat_time else '',
                                'last_transition_time': condition.last_transition_time.isoformat() if condition.last_transition_time else ''
                            }
                            for condition in node.status.conditions
                        ]
                        
                        # Extract ready status specifically
                        ready_condition = next(
                            (c for c in node.status.conditions if c.type == 'Ready'), 
                            None
                        )
                        metadata['ready'] = ready_condition.status == 'True' if ready_condition else False
                    
                    # Extract node addresses
                    if node.status.addresses:
                        addresses = {}
                        for address in node.status.addresses:
                            addresses[address.type] = address.address
                        metadata['addresses'] = addresses
                        
                        # Extract specific address types for convenience
                        metadata['internal_ip'] = addresses.get('InternalIP', '')
                        metadata['external_ip'] = addresses.get('ExternalIP', '')
                        metadata['hostname'] = addresses.get('Hostname', '')
                    
                    # Extract daemon endpoints
                    if node.status.daemon_endpoints:
                        if node.status.daemon_endpoints.kubelet_endpoint:
                            metadata['kubelet_port'] = node.status.daemon_endpoints.kubelet_endpoint.port
                    
                    # Extract node images (container images available on the node)
                    if node.status.images:
                        metadata['images'] = [
                            {
                                'names': image.names or [],
                                'size_bytes': image.size_bytes or 0
                            }
                            for image in node.status.images[:10]  # Limit to first 10 images
                        ]
                        metadata['total_images'] = len(node.status.images)
                    
                    # Extract volume stats if available
                    try:
                        if node.status.volumes_in_use:
                            metadata['volumes_in_use'] = list(node.status.volumes_in_use)
                        else:
                            metadata['volumes_in_use'] = []
                    except (AttributeError, TypeError):
                        metadata['volumes_in_use'] = []
                    
                    try:
                        if node.status.volumes_attached:
                            metadata['volumes_attached'] = [
                                {
                                    'name': vol.name,
                                    'device_path': vol.device_path or ''
                                }
                                for vol in node.status.volumes_attached
                            ]
                        else:
                            metadata['volumes_attached'] = []
                    except (AttributeError, TypeError):
                        metadata['volumes_attached'] = []
                
                # Extract node taints
                if node.spec and node.spec.taints:
                    metadata['taints'] = [
                        {
                            'key': taint.key,
                            'value': taint.value or '',
                            'effect': taint.effect,
                            'time_added': taint.time_added.isoformat() if taint.time_added else ''
                        }
                        for taint in node.spec.taints
                    ]
                else:
                    metadata['taints'] = []
                
                # Check if node is schedulable
                if node.spec:
                    metadata['unschedulable'] = node.spec.unschedulable or False
                    metadata['schedulable'] = not (node.spec.unschedulable or False)
                
                return metadata
                
            except Exception as e:
                self.logger.error(f"Failed to collect node metadata: {e}")
                return self._get_fallback_node_metadata()
        
        return self._get_cached_or_fetch('node_metadata', _fetch_node_metadata)
    
    def collect_deployment_metadata(self) -> Dict[str, Any]:
        """Collect comprehensive deployment, replicaset, and service metadata"""
        def _fetch_deployment_metadata():
            if not self._apps_client or not self._k8s_client:
                return self._get_fallback_deployment_metadata()
            
            try:
                metadata = {
                    'deployment': {},
                    'replicaset': {},
                    'services': [],
                    'ingresses': [],
                    'configmaps': [],
                    'secrets': []
                }
                
                # Get pod metadata to find owner references
                pod_metadata = self.collect_pod_metadata()
                
                if self._pod_name:
                    pod = self._retry_api_call(
                        self._k8s_client.read_namespaced_pod,
                        name=self._pod_name,
                        namespace=self._namespace
                    )
                    
                    # Trace ownership hierarchy: Pod -> ReplicaSet -> Deployment
                    if pod.metadata.owner_references:
                        for owner in pod.metadata.owner_references:
                            if owner.kind == 'ReplicaSet':
                                # Get ReplicaSet information
                                try:
                                    rs = self._retry_api_call(
                                        self._apps_client.read_namespaced_replica_set,
                                        name=owner.name,
                                        namespace=self._namespace
                                    )
                                    
                                    metadata['replicaset'] = {
                                        'name': rs.metadata.name,
                                        'uid': rs.metadata.uid,
                                        'labels': rs.metadata.labels or {},
                                        'annotations': rs.metadata.annotations or {},
                                        'creation_timestamp': rs.metadata.creation_timestamp.isoformat() if rs.metadata.creation_timestamp else '',
                                        'replicas': rs.spec.replicas or 0,
                                        'ready_replicas': rs.status.ready_replicas or 0,
                                        'available_replicas': rs.status.available_replicas or 0,
                                        'fully_labeled_replicas': rs.status.fully_labeled_replicas or 0,
                                        'observed_generation': rs.status.observed_generation or 0
                                    }
                                    
                                    # Find parent Deployment
                                    if rs.metadata.owner_references:
                                        for rs_owner in rs.metadata.owner_references:
                                            if rs_owner.kind == 'Deployment':
                                                deployment = self._retry_api_call(
                                                    self._apps_client.read_namespaced_deployment,
                                                    name=rs_owner.name,
                                                    namespace=self._namespace
                                                )
                                                
                                                metadata['deployment'] = {
                                                    'name': deployment.metadata.name,
                                                    'uid': deployment.metadata.uid,
                                                    'labels': deployment.metadata.labels or {},
                                                    'annotations': deployment.metadata.annotations or {},
                                                    'creation_timestamp': deployment.metadata.creation_timestamp.isoformat() if deployment.metadata.creation_timestamp else '',
                                                    'generation': deployment.metadata.generation or 0,
                                                    'replicas': deployment.spec.replicas or 0,
                                                    'strategy_type': deployment.spec.strategy.type if deployment.spec.strategy else 'RollingUpdate',
                                                    'ready_replicas': deployment.status.ready_replicas or 0,
                                                    'available_replicas': deployment.status.available_replicas or 0,
                                                    'unavailable_replicas': deployment.status.unavailable_replicas or 0,
                                                    'updated_replicas': deployment.status.updated_replicas or 0,
                                                    'observed_generation': deployment.status.observed_generation or 0,
                                                    'collision_count': deployment.status.collision_count or 0
                                                }
                                                
                                                # Extract deployment conditions
                                                if deployment.status.conditions:
                                                    metadata['deployment']['conditions'] = [
                                                        {
                                                            'type': condition.type,
                                                            'status': condition.status,
                                                            'reason': condition.reason or '',
                                                            'message': condition.message or '',
                                                            'last_transition_time': condition.last_transition_time.isoformat() if condition.last_transition_time else '',
                                                            'last_update_time': condition.last_update_time.isoformat() if condition.last_update_time else ''
                                                        }
                                                        for condition in deployment.status.conditions
                                                    ]
                                                
                                                # Extract rolling update strategy details
                                                if deployment.spec.strategy and deployment.spec.strategy.rolling_update:
                                                    ru = deployment.spec.strategy.rolling_update
                                                    metadata['deployment']['rolling_update_strategy'] = {
                                                        'max_surge': str(ru.max_surge) if ru.max_surge else '25%',
                                                        'max_unavailable': str(ru.max_unavailable) if ru.max_unavailable else '25%'
                                                    }
                                                
                                                break
                                except Exception as e:
                                    self.logger.debug(f"Could not get deployment/replicaset info: {e}")
                            
                            # Handle other controller types
                            elif owner.kind in ['DaemonSet', 'StatefulSet', 'Job', 'CronJob']:
                                metadata['controller'] = {
                                    'kind': owner.kind,
                                    'name': owner.name,
                                    'uid': owner.uid
                                }
                
                # Find associated services
                try:
                    services = self._retry_api_call(
                        self._k8s_client.list_namespaced_service,
                        namespace=self._namespace
                    )
                    
                    pod_labels = pod_metadata.get('labels', {})
                    
                    for service in services.items:
                        if service.spec.selector:
                            # Check if service selector matches pod labels
                            if all(pod_labels.get(k) == v for k, v in service.spec.selector.items()):
                                service_info = {
                                    'name': service.metadata.name,
                                    'uid': service.metadata.uid,
                                    'labels': service.metadata.labels or {},
                                    'annotations': service.metadata.annotations or {},
                                    'type': service.spec.type or 'ClusterIP',
                                    'cluster_ip': service.spec.cluster_ip or '',
                                    'external_ips': service.spec.external_i_ps or [],
                                    'session_affinity': service.spec.session_affinity or 'None',
                                    'ports': []
                                }
                                
                                # Extract port information
                                if service.spec.ports:
                                    service_info['ports'] = [
                                        {
                                            'name': port.name or '',
                                            'port': port.port,
                                            'target_port': str(port.target_port) if port.target_port else '',
                                            'protocol': port.protocol or 'TCP',
                                            'node_port': port.node_port if port.node_port else None
                                        }
                                        for port in service.spec.ports
                                    ]
                                
                                # Extract LoadBalancer status if applicable
                                if service.spec.type == 'LoadBalancer' and service.status.load_balancer:
                                    if service.status.load_balancer.ingress:
                                        service_info['load_balancer_ingress'] = [
                                            {
                                                'ip': ingress.ip or '',
                                                'hostname': ingress.hostname or ''
                                            }
                                            for ingress in service.status.load_balancer.ingress
                                        ]
                                
                                metadata['services'].append(service_info)
                    
                    # Set primary service name for backward compatibility
                    if metadata['services']:
                        metadata['service_name'] = metadata['services'][0]['name']
                
                except Exception as e:
                    self.logger.debug(f"Could not get service info: {e}")
                
                # Find associated ConfigMaps and Secrets referenced by the pod
                try:
                    if pod.spec.volumes:
                        for volume in pod.spec.volumes:
                            if volume.config_map:
                                try:
                                    cm = self._retry_api_call(
                                        self._k8s_client.read_namespaced_config_map,
                                        name=volume.config_map.name,
                                        namespace=self._namespace
                                    )
                                    metadata['configmaps'].append({
                                        'name': cm.metadata.name,
                                        'uid': cm.metadata.uid,
                                        'data_keys': list(cm.data.keys()) if cm.data else [],
                                        'binary_data_keys': list(cm.binary_data.keys()) if cm.binary_data else []
                                    })
                                except Exception as e:
                                    self.logger.debug(f"Could not get ConfigMap {volume.config_map.name}: {e}")
                            
                            elif volume.secret:
                                try:
                                    secret = self._retry_api_call(
                                        self._k8s_client.read_namespaced_secret,
                                        name=volume.secret.secret_name,
                                        namespace=self._namespace
                                    )
                                    metadata['secrets'].append({
                                        'name': secret.metadata.name,
                                        'uid': secret.metadata.uid,
                                        'type': secret.type or 'Opaque',
                                        'data_keys': list(secret.data.keys()) if secret.data else []
                                    })
                                except Exception as e:
                                    self.logger.debug(f"Could not get Secret {volume.secret.secret_name}: {e}")
                
                except Exception as e:
                    self.logger.debug(f"Could not get ConfigMap/Secret info: {e}")
                
                # Find associated Ingresses
                try:
                    # Try networking.k8s.io/v1 first, then extensions/v1beta1
                    try:
                        networking_client = client.NetworkingV1Api()
                        ingresses = self._retry_api_call(
                            networking_client.list_namespaced_ingress,
                            namespace=self._namespace
                        )
                    except:
                        # Fallback to extensions API for older clusters
                        extensions_client = client.ExtensionsV1beta1Api()
                        ingresses = self._retry_api_call(
                            extensions_client.list_namespaced_ingress,
                            namespace=self._namespace
                        )
                    
                    service_names = [svc['name'] for svc in metadata['services']]
                    
                    for ingress in ingresses.items:
                        if ingress.spec.rules:
                            for rule in ingress.spec.rules:
                                if rule.http and rule.http.paths:
                                    for path in rule.http.paths:
                                        if path.backend and hasattr(path.backend, 'service') and path.backend.service:
                                            if path.backend.service.name in service_names:
                                                metadata['ingresses'].append({
                                                    'name': ingress.metadata.name,
                                                    'uid': ingress.metadata.uid,
                                                    'host': rule.host or '',
                                                    'path': path.path or '/',
                                                    'service_name': path.backend.service.name,
                                                    'service_port': path.backend.service.port.number if path.backend.service.port else None
                                                })
                                                break
                
                except Exception as e:
                    self.logger.debug(f"Could not get Ingress info: {e}")
                
                # Add backward compatibility fields
                if metadata['deployment']:
                    metadata['deployment_name'] = metadata['deployment']['name']
                    metadata['deployment_labels'] = metadata['deployment']['labels']
                    metadata['deployment_annotations'] = metadata['deployment']['annotations']
                    metadata['deployment_uid'] = metadata['deployment']['uid']
                    metadata['replicas'] = metadata['deployment']['replicas']
                    metadata['ready_replicas'] = metadata['deployment']['ready_replicas']
                
                return metadata
                
            except Exception as e:
                self.logger.error(f"Failed to collect deployment metadata: {e}")
                return self._get_fallback_deployment_metadata()
        
        return self._get_cached_or_fetch('deployment_metadata', _fetch_deployment_metadata)
    
    def get_security_context(self) -> Dict[str, Any]:
        """Get container security context information"""
        def _fetch_security_context():
            if not self._k8s_client or not self._pod_name:
                return self._get_fallback_security_context()
            
            try:
                pod = self._retry_api_call(
                    self._k8s_client.read_namespaced_pod,
                    name=self._pod_name,
                    namespace=self._namespace
                )
                
                security_context = SecurityContext()
                
                # Get pod-level security context
                if pod.spec.security_context:
                    pod_sc = pod.spec.security_context
                    security_context.run_as_non_root = pod_sc.run_as_non_root
                    if pod_sc.run_as_user is not None:
                        security_context.user_id = pod_sc.run_as_user
                    if pod_sc.run_as_group is not None:
                        security_context.group_id = pod_sc.run_as_group
                
                # Get container-level security context (first container)
                if pod.spec.containers:
                    container = pod.spec.containers[0]
                    if container.security_context:
                        container_sc = container.security_context
                        
                        # Container settings override pod settings
                        if container_sc.run_as_non_root is not None:
                            security_context.run_as_non_root = container_sc.run_as_non_root
                        if container_sc.run_as_user is not None:
                            security_context.user_id = container_sc.run_as_user
                        if container_sc.run_as_group is not None:
                            security_context.group_id = container_sc.run_as_group
                        if container_sc.read_only_root_filesystem is not None:
                            security_context.read_only_root_filesystem = container_sc.read_only_root_filesystem
                        if container_sc.allow_privilege_escalation is not None:
                            security_context.allow_privilege_escalation = container_sc.allow_privilege_escalation
                        
                        # Capabilities
                        if container_sc.capabilities:
                            caps = {}
                            if container_sc.capabilities.add:
                                caps['add'] = list(container_sc.capabilities.add)
                            if container_sc.capabilities.drop:
                                caps['drop'] = list(container_sc.capabilities.drop)
                            security_context.capabilities = caps
                
                # Add current process info as fallback
                if security_context.user_id is None and hasattr(os, 'getuid'):
                    security_context.user_id = os.getuid()
                if security_context.group_id is None and hasattr(os, 'getgid'):
                    security_context.group_id = os.getgid()
                
                return security_context.to_dict()
                
            except Exception as e:
                self.logger.error(f"Failed to collect security context: {e}")
                return self._get_fallback_security_context()
        
        return self._get_cached_or_fetch('security_context', _fetch_security_context)
    
    def is_kubernetes_environment(self) -> bool:
        """Check if running in Kubernetes environment"""
        return os.path.exists('/var/run/secrets/kubernetes.io/serviceaccount')
    
    def refresh_metadata_cache(self) -> None:
        """Refresh cached metadata from Kubernetes API"""
        self.logger.info("Refreshing metadata cache")
        
        # Clear cache timestamps to force refresh
        self._cache_timestamps.clear()
        
        # Fetch fresh data
        self.collect_pod_metadata()
        self.collect_node_metadata()
        self.collect_deployment_metadata()
        self.get_security_context()
        
        self.logger.info("Metadata cache refreshed")
    
    def get_all_metadata(self) -> Dict[str, Any]:
        """Get all collected metadata in a single call"""
        return {
            'pod': self.collect_pod_metadata(),
            'node': self.collect_node_metadata(),
            'deployment': self.collect_deployment_metadata(),
            'security_context': self.get_security_context(),
            'kubernetes_environment': self.is_kubernetes_environment(),
            'cache_info': {
                'cache_ttl': self.cache_ttl,
                'cached_keys': list(self._cache_timestamps.keys()),
                'cache_ages': {
                    key: time.time() - timestamp 
                    for key, timestamp in self._cache_timestamps.items()
                }
            }
        }
    
    # Fallback methods for when Kubernetes API is unavailable
    def _get_fallback_pod_metadata(self) -> Dict[str, Any]:
        """Get pod metadata from environment variables as fallback"""
        return {
            'pod_name': os.getenv('HOSTNAME', 'unknown'),
            'namespace': self._namespace,
            'service_account': os.getenv('KUBERNETES_SERVICE_ACCOUNT', 'default'),
            'labels': {},
            'annotations': {},
            'resource_limits': {},
            'resource_requests': {},
            'node_name': os.getenv('KUBERNETES_NODE_NAME', 'unknown'),
            'pod_ip': '',
            'host_ip': '',
            'phase': 'Unknown',
            'creation_timestamp': '',
            'uid': '',
            'restart_policy': 'Always',
            'dns_policy': 'ClusterFirst',
            'priority_class_name': '',
            'scheduler_name': 'default-scheduler',
            'owner_references': [],
            'containers': [],
            'volumes': [],
            'conditions': [],
            'container_statuses': [],
            'qos_class': 'BestEffort',
        }
    
    def _get_fallback_node_metadata(self) -> Dict[str, Any]:
        """Get node metadata from environment variables as fallback"""
        return {
            'node_name': os.getenv('KUBERNETES_NODE_NAME', 'unknown'),
            'labels': {},
            'annotations': {},
            'capacity': {},
            'allocatable': {},
            'capacity_parsed': {},
            'allocatable_parsed': {},
            'resource_utilization': {},
            'conditions': [],
            'ready': False,
            'addresses': {},
            'internal_ip': '',
            'external_ip': '',
            'hostname': '',
            'kubelet_port': 10250,
            'images': [],
            'total_images': 0,
            'volumes_in_use': [],
            'volumes_attached': [],
            'taints': [],
            'unschedulable': False,
            'schedulable': True,
            'architecture': '',
            'boot_id': '',
            'container_runtime_version': '',
            'kernel_version': '',
            'kube_proxy_version': '',
            'kubelet_version': '',
            'machine_id': '',
            'operating_system': '',
            'os_image': '',
            'system_uuid': '',
            'creation_timestamp': '',
            'uid': '',
        }
    
    def _get_fallback_deployment_metadata(self) -> Dict[str, Any]:
        """Get deployment metadata from environment variables as fallback"""
        return {
            'deployment': {},
            'replicaset': {},
            'services': [],
            'ingresses': [],
            'configmaps': [],
            'secrets': [],
            'controller': {},
            # Backward compatibility fields
            'deployment_name': os.getenv('KUBERNETES_DEPLOYMENT_NAME', 'unknown'),
            'service_name': os.getenv('KUBERNETES_SERVICE_NAME', 'unknown'),
            'deployment_labels': {},
            'deployment_annotations': {},
            'deployment_uid': '',
            'replicas': 0,
            'ready_replicas': 0,
        }
    
    def _get_fallback_security_context(self) -> Dict[str, Any]:
        """Get security context from process info as fallback"""
        security_context = SecurityContext()
        
        if hasattr(os, 'getuid'):
            security_context.user_id = os.getuid()
        if hasattr(os, 'getgid'):
            security_context.group_id = os.getgid()
        
        return security_context.to_dict()
    
    def _is_sensitive_env_var(self, name: str) -> bool:
        """Check if environment variable name indicates sensitive data"""
        sensitive_patterns = [
            'password', 'secret', 'key', 'token', 'credential', 
            'auth', 'cert', 'private', 'api_key', 'access_key'
        ]
        name_lower = name.lower()
        return any(pattern in name_lower for pattern in sensitive_patterns)
    
    def _add_resource_values(self, value1: str, value2: str) -> str:
        """Add two Kubernetes resource values (simplified)"""
        # This is a simplified implementation - in production you'd want proper unit conversion
        try:
            # Handle CPU values (millicores)
            if 'm' in value1 or 'm' in value2:
                val1 = int(value1.replace('m', '')) if 'm' in value1 else int(value1) * 1000
                val2 = int(value2.replace('m', '')) if 'm' in value2 else int(value2) * 1000
                return f"{val1 + val2}m"
            
            # Handle memory values (bytes, Ki, Mi, Gi)
            def parse_memory(val):
                if val.endswith('Ki'):
                    return int(val[:-2]) * 1024
                elif val.endswith('Mi'):
                    return int(val[:-2]) * 1024 * 1024
                elif val.endswith('Gi'):
                    return int(val[:-2]) * 1024 * 1024 * 1024
                else:
                    return int(val)
            
            if any(unit in value1 + value2 for unit in ['Ki', 'Mi', 'Gi']):
                total_bytes = parse_memory(value1) + parse_memory(value2)
                # Convert back to appropriate unit
                if total_bytes >= 1024 * 1024 * 1024:
                    return f"{total_bytes // (1024 * 1024 * 1024)}Gi"
                elif total_bytes >= 1024 * 1024:
                    return f"{total_bytes // (1024 * 1024)}Mi"
                elif total_bytes >= 1024:
                    return f"{total_bytes // 1024}Ki"
                else:
                    return str(total_bytes)
            
            # Fallback to simple addition
            return str(int(value1) + int(value2))
        except (ValueError, AttributeError):
            return value2  # Return the second value if parsing fails
    
    def _get_volume_type(self, volume) -> str:
        """Determine the type of a Kubernetes volume"""
        if volume.config_map:
            return 'configMap'
        elif volume.secret:
            return 'secret'
        elif volume.empty_dir:
            return 'emptyDir'
        elif volume.host_path:
            return 'hostPath'
        elif volume.persistent_volume_claim:
            return 'persistentVolumeClaim'
        elif volume.projected:
            return 'projected'
        elif volume.downward_api:
            return 'downwardAPI'
        elif volume.nfs:
            return 'nfs'
        elif volume.aws_elastic_block_store:
            return 'awsElasticBlockStore'
        elif volume.azure_disk:
            return 'azureDisk'
        elif volume.gce_persistent_disk:
            return 'gcePersistentDisk'
        else:
            return 'unknown'
    
    def _parse_node_resources(self, resources: Dict[str, str]) -> Dict[str, Any]:
        """Parse node resource values into more readable format"""
        parsed = {}
        
        for resource, value in resources.items():
            if resource == 'cpu':
                # Parse CPU values
                if 'm' in value:
                    parsed[resource] = {
                        'raw': value,
                        'millicores': int(value.replace('m', '')),
                        'cores': int(value.replace('m', '')) / 1000
                    }
                else:
                    cores = int(value)
                    parsed[resource] = {
                        'raw': value,
                        'millicores': cores * 1000,
                        'cores': cores
                    }
            elif resource == 'memory':
                # Parse memory values
                parsed[resource] = {
                    'raw': value,
                    'bytes': self._parse_memory_to_bytes(value),
                    'human_readable': self._format_bytes(self._parse_memory_to_bytes(value))
                }
            elif resource in ['ephemeral-storage', 'storage']:
                # Parse storage values
                parsed[resource] = {
                    'raw': value,
                    'bytes': self._parse_memory_to_bytes(value),
                    'human_readable': self._format_bytes(self._parse_memory_to_bytes(value))
                }
            else:
                # For other resources (pods, etc.), keep as-is
                parsed[resource] = {
                    'raw': value,
                    'value': int(value) if value.isdigit() else value
                }
        
        return parsed
    
    def _parse_memory_to_bytes(self, value: str) -> int:
        """Convert Kubernetes memory value to bytes"""
        try:
            if value.endswith('Ki'):
                return int(value[:-2]) * 1024
            elif value.endswith('Mi'):
                return int(value[:-2]) * 1024 * 1024
            elif value.endswith('Gi'):
                return int(value[:-2]) * 1024 * 1024 * 1024
            elif value.endswith('Ti'):
                return int(value[:-2]) * 1024 * 1024 * 1024 * 1024
            elif value.endswith('k'):
                return int(value[:-1]) * 1000
            elif value.endswith('M'):
                return int(value[:-1]) * 1000 * 1000
            elif value.endswith('G'):
                return int(value[:-1]) * 1000 * 1000 * 1000
            elif value.endswith('T'):
                return int(value[:-1]) * 1000 * 1000 * 1000 * 1000
            else:
                return int(value)
        except (ValueError, AttributeError):
            return 0
    
    def _format_bytes(self, bytes_value: int) -> str:
        """Format bytes into human-readable string"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.1f}{unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.1f}PB"
    
    def _calculate_node_utilization(self, capacity: Dict[str, str], allocatable: Dict[str, str]) -> Dict[str, Any]:
        """Calculate node resource utilization percentages"""
        utilization = {}
        
        for resource in ['cpu', 'memory', 'ephemeral-storage']:
            if resource in capacity and resource in allocatable:
                try:
                    if resource == 'cpu':
                        cap_val = int(capacity[resource].replace('m', '')) if 'm' in capacity[resource] else int(capacity[resource]) * 1000
                        alloc_val = int(allocatable[resource].replace('m', '')) if 'm' in allocatable[resource] else int(allocatable[resource]) * 1000
                    else:
                        cap_val = self._parse_memory_to_bytes(capacity[resource])
                        alloc_val = self._parse_memory_to_bytes(allocatable[resource])
                    
                    if cap_val > 0:
                        utilization[resource] = {
                            'capacity': capacity[resource],
                            'allocatable': allocatable[resource],
                            'reserved_percentage': round((1 - alloc_val / cap_val) * 100, 2),
                            'allocatable_percentage': round((alloc_val / cap_val) * 100, 2)
                        }
                except (ValueError, ZeroDivisionError):
                    utilization[resource] = {
                        'capacity': capacity[resource],
                        'allocatable': allocatable[resource],
                        'reserved_percentage': 0,
                        'allocatable_percentage': 100
                    }
        
        return utilization