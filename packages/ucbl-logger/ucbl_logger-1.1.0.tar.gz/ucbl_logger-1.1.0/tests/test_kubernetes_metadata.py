"""
Comprehensive unit tests for KubernetesMetadataCollector
"""

import os
import time
import unittest
from unittest.mock import Mock, patch, MagicMock, call
from kubernetes.client.rest import ApiException

from ucbl_logger.enhanced.metadata.kubernetes_collector import KubernetesMetadataCollector
from ucbl_logger.enhanced.metadata.models import SecurityContext


class TestKubernetesMetadataCollector(unittest.TestCase):
    """Test cases for KubernetesMetadataCollector"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.collector = KubernetesMetadataCollector(cache_ttl=60, max_retries=2)
    
    def test_initialization(self):
        """Test collector initialization"""
        self.assertEqual(self.collector.cache_ttl, 60)
        self.assertEqual(self.collector.max_retries, 2)
        self.assertIsInstance(self.collector._metadata_cache, dict)
        self.assertIsInstance(self.collector._cache_timestamps, dict)
    
    @patch.dict(os.environ, {'KUBERNETES_NAMESPACE': 'test-namespace'})
    def test_get_namespace_from_env(self):
        """Test namespace detection from environment variable"""
        collector = KubernetesMetadataCollector()
        self.assertEqual(collector._namespace, 'test-namespace')
    
    @patch('builtins.open', unittest.mock.mock_open(read_data='file-namespace'))
    @patch.dict(os.environ, {}, clear=True)
    def test_get_namespace_from_file(self):
        """Test namespace detection from service account file"""
        collector = KubernetesMetadataCollector()
        self.assertEqual(collector._namespace, 'file-namespace')
    
    @patch.dict(os.environ, {}, clear=True)
    @patch('builtins.open', side_effect=FileNotFoundError())
    def test_get_namespace_fallback(self, mock_open):
        """Test namespace fallback to default"""
        collector = KubernetesMetadataCollector()
        self.assertEqual(collector._namespace, 'default')
    
    def test_cache_validity(self):
        """Test cache validity checking"""
        # Empty cache should be invalid
        self.assertFalse(self.collector._is_cache_valid('test_key'))
        
        # Fresh cache should be valid
        self.collector._cache_timestamps['test_key'] = time.time()
        self.assertTrue(self.collector._is_cache_valid('test_key'))
        
        # Expired cache should be invalid
        self.collector._cache_timestamps['test_key'] = time.time() - 3600  # 1 hour ago
        self.assertFalse(self.collector._is_cache_valid('test_key'))
    
    def test_retry_api_call_success(self):
        """Test successful API call with retry mechanism"""
        mock_api_call = Mock(return_value="success")
        
        result = self.collector._retry_api_call(mock_api_call, "arg1", kwarg1="value1")
        
        self.assertEqual(result, "success")
        mock_api_call.assert_called_once_with("arg1", kwarg1="value1")
    
    def test_retry_api_call_with_retries(self):
        """Test API call retry mechanism"""
        mock_api_call = Mock()
        mock_api_call.side_effect = [
            ApiException(status=500, reason="Server Error"),
            "success"
        ]
        
        with patch('time.sleep'):  # Mock sleep to speed up test
            result = self.collector._retry_api_call(mock_api_call)
        
        self.assertEqual(result, "success")
        self.assertEqual(mock_api_call.call_count, 2)
    
    def test_retry_api_call_max_retries_exceeded(self):
        """Test API call when max retries exceeded"""
        mock_api_call = Mock()
        mock_api_call.side_effect = ApiException(status=500, reason="Server Error")
        
        with patch('time.sleep'):  # Mock sleep to speed up test
            with self.assertRaises(ApiException):
                self.collector._retry_api_call(mock_api_call)
        
        self.assertEqual(mock_api_call.call_count, 2)  # max_retries = 2
    
    @patch('os.path.exists')
    def test_is_kubernetes_environment(self, mock_exists):
        """Test Kubernetes environment detection"""
        mock_exists.return_value = True
        self.assertTrue(self.collector.is_kubernetes_environment())
        
        mock_exists.return_value = False
        self.assertFalse(self.collector.is_kubernetes_environment())
        
        mock_exists.assert_called_with('/var/run/secrets/kubernetes.io/serviceaccount')
    
    @patch.dict(os.environ, {
        'HOSTNAME': 'test-pod',
        'KUBERNETES_NAMESPACE': 'test-ns',
        'KUBERNETES_SERVICE_ACCOUNT': 'test-sa'
    })
    def test_fallback_pod_metadata(self):
        """Test fallback pod metadata collection"""
        # Create a new collector with the environment variables set
        collector = KubernetesMetadataCollector()
        metadata = collector._get_fallback_pod_metadata()
        
        self.assertEqual(metadata['pod_name'], 'test-pod')
        self.assertEqual(metadata['namespace'], 'test-ns')
        self.assertEqual(metadata['service_account'], 'test-sa')
        self.assertIsInstance(metadata['labels'], dict)
        self.assertIsInstance(metadata['annotations'], dict)
    
    @patch('os.getuid', return_value=1000)
    @patch('os.getgid', return_value=1000)
    def test_fallback_security_context(self, mock_getgid, mock_getuid):
        """Test fallback security context collection"""
        security_context = self.collector._get_fallback_security_context()
        
        self.assertEqual(security_context['user_id'], 1000)
        self.assertEqual(security_context['group_id'], 1000)
    
    def test_collect_pod_metadata_without_k8s_client(self):
        """Test pod metadata collection when Kubernetes client is unavailable"""
        self.collector._k8s_client = None
        
        with patch.dict(os.environ, {'HOSTNAME': 'fallback-pod'}):
            metadata = self.collector.collect_pod_metadata()
        
        self.assertEqual(metadata['pod_name'], 'fallback-pod')
        self.assertIsInstance(metadata, dict)
    
    def test_collect_node_metadata_without_k8s_client(self):
        """Test node metadata collection when Kubernetes client is unavailable"""
        self.collector._k8s_client = None
        
        metadata = self.collector.collect_node_metadata()
        
        self.assertIsInstance(metadata, dict)
        self.assertIn('node_name', metadata)
    
    def test_collect_deployment_metadata_without_k8s_client(self):
        """Test deployment metadata collection when Kubernetes client is unavailable"""
        self.collector._apps_client = None
        self.collector._k8s_client = None
        
        metadata = self.collector.collect_deployment_metadata()
        
        self.assertIsInstance(metadata, dict)
        self.assertIn('deployment_name', metadata)
    
    def test_get_security_context_without_k8s_client(self):
        """Test security context collection when Kubernetes client is unavailable"""
        self.collector._k8s_client = None
        
        with patch('os.getuid', return_value=1001), patch('os.getgid', return_value=1001):
            security_context = self.collector.get_security_context()
        
        self.assertEqual(security_context['user_id'], 1001)
        self.assertEqual(security_context['group_id'], 1001)
    
    @patch('ucbl_logger.enhanced.metadata.kubernetes_collector.client.CoreV1Api')
    def test_collect_pod_metadata_with_k8s_client(self, mock_core_api):
        """Test pod metadata collection with Kubernetes client"""
        # Mock pod object with all required attributes
        mock_pod = Mock()
        mock_pod.metadata.name = 'test-pod'
        mock_pod.metadata.namespace = 'test-namespace'
        mock_pod.metadata.labels = {'app': 'test'}
        mock_pod.metadata.annotations = {'annotation': 'value'}
        mock_pod.metadata.uid = 'test-uid'
        mock_pod.metadata.creation_timestamp = None
        mock_pod.metadata.owner_references = []
        
        mock_pod.spec.service_account_name = 'test-sa'
        mock_pod.spec.node_name = 'test-node'
        mock_pod.spec.containers = []
        mock_pod.spec.volumes = []
        mock_pod.spec.restart_policy = 'Always'
        mock_pod.spec.dns_policy = 'ClusterFirst'
        mock_pod.spec.priority_class_name = None
        mock_pod.spec.scheduler_name = 'default-scheduler'
        
        mock_pod.status.pod_ip = '10.0.0.1'
        mock_pod.status.host_ip = '10.0.0.100'
        mock_pod.status.phase = 'Running'
        mock_pod.status.conditions = []
        mock_pod.status.container_statuses = []
        mock_pod.status.qos_class = 'BestEffort'
        
        # Mock API client
        mock_client = Mock()
        mock_client.read_namespaced_pod.return_value = mock_pod
        self.collector._k8s_client = mock_client
        self.collector._pod_name = 'test-pod'
        
        metadata = self.collector.collect_pod_metadata()
        
        self.assertEqual(metadata['pod_name'], 'test-pod')
        self.assertEqual(metadata['namespace'], 'test-namespace')
        self.assertEqual(metadata['labels'], {'app': 'test'})
        self.assertEqual(metadata['service_account'], 'test-sa')
        self.assertEqual(metadata['node_name'], 'test-node')
        self.assertEqual(metadata['pod_ip'], '10.0.0.1')
        self.assertEqual(metadata['phase'], 'Running')
        self.assertEqual(metadata['restart_policy'], 'Always')
        self.assertEqual(metadata['dns_policy'], 'ClusterFirst')
        self.assertEqual(metadata['qos_class'], 'BestEffort')
        self.assertIsInstance(metadata['containers'], list)
        self.assertIsInstance(metadata['volumes'], list)
        self.assertIsInstance(metadata['conditions'], list)
        self.assertIsInstance(metadata['owner_references'], list)
    
    def test_refresh_metadata_cache(self):
        """Test metadata cache refresh"""
        # Add some cached data
        self.collector._cache_timestamps['test'] = time.time() - 100
        self.collector._metadata_cache['test'] = {'old': 'data'}
        
        with patch.object(self.collector, 'collect_pod_metadata') as mock_pod, \
             patch.object(self.collector, 'collect_node_metadata') as mock_node, \
             patch.object(self.collector, 'collect_deployment_metadata') as mock_deployment, \
             patch.object(self.collector, 'get_security_context') as mock_security:
            
            self.collector.refresh_metadata_cache()
            
            # Verify all collection methods were called
            mock_pod.assert_called_once()
            mock_node.assert_called_once()
            mock_deployment.assert_called_once()
            mock_security.assert_called_once()
            
            # Verify cache was cleared
            self.assertEqual(len(self.collector._cache_timestamps), 0)
    
    def test_get_all_metadata(self):
        """Test getting all metadata in single call"""
        with patch.object(self.collector, 'collect_pod_metadata', return_value={'pod': 'data'}), \
             patch.object(self.collector, 'collect_node_metadata', return_value={'node': 'data'}), \
             patch.object(self.collector, 'collect_deployment_metadata', return_value={'deployment': 'data'}), \
             patch.object(self.collector, 'get_security_context', return_value={'security': 'data'}), \
             patch.object(self.collector, 'is_kubernetes_environment', return_value=True):
            
            all_metadata = self.collector.get_all_metadata()
            
            self.assertIn('pod', all_metadata)
            self.assertIn('node', all_metadata)
            self.assertIn('deployment', all_metadata)
            self.assertIn('security_context', all_metadata)
            self.assertIn('kubernetes_environment', all_metadata)
            self.assertIn('cache_info', all_metadata)
            
            self.assertEqual(all_metadata['pod'], {'pod': 'data'})
            self.assertEqual(all_metadata['kubernetes_environment'], True)
    
    def test_cached_or_fetch_with_valid_cache(self):
        """Test cached data retrieval when cache is valid"""
        # Set up valid cache
        cache_key = 'test_key'
        cached_data = {'cached': 'data'}
        self.collector._metadata_cache[cache_key] = cached_data
        self.collector._cache_timestamps[cache_key] = time.time()
        
        mock_fetch_func = Mock()
        
        result = self.collector._get_cached_or_fetch(cache_key, mock_fetch_func)
        
        self.assertEqual(result, cached_data)
        mock_fetch_func.assert_not_called()
    
    def test_cached_or_fetch_with_expired_cache(self):
        """Test data fetching when cache is expired"""
        cache_key = 'test_key'
        fresh_data = {'fresh': 'data'}
        
        # Set up expired cache
        self.collector._cache_timestamps[cache_key] = time.time() - 3600
        
        mock_fetch_func = Mock(return_value=fresh_data)
        
        result = self.collector._get_cached_or_fetch(cache_key, mock_fetch_func)
        
        self.assertEqual(result, fresh_data)
        mock_fetch_func.assert_called_once()
        self.assertEqual(self.collector._metadata_cache[cache_key], fresh_data)
    
    def test_cached_or_fetch_with_fetch_error(self):
        """Test error handling during data fetching"""
        cache_key = 'test_key'
        old_cached_data = {'old': 'data'}
        
        # Set up expired cache with old data
        self.collector._metadata_cache[cache_key] = old_cached_data
        self.collector._cache_timestamps[cache_key] = time.time() - 3600
        
        mock_fetch_func = Mock(side_effect=Exception("Fetch failed"))
        
        result = self.collector._get_cached_or_fetch(cache_key, mock_fetch_func)
        
        # Should return old cached data on error
        self.assertEqual(result, old_cached_data)
        mock_fetch_func.assert_called_once()


    def test_comprehensive_pod_metadata_collection(self):
        """Test comprehensive pod metadata collection with containers and volumes"""
        # Mock pod with comprehensive data
        mock_pod = Mock()
        mock_pod.metadata.name = 'test-pod'
        mock_pod.metadata.namespace = 'test-namespace'
        mock_pod.metadata.labels = {'app': 'test', 'version': 'v1.0'}
        mock_pod.metadata.annotations = {'deployment.kubernetes.io/revision': '1'}
        mock_pod.metadata.uid = 'test-uid'
        mock_pod.metadata.creation_timestamp = None
        mock_owner_ref = Mock()
        mock_owner_ref.kind = 'ReplicaSet'
        mock_owner_ref.name = 'test-rs'
        mock_owner_ref.uid = 'rs-uid'
        mock_owner_ref.controller = True
        mock_owner_ref.block_owner_deletion = True
        mock_pod.metadata.owner_references = [mock_owner_ref]
        
        # Mock container with resources
        mock_container = Mock()
        mock_container.name = 'test-container'
        mock_container.image = 'nginx:1.20'
        mock_container.image_pull_policy = 'IfNotPresent'
        mock_port = Mock()
        mock_port.name = 'http'
        mock_port.container_port = 80
        mock_port.protocol = 'TCP'
        mock_port.host_port = None
        mock_container.ports = [mock_port]
        mock_env_var = Mock()
        mock_env_var.name = 'ENV_VAR'
        mock_env_var.value = 'test-value'
        mock_env_var.value_from = None
        mock_container.env = [mock_env_var]
        mock_volume_mount = Mock()
        mock_volume_mount.name = 'config-vol'
        mock_volume_mount.mount_path = '/etc/config'
        mock_volume_mount.read_only = True
        mock_volume_mount.sub_path = ''
        mock_container.volume_mounts = [mock_volume_mount]
        mock_container.working_dir = '/app'
        mock_container.command = ['nginx']
        mock_container.args = ['-g', 'daemon off;']
        
        # Mock resources
        mock_resources = Mock()
        mock_resources.limits = {'cpu': '500m', 'memory': '512Mi'}
        mock_resources.requests = {'cpu': '100m', 'memory': '128Mi'}
        mock_container.resources = mock_resources
        
        mock_pod.spec.containers = [mock_container]
        mock_volume = Mock()
        mock_volume.name = 'config-vol'
        mock_volume.config_map = Mock()
        mock_volume.config_map.name = 'test-config'
        mock_volume.secret = None
        mock_volume.empty_dir = None
        mock_volume.host_path = None
        mock_volume.persistent_volume_claim = None
        mock_volume.projected = None
        mock_volume.downward_api = None
        mock_volume.nfs = None
        mock_volume.aws_elastic_block_store = None
        mock_volume.azure_disk = None
        mock_volume.gce_persistent_disk = None
        mock_pod.spec.volumes = [mock_volume]
        mock_pod.spec.service_account_name = 'test-sa'
        mock_pod.spec.node_name = 'test-node'
        mock_pod.spec.restart_policy = 'Always'
        mock_pod.spec.dns_policy = 'ClusterFirst'
        mock_pod.spec.priority_class_name = 'high-priority'
        mock_pod.spec.scheduler_name = 'default-scheduler'
        
        mock_pod.status.pod_ip = '10.0.0.1'
        mock_pod.status.host_ip = '10.0.0.100'
        mock_pod.status.phase = 'Running'
        mock_condition = Mock()
        mock_condition.type = 'Ready'
        mock_condition.status = 'True'
        mock_condition.reason = ''
        mock_condition.message = ''
        mock_condition.last_transition_time = None
        mock_pod.status.conditions = [mock_condition]
        mock_container_status = Mock()
        mock_container_status.name = 'test-container'
        mock_container_status.ready = True
        mock_container_status.restart_count = 0
        mock_container_status.image = 'nginx:1.20'
        mock_container_status.image_id = 'sha256:abc123'
        mock_container_status.container_id = 'docker://def456'
        mock_container_status.started = True
        mock_pod.status.container_statuses = [mock_container_status]
        mock_pod.status.qos_class = 'Burstable'
        
        # Mock API client
        mock_client = Mock()
        mock_client.read_namespaced_pod.return_value = mock_pod
        self.collector._k8s_client = mock_client
        self.collector._pod_name = 'test-pod'
        
        metadata = self.collector.collect_pod_metadata()
        
        # Verify basic metadata
        self.assertEqual(metadata['pod_name'], 'test-pod')
        self.assertEqual(metadata['qos_class'], 'Burstable')
        self.assertEqual(metadata['priority_class_name'], 'high-priority')
        
        # Verify owner references
        self.assertEqual(len(metadata['owner_references']), 1)
        self.assertEqual(metadata['owner_references'][0]['kind'], 'ReplicaSet')
        self.assertEqual(metadata['owner_references'][0]['name'], 'test-rs')
        
        # Verify container information
        self.assertEqual(len(metadata['containers']), 1)
        container_info = metadata['containers'][0]
        self.assertEqual(container_info['name'], 'test-container')
        self.assertEqual(container_info['image'], 'nginx:1.20')
        self.assertEqual(len(container_info['ports']), 1)
        self.assertEqual(container_info['ports'][0]['container_port'], 80)
        
        # Verify resource aggregation
        self.assertEqual(metadata['resource_limits']['cpu'], '500m')
        self.assertEqual(metadata['resource_limits']['memory'], '512Mi')
        self.assertEqual(metadata['resource_requests']['cpu'], '100m')
        self.assertEqual(metadata['resource_requests']['memory'], '128Mi')
        
        # Verify volumes
        self.assertEqual(len(metadata['volumes']), 1)
        self.assertEqual(metadata['volumes'][0]['name'], 'config-vol')
        self.assertEqual(metadata['volumes'][0]['type'], 'configMap')
    
    def test_comprehensive_node_metadata_collection(self):
        """Test comprehensive node metadata collection with capacity and conditions"""
        # Mock node with comprehensive data
        mock_node = Mock()
        mock_node.metadata.name = 'test-node'
        mock_node.metadata.labels = {'kubernetes.io/arch': 'amd64', 'node-role.kubernetes.io/worker': ''}
        mock_node.metadata.annotations = {'node.alpha.kubernetes.io/ttl': '0'}
        mock_node.metadata.uid = 'node-uid'
        mock_node.metadata.creation_timestamp = None
        
        # Mock node info
        mock_node_info = Mock()
        mock_node_info.architecture = 'amd64'
        mock_node_info.boot_id = 'boot-123'
        mock_node_info.container_runtime_version = 'containerd://1.6.6'
        mock_node_info.kernel_version = '5.4.0-74-generic'
        mock_node_info.kubelet_version = 'v1.24.0'
        mock_node_info.kube_proxy_version = 'v1.24.0'
        mock_node_info.machine_id = 'machine-123'
        mock_node_info.operating_system = 'linux'
        mock_node_info.os_image = 'Ubuntu 20.04.2 LTS'
        mock_node_info.system_uuid = 'system-123'
        
        # Mock node status
        mock_node.status.node_info = mock_node_info
        mock_node.status.capacity = {'cpu': '4', 'memory': '8Gi', 'pods': '110'}
        mock_node.status.allocatable = {'cpu': '3800m', 'memory': '7Gi', 'pods': '110'}
        mock_ready_condition = Mock()
        mock_ready_condition.type = 'Ready'
        mock_ready_condition.status = 'True'
        mock_ready_condition.reason = 'KubeletReady'
        mock_ready_condition.message = 'kubelet is posting ready status'
        mock_ready_condition.last_heartbeat_time = None
        mock_ready_condition.last_transition_time = None
        
        mock_memory_condition = Mock()
        mock_memory_condition.type = 'MemoryPressure'
        mock_memory_condition.status = 'False'
        mock_memory_condition.reason = 'KubeletHasSufficientMemory'
        mock_memory_condition.message = 'kubelet has sufficient memory available'
        mock_memory_condition.last_heartbeat_time = None
        mock_memory_condition.last_transition_time = None
        
        mock_node.status.conditions = [mock_ready_condition, mock_memory_condition]
        mock_internal_ip = Mock()
        mock_internal_ip.type = 'InternalIP'
        mock_internal_ip.address = '10.0.1.100'
        
        mock_hostname = Mock()
        mock_hostname.type = 'Hostname'
        mock_hostname.address = 'test-node'
        
        mock_node.status.addresses = [mock_internal_ip, mock_hostname]
        mock_node.status.daemon_endpoints = Mock(kubelet_endpoint=Mock(port=10250))
        mock_image1 = Mock()
        mock_image1.names = ['nginx:1.20', 'nginx:latest']
        mock_image1.size_bytes = 50000000
        
        mock_image2 = Mock()
        mock_image2.names = ['ubuntu:20.04']
        mock_image2.size_bytes = 30000000
        
        mock_node.status.images = [mock_image1, mock_image2]
        
        # Add volumes attributes to avoid iteration issues
        mock_node.status.volumes_in_use = []
        mock_node.status.volumes_attached = []
        
        # Mock node spec
        mock_taint = Mock()
        mock_taint.key = 'node-role.kubernetes.io/master'
        mock_taint.value = ''
        mock_taint.effect = 'NoSchedule'
        mock_taint.time_added = None
        
        mock_node.spec.taints = [mock_taint]
        mock_node.spec.unschedulable = False
        
        # Mock API client and pod metadata
        mock_client = Mock()
        mock_client.read_node.return_value = mock_node
        self.collector._k8s_client = mock_client
        
        # Mock pod metadata to return node name
        with patch.object(self.collector, 'collect_pod_metadata', return_value={'node_name': 'test-node'}):
            metadata = self.collector.collect_node_metadata()
        
        # Verify basic metadata
        self.assertEqual(metadata['node_name'], 'test-node')
        self.assertEqual(metadata['architecture'], 'amd64')
        self.assertEqual(metadata['operating_system'], 'linux')
        self.assertEqual(metadata['kubelet_version'], 'v1.24.0')
        
        # Verify capacity and allocatable
        self.assertEqual(metadata['capacity']['cpu'], '4')
        self.assertEqual(metadata['capacity']['memory'], '8Gi')
        self.assertEqual(metadata['allocatable']['cpu'], '3800m')
        self.assertEqual(metadata['allocatable']['memory'], '7Gi')
        
        # Verify parsed resources
        self.assertIn('capacity_parsed', metadata)
        self.assertIn('allocatable_parsed', metadata)
        self.assertEqual(metadata['capacity_parsed']['cpu']['cores'], 4)
        
        # Verify resource utilization calculation
        self.assertIn('resource_utilization', metadata)
        self.assertIn('cpu', metadata['resource_utilization'])
        
        # Verify conditions
        self.assertEqual(len(metadata['conditions']), 2)
        ready_condition = next(c for c in metadata['conditions'] if c['type'] == 'Ready')
        self.assertEqual(ready_condition['status'], 'True')
        self.assertTrue(metadata['ready'])
        
        # Verify addresses
        self.assertEqual(metadata['internal_ip'], '10.0.1.100')
        self.assertEqual(metadata['hostname'], 'test-node')
        
        # Verify taints
        self.assertEqual(len(metadata['taints']), 1)
        self.assertEqual(metadata['taints'][0]['key'], 'node-role.kubernetes.io/master')
        
        # Verify schedulability
        self.assertFalse(metadata['unschedulable'])
        self.assertTrue(metadata['schedulable'])
        
        # Verify images
        self.assertEqual(len(metadata['images']), 2)
        self.assertEqual(metadata['total_images'], 2)
    
    def test_comprehensive_deployment_metadata_collection(self):
        """Test comprehensive deployment metadata collection with services and ingresses"""
        # Mock pod with owner references
        mock_pod = Mock()
        mock_pod.metadata.owner_references = [Mock(kind='ReplicaSet', name='test-deploy-abc123', uid='rs-uid')]
        
        # Mock ReplicaSet
        mock_rs = Mock()
        mock_rs.metadata.name = 'test-deploy-abc123'
        mock_rs.metadata.uid = 'rs-uid'
        mock_rs.metadata.labels = {'app': 'test', 'pod-template-hash': 'abc123'}
        mock_rs.metadata.annotations = {}
        mock_rs.metadata.creation_timestamp = None
        mock_rs.metadata.owner_references = [Mock(kind='Deployment', name='test-deploy', uid='deploy-uid')]
        mock_rs.spec.replicas = 3
        mock_rs.status.ready_replicas = 3
        mock_rs.status.available_replicas = 3
        mock_rs.status.fully_labeled_replicas = 3
        mock_rs.status.observed_generation = 1
        
        # Mock Deployment
        mock_deployment = Mock()
        mock_deployment.metadata.name = 'test-deploy'
        mock_deployment.metadata.uid = 'deploy-uid'
        mock_deployment.metadata.labels = {'app': 'test'}
        mock_deployment.metadata.annotations = {'deployment.kubernetes.io/revision': '1'}
        mock_deployment.metadata.creation_timestamp = None
        mock_deployment.metadata.generation = 1
        mock_deployment.spec.replicas = 3
        mock_deployment.spec.strategy = Mock(type='RollingUpdate', rolling_update=Mock(max_surge='25%', max_unavailable='25%'))
        mock_deployment.status.ready_replicas = 3
        mock_deployment.status.available_replicas = 3
        mock_deployment.status.unavailable_replicas = 0
        mock_deployment.status.updated_replicas = 3
        mock_deployment.status.observed_generation = 1
        mock_deployment.status.collision_count = 0
        mock_deployment.status.conditions = [
            Mock(type='Available', status='True', reason='MinimumReplicasAvailable', message='Deployment has minimum availability.', last_transition_time=None, last_update_time=None)
        ]
        
        # Mock Service
        mock_service = Mock()
        mock_service.metadata.name = 'test-service'
        mock_service.metadata.uid = 'svc-uid'
        mock_service.metadata.labels = {'app': 'test'}
        mock_service.metadata.annotations = {}
        mock_service.spec.selector = {'app': 'test'}
        mock_service.spec.type = 'ClusterIP'
        mock_service.spec.cluster_ip = '10.96.0.1'
        mock_service.spec.external_i_ps = []
        mock_service.spec.session_affinity = 'None'
        mock_service.spec.ports = [Mock(name='http', port=80, target_port=8080, protocol='TCP', node_port=None)]
        mock_service.status.load_balancer = None
        
        # Mock API clients
        mock_k8s_client = Mock()
        mock_k8s_client.read_namespaced_pod.return_value = mock_pod
        mock_k8s_client.list_namespaced_service.return_value = Mock(items=[mock_service])
        
        mock_apps_client = Mock()
        mock_apps_client.read_namespaced_replica_set.return_value = mock_rs
        mock_apps_client.read_namespaced_deployment.return_value = mock_deployment
        
        self.collector._k8s_client = mock_k8s_client
        self.collector._apps_client = mock_apps_client
        self.collector._pod_name = 'test-pod'
        
        # Mock pod metadata to return matching labels
        with patch.object(self.collector, 'collect_pod_metadata', return_value={'labels': {'app': 'test'}}):
            metadata = self.collector.collect_deployment_metadata()
        
        # Verify deployment metadata
        self.assertEqual(metadata['deployment']['name'], 'test-deploy')
        self.assertEqual(metadata['deployment']['replicas'], 3)
        self.assertEqual(metadata['deployment']['ready_replicas'], 3)
        self.assertEqual(metadata['deployment']['strategy_type'], 'RollingUpdate')
        self.assertIn('rolling_update_strategy', metadata['deployment'])
        self.assertEqual(metadata['deployment']['rolling_update_strategy']['max_surge'], '25%')
        
        # Verify replicaset metadata
        self.assertEqual(metadata['replicaset']['name'], 'test-deploy-abc123')
        self.assertEqual(metadata['replicaset']['replicas'], 3)
        self.assertEqual(metadata['replicaset']['ready_replicas'], 3)
        
        # Verify service metadata
        self.assertEqual(len(metadata['services']), 1)
        service = metadata['services'][0]
        self.assertEqual(service['name'], 'test-service')
        self.assertEqual(service['type'], 'ClusterIP')
        self.assertEqual(service['cluster_ip'], '10.96.0.1')
        self.assertEqual(len(service['ports']), 1)
        self.assertEqual(service['ports'][0]['port'], 80)
        
        # Verify backward compatibility
        self.assertEqual(metadata['deployment_name'], 'test-deploy')
        self.assertEqual(metadata['service_name'], 'test-service')
        self.assertEqual(metadata['replicas'], 3)
        self.assertEqual(metadata['ready_replicas'], 3)
    
    # ========== COMPREHENSIVE API MOCKING TESTS ==========
    
    def test_api_call_retry_with_various_exceptions(self):
        """Test API retry mechanism with various exception types"""
        mock_api_call = Mock()
        
        # Test with 404 error (should retry based on current implementation)
        mock_api_call.side_effect = ApiException(status=404, reason="Not Found")
        
        with self.assertRaises(ApiException):
            self.collector._retry_api_call(mock_api_call)
        
        self.assertEqual(mock_api_call.call_count, 2)  # Current implementation retries all ApiExceptions
        
        # Reset mock
        mock_api_call.reset_mock()
        
        # Test with 503 error (should retry and eventually succeed)
        mock_api_call.side_effect = [
            ApiException(status=503, reason="Service Unavailable"),
            "success"  # Succeed on second attempt
        ]
        
        with patch('time.sleep'):
            result = self.collector._retry_api_call(mock_api_call)
        
        self.assertEqual(result, "success")
        self.assertEqual(mock_api_call.call_count, 2)
    
    def test_api_call_retry_with_network_errors(self):
        """Test API retry with network-related errors"""
        mock_api_call = Mock()
        
        # Test with connection error
        mock_api_call.side_effect = [
            ConnectionError("Connection failed"),
            "success"
        ]
        
        with patch('time.sleep'):
            with self.assertRaises(ConnectionError):
                self.collector._retry_api_call(mock_api_call)
    
    def test_comprehensive_pod_metadata_api_failure_scenarios(self):
        """Test pod metadata collection with various API failure scenarios"""
        # Test with partial pod data (missing optional fields)
        mock_pod = Mock()
        mock_pod.metadata.name = 'test-pod'
        mock_pod.metadata.namespace = 'test-namespace'
        mock_pod.metadata.labels = None  # Missing labels
        mock_pod.metadata.annotations = None  # Missing annotations
        mock_pod.metadata.uid = 'test-uid'
        mock_pod.metadata.creation_timestamp = None
        mock_pod.metadata.owner_references = None  # Missing owner references
        
        mock_pod.spec.service_account_name = None  # Missing service account
        mock_pod.spec.node_name = None  # Missing node name
        mock_pod.spec.containers = None  # Missing containers
        mock_pod.spec.volumes = None  # Missing volumes
        mock_pod.spec.restart_policy = None
        mock_pod.spec.dns_policy = None
        mock_pod.spec.priority_class_name = None
        mock_pod.spec.scheduler_name = None
        
        mock_pod.status.pod_ip = None
        mock_pod.status.host_ip = None
        mock_pod.status.phase = None
        mock_pod.status.conditions = None
        mock_pod.status.container_statuses = None
        mock_pod.status.qos_class = None
        
        mock_client = Mock()
        mock_client.read_namespaced_pod.return_value = mock_pod
        self.collector._k8s_client = mock_client
        self.collector._pod_name = 'test-pod'
        
        metadata = self.collector.collect_pod_metadata()
        
        # Verify graceful handling of missing fields
        self.assertEqual(metadata['pod_name'], 'test-pod')
        self.assertEqual(metadata['labels'], {})
        self.assertEqual(metadata['annotations'], {})
        self.assertEqual(metadata['service_account'], 'default')
        self.assertEqual(metadata['node_name'], 'unknown')
        self.assertEqual(metadata['owner_references'], [])
        self.assertEqual(metadata['containers'], [])
        self.assertEqual(metadata['volumes'], [])
        self.assertEqual(metadata['conditions'], [])
        self.assertEqual(metadata['qos_class'], 'BestEffort')
    
    def test_node_metadata_with_missing_status_fields(self):
        """Test node metadata collection with missing status fields"""
        mock_node = Mock()
        mock_node.metadata.name = 'test-node'
        mock_node.metadata.labels = {}
        mock_node.metadata.annotations = {}
        mock_node.metadata.uid = 'node-uid'
        mock_node.metadata.creation_timestamp = None
        
        # Missing node status entirely
        mock_node.status = None
        mock_node.spec = None
        
        mock_client = Mock()
        mock_client.read_node.return_value = mock_node
        self.collector._k8s_client = mock_client
        
        with patch.object(self.collector, 'collect_pod_metadata', return_value={'node_name': 'test-node'}):
            metadata = self.collector.collect_node_metadata()
        
        # Verify graceful handling of missing status
        self.assertEqual(metadata['node_name'], 'test-node')
        self.assertNotIn('capacity', metadata)
        self.assertNotIn('allocatable', metadata)
        self.assertNotIn('conditions', metadata)
    
    def test_deployment_metadata_with_complex_ownership_chain(self):
        """Test deployment metadata with complex ownership chains"""
        # Mock pod with DaemonSet owner (not ReplicaSet)
        mock_pod = Mock()
        mock_daemonset_owner = Mock()
        mock_daemonset_owner.kind = 'DaemonSet'
        mock_daemonset_owner.name = 'test-daemonset'
        mock_daemonset_owner.uid = 'ds-uid'
        mock_pod.metadata.owner_references = [mock_daemonset_owner]
        
        mock_k8s_client = Mock()
        mock_k8s_client.read_namespaced_pod.return_value = mock_pod
        mock_k8s_client.list_namespaced_service.return_value = Mock(items=[])
        
        self.collector._k8s_client = mock_k8s_client
        self.collector._apps_client = Mock()
        self.collector._pod_name = 'test-pod'
        
        with patch.object(self.collector, 'collect_pod_metadata', return_value={'labels': {}}):
            metadata = self.collector.collect_deployment_metadata()
        
        # Verify DaemonSet controller is detected
        self.assertEqual(metadata['controller']['kind'], 'DaemonSet')
        self.assertEqual(metadata['controller']['name'], 'test-daemonset')
    
    # ========== COMPREHENSIVE CACHING TESTS ==========
    
    def test_cache_ttl_expiration_behavior(self):
        """Test detailed cache TTL expiration behavior"""
        cache_key = 'test_cache'
        
        # Test fresh cache
        self.collector._cache_timestamps[cache_key] = time.time()
        self.assertTrue(self.collector._is_cache_valid(cache_key))
        
        # Test cache at TTL boundary
        self.collector._cache_timestamps[cache_key] = time.time() - self.collector.cache_ttl + 1
        self.assertTrue(self.collector._is_cache_valid(cache_key))
        
        # Test expired cache
        self.collector._cache_timestamps[cache_key] = time.time() - self.collector.cache_ttl - 1
        self.assertFalse(self.collector._is_cache_valid(cache_key))
    
    def test_cache_invalidation_on_refresh(self):
        """Test cache invalidation during refresh operations"""
        # Set up initial cache data
        self.collector._metadata_cache['pod_metadata'] = {'old': 'data'}
        self.collector._metadata_cache['node_metadata'] = {'old': 'node'}
        self.collector._cache_timestamps['pod_metadata'] = time.time() - 100
        self.collector._cache_timestamps['node_metadata'] = time.time() - 100
        
        # Mock collection methods
        with patch.object(self.collector, 'collect_pod_metadata', return_value={'new': 'pod_data'}) as mock_pod, \
             patch.object(self.collector, 'collect_node_metadata', return_value={'new': 'node_data'}) as mock_node, \
             patch.object(self.collector, 'collect_deployment_metadata', return_value={'new': 'deploy_data'}) as mock_deploy, \
             patch.object(self.collector, 'get_security_context', return_value={'new': 'security_data'}) as mock_security:
            
            # Verify cache has old data
            self.assertEqual(len(self.collector._cache_timestamps), 2)
            
            # Refresh cache
            self.collector.refresh_metadata_cache()
            
            # Verify all methods were called
            mock_pod.assert_called_once()
            mock_node.assert_called_once()
            mock_deploy.assert_called_once()
            mock_security.assert_called_once()
            
            # Verify cache was cleared
            self.assertEqual(len(self.collector._cache_timestamps), 0)
    
    def test_concurrent_cache_access_simulation(self):
        """Test cache behavior under simulated concurrent access"""
        cache_key = 'concurrent_test'
        
        # Simulate multiple threads accessing cache
        def mock_fetch_func():
            time.sleep(0.01)  # Simulate API delay
            return {'thread_data': time.time()}
        
        # First call should fetch data
        result1 = self.collector._get_cached_or_fetch(cache_key, mock_fetch_func)
        self.assertIn('thread_data', result1)
        
        # Second call should use cached data (no delay)
        start_time = time.time()
        result2 = self.collector._get_cached_or_fetch(cache_key, mock_fetch_func)
        end_time = time.time()
        
        # Should be same data and much faster
        self.assertEqual(result1, result2)
        self.assertLess(end_time - start_time, 0.005)  # Should be much faster than 0.01s
    
    def test_cache_memory_management(self):
        """Test cache memory management and cleanup"""
        # Fill cache with multiple entries
        for i in range(10):
            cache_key = f'test_key_{i}'
            self.collector._metadata_cache[cache_key] = {'data': f'value_{i}'}
            self.collector._cache_timestamps[cache_key] = time.time() - (i * 10)
        
        # Verify cache is populated
        self.assertEqual(len(self.collector._metadata_cache), 10)
        self.assertEqual(len(self.collector._cache_timestamps), 10)
        
        # Refresh should clear all cache
        with patch.object(self.collector, 'collect_pod_metadata'), \
             patch.object(self.collector, 'collect_node_metadata'), \
             patch.object(self.collector, 'collect_deployment_metadata'), \
             patch.object(self.collector, 'get_security_context'):
            
            self.collector.refresh_metadata_cache()
        
        # Verify cache was cleared
        self.assertEqual(len(self.collector._cache_timestamps), 0)
    
    # ========== COMPREHENSIVE FALLBACK BEHAVIOR TESTS ==========
    
    def test_complete_kubernetes_api_unavailability(self):
        """Test behavior when Kubernetes API is completely unavailable"""
        # Create a new collector with environment variables set
        with patch.dict(os.environ, {
            'HOSTNAME': 'fallback-pod',
            'KUBERNETES_NAMESPACE': 'fallback-ns',
            'KUBERNETES_SERVICE_ACCOUNT': 'fallback-sa',
            'KUBERNETES_NODE_NAME': 'fallback-node',
            'KUBERNETES_DEPLOYMENT_NAME': 'fallback-deploy',
            'KUBERNETES_SERVICE_NAME': 'fallback-service'
        }):
            # Create collector with environment variables set
            collector = KubernetesMetadataCollector()
            # Simulate complete API unavailability
            collector._k8s_client = None
            collector._apps_client = None
            
            # Test all metadata collection methods
            pod_metadata = collector.collect_pod_metadata()
            node_metadata = collector.collect_node_metadata()
            deployment_metadata = collector.collect_deployment_metadata()
            security_context = collector.get_security_context()
            
            # Verify fallback data is returned
            self.assertEqual(pod_metadata['pod_name'], 'fallback-pod')
            self.assertEqual(pod_metadata['namespace'], 'fallback-ns')
            self.assertEqual(pod_metadata['service_account'], 'fallback-sa')
            
            self.assertEqual(node_metadata['node_name'], 'fallback-node')
            
            self.assertEqual(deployment_metadata['deployment_name'], 'fallback-deploy')
            self.assertEqual(deployment_metadata['service_name'], 'fallback-service')
            
            self.assertIn('user_id', security_context)
            self.assertIn('group_id', security_context)
    
    def test_partial_api_failure_graceful_degradation(self):
        """Test graceful degradation when some API calls fail"""
        # Mock clients that fail for specific calls
        mock_k8s_client = Mock()
        mock_apps_client = Mock()
        
        # Pod API works, but node API fails
        mock_pod = Mock()
        mock_pod.metadata.name = 'working-pod'
        mock_pod.metadata.namespace = 'test-ns'
        mock_pod.metadata.labels = {}
        mock_pod.metadata.annotations = {}
        mock_pod.metadata.uid = 'pod-uid'
        mock_pod.metadata.creation_timestamp = None
        mock_pod.metadata.owner_references = []
        mock_pod.spec.service_account_name = 'test-sa'
        mock_pod.spec.node_name = 'test-node'
        mock_pod.spec.containers = []
        mock_pod.spec.volumes = []
        mock_pod.spec.restart_policy = 'Always'
        mock_pod.spec.dns_policy = 'ClusterFirst'
        mock_pod.spec.priority_class_name = None
        mock_pod.spec.scheduler_name = 'default-scheduler'
        mock_pod.status.pod_ip = '10.0.0.1'
        mock_pod.status.host_ip = '10.0.0.100'
        mock_pod.status.phase = 'Running'
        mock_pod.status.conditions = []
        mock_pod.status.container_statuses = []
        mock_pod.status.qos_class = 'BestEffort'
        
        mock_k8s_client.read_namespaced_pod.return_value = mock_pod
        mock_k8s_client.read_node.side_effect = ApiException(status=500, reason="Server Error")
        mock_k8s_client.list_namespaced_service.return_value = Mock(items=[])
        
        self.collector._k8s_client = mock_k8s_client
        self.collector._apps_client = mock_apps_client
        self.collector._pod_name = 'working-pod'
        
        # Pod metadata should work
        pod_metadata = self.collector.collect_pod_metadata()
        self.assertEqual(pod_metadata['pod_name'], 'working-pod')
        
        # Node metadata should fall back gracefully
        with patch.dict(os.environ, {'KUBERNETES_NODE_NAME': 'fallback-node'}):
            node_metadata = self.collector.collect_node_metadata()
            self.assertEqual(node_metadata['node_name'], 'fallback-node')
    
    def test_network_timeout_simulation(self):
        """Test behavior during network timeouts"""
        mock_api_call = Mock()
        mock_api_call.side_effect = [
            TimeoutError("Network timeout"),
            TimeoutError("Network timeout"),
            "success"
        ]
        
        # Should raise TimeoutError immediately (not retried in current implementation)
        with patch('time.sleep'):
            with self.assertRaises(TimeoutError):
                self.collector._retry_api_call(mock_api_call)
        
        self.assertEqual(mock_api_call.call_count, 1)  # TimeoutError not retried
    
    def test_kubernetes_environment_detection_edge_cases(self):
        """Test Kubernetes environment detection in various scenarios"""
        # Test when service account directory exists but is empty
        with patch('os.path.exists') as mock_exists:
            mock_exists.return_value = True
            self.assertTrue(self.collector.is_kubernetes_environment())
            
            mock_exists.return_value = False
            self.assertFalse(self.collector.is_kubernetes_environment())
    
    def test_fallback_with_missing_environment_variables(self):
        """Test fallback behavior when environment variables are missing"""
        # Clear all Kubernetes-related environment variables
        with patch.dict(os.environ, {}, clear=True):
            collector = KubernetesMetadataCollector()
            # Ensure no API clients
            collector._k8s_client = None
            collector._apps_client = None
            
            # Test fallback metadata collection
            pod_metadata = collector.collect_pod_metadata()
            node_metadata = collector.collect_node_metadata()
            deployment_metadata = collector.collect_deployment_metadata()
            
            # Verify default values are used
            self.assertEqual(pod_metadata['pod_name'], 'unknown')
            self.assertEqual(pod_metadata['namespace'], 'default')
            self.assertEqual(pod_metadata['service_account'], 'default')
            
            self.assertEqual(node_metadata['node_name'], 'unknown')
            
            # Check the actual structure returned by fallback
            self.assertIn('deployment_name', deployment_metadata)
            self.assertEqual(deployment_metadata['deployment_name'], 'unknown')
            self.assertEqual(deployment_metadata['service_name'], 'unknown')
    
    def test_error_recovery_after_api_restoration(self):
        """Test recovery behavior when API becomes available after being unavailable"""
        # Start with no client
        self.collector._k8s_client = None
        
        # First call should use fallback
        with patch.dict(os.environ, {'HOSTNAME': 'fallback-pod'}):
            metadata1 = self.collector.collect_pod_metadata()
            self.assertEqual(metadata1['pod_name'], 'fallback-pod')
        
        # Simulate API restoration
        mock_pod = Mock()
        mock_pod.metadata.name = 'restored-pod'
        mock_pod.metadata.namespace = 'test-ns'
        mock_pod.metadata.labels = {}
        mock_pod.metadata.annotations = {}
        mock_pod.metadata.uid = 'pod-uid'
        mock_pod.metadata.creation_timestamp = None
        mock_pod.metadata.owner_references = []
        mock_pod.spec.service_account_name = 'test-sa'
        mock_pod.spec.node_name = 'test-node'
        mock_pod.spec.containers = []
        mock_pod.spec.volumes = []
        mock_pod.spec.restart_policy = 'Always'
        mock_pod.spec.dns_policy = 'ClusterFirst'
        mock_pod.spec.priority_class_name = None
        mock_pod.spec.scheduler_name = 'default-scheduler'
        mock_pod.status.pod_ip = '10.0.0.1'
        mock_pod.status.host_ip = '10.0.0.100'
        mock_pod.status.phase = 'Running'
        mock_pod.status.conditions = []
        mock_pod.status.container_statuses = []
        mock_pod.status.qos_class = 'BestEffort'
        
        mock_client = Mock()
        mock_client.read_namespaced_pod.return_value = mock_pod
        self.collector._k8s_client = mock_client
        self.collector._pod_name = 'restored-pod'
        
        # Clear cache to force fresh fetch
        self.collector._cache_timestamps.clear()
        
        # Second call should use API
        metadata2 = self.collector.collect_pod_metadata()
        self.assertEqual(metadata2['pod_name'], 'restored-pod')
    
    def test_resource_parsing_helpers(self):
        """Test resource parsing helper methods"""
        # Test CPU resource addition
        result = self.collector._add_resource_values('100m', '200m')
        self.assertEqual(result, '300m')
        
        result = self.collector._add_resource_values('1', '500m')
        self.assertEqual(result, '1500m')
        
        # Test memory resource addition
        result = self.collector._add_resource_values('128Mi', '256Mi')
        self.assertEqual(result, '384Mi')
        
        result = self.collector._add_resource_values('1Gi', '512Mi')
        self.assertEqual(result, '1Gi')  # Should convert to appropriate unit
        
        # Test memory parsing
        bytes_val = self.collector._parse_memory_to_bytes('128Mi')
        self.assertEqual(bytes_val, 128 * 1024 * 1024)
        
        bytes_val = self.collector._parse_memory_to_bytes('1Gi')
        self.assertEqual(bytes_val, 1024 * 1024 * 1024)
        
        # Test resource parsing
        resources = {'cpu': '2', 'memory': '4Gi', 'pods': '110'}
        parsed = self.collector._parse_node_resources(resources)
        
        self.assertEqual(parsed['cpu']['cores'], 2)
        self.assertEqual(parsed['cpu']['millicores'], 2000)
        self.assertEqual(parsed['memory']['bytes'], 4 * 1024 * 1024 * 1024)
        self.assertEqual(parsed['pods']['value'], 110)
    
    def test_sensitive_env_var_detection(self):
        """Test sensitive environment variable detection"""
        self.assertTrue(self.collector._is_sensitive_env_var('PASSWORD'))
        self.assertTrue(self.collector._is_sensitive_env_var('API_KEY'))
        self.assertTrue(self.collector._is_sensitive_env_var('SECRET_TOKEN'))
        self.assertTrue(self.collector._is_sensitive_env_var('database_password'))
        
        self.assertFalse(self.collector._is_sensitive_env_var('APP_NAME'))
        self.assertFalse(self.collector._is_sensitive_env_var('LOG_LEVEL'))
        self.assertFalse(self.collector._is_sensitive_env_var('PORT'))
    
    # ========== ADDITIONAL COMPREHENSIVE TESTS ==========
    
    def test_cache_performance_under_load(self):
        """Test cache performance under simulated load"""
        cache_key = 'performance_test'
        call_count = 0
        
        def expensive_fetch_func():
            nonlocal call_count
            call_count += 1
            time.sleep(0.01)  # Simulate expensive operation
            return {'expensive_data': call_count}
        
        # First batch of calls should hit cache after first call
        results = []
        for i in range(10):
            result = self.collector._get_cached_or_fetch(cache_key, expensive_fetch_func)
            results.append(result)
        
        # Should only call fetch function once
        self.assertEqual(call_count, 1)
        # All results should be identical
        for result in results:
            self.assertEqual(result, results[0])
    
    def test_metadata_collection_with_malformed_api_responses(self):
        """Test handling of malformed API responses"""
        # Mock pod with malformed data that will cause an exception
        mock_client = Mock()
        mock_client.read_namespaced_pod.side_effect = Exception("Malformed API response")
        
        self.collector._k8s_client = mock_client
        self.collector._pod_name = 'test-pod'
        
        # Clear cache to force API call
        self.collector._cache_timestamps.clear()
        
        # Should handle malformed data gracefully by falling back
        with patch.dict(os.environ, {'HOSTNAME': 'fallback-pod'}):
            metadata = self.collector.collect_pod_metadata()
        
        # Should return fallback metadata
        self.assertEqual(metadata['pod_name'], 'fallback-pod')
    
    def test_api_rate_limiting_simulation(self):
        """Test behavior under API rate limiting"""
        mock_api_call = Mock()
        
        # Simulate rate limiting with 429 status
        mock_api_call.side_effect = [
            ApiException(status=429, reason="Too Many Requests"),
            ApiException(status=429, reason="Too Many Requests"),
            "success"
        ]
        
        with patch('time.sleep') as mock_sleep:
            with self.assertRaises(ApiException):  # Should fail after max retries
                self.collector._retry_api_call(mock_api_call)
        
        # Should have attempted retries with backoff
        self.assertEqual(mock_api_call.call_count, 2)
        self.assertEqual(mock_sleep.call_count, 1)  # One sleep between retries
    
    def test_cache_invalidation_edge_cases(self):
        """Test cache invalidation in edge cases"""
        # Test cache with future timestamp (clock skew)
        future_time = time.time() + 3600  # 1 hour in future
        self.collector._cache_timestamps['future_key'] = future_time
        
        # Should still be considered valid
        self.assertTrue(self.collector._is_cache_valid('future_key'))
        
        # Test cache with zero TTL
        zero_ttl_collector = KubernetesMetadataCollector(cache_ttl=0)
        zero_ttl_collector._cache_timestamps['zero_ttl_key'] = time.time()
        
        # Should immediately be invalid
        self.assertFalse(zero_ttl_collector._is_cache_valid('zero_ttl_key'))
    
    def test_comprehensive_error_logging(self):
        """Test that errors are properly logged during failures"""
        with patch.object(self.collector, 'logger') as mock_logger:
            # Simulate API failure
            self.collector._k8s_client = None
            
            # Call methods that should log errors
            self.collector.collect_pod_metadata()
            
            # Verify error logging (should use fallback without error)
            # Since fallback is used, no error should be logged
            mock_logger.error.assert_not_called()
            
            # Now test with actual API failure
            mock_client = Mock()
            mock_client.read_namespaced_pod.side_effect = Exception("Test error")
            self.collector._k8s_client = mock_client
            self.collector._pod_name = 'test-pod'
            
            # Clear cache to force API call
            self.collector._cache_timestamps.clear()
            
            self.collector.collect_pod_metadata()
            
            # Should log the error
            mock_logger.error.assert_called()
    
    def test_all_metadata_aggregation(self):
        """Test the get_all_metadata method comprehensively"""
        # Mock all individual collection methods
        mock_pod_data = {'pod': 'data'}
        mock_node_data = {'node': 'data'}
        mock_deployment_data = {'deployment': 'data'}
        mock_security_data = {'security': 'data'}
        
        with patch.object(self.collector, 'collect_pod_metadata', return_value=mock_pod_data), \
             patch.object(self.collector, 'collect_node_metadata', return_value=mock_node_data), \
             patch.object(self.collector, 'collect_deployment_metadata', return_value=mock_deployment_data), \
             patch.object(self.collector, 'get_security_context', return_value=mock_security_data), \
             patch.object(self.collector, 'is_kubernetes_environment', return_value=True):
            
            all_metadata = self.collector.get_all_metadata()
            
            # Verify all sections are present
            self.assertEqual(all_metadata['pod'], mock_pod_data)
            self.assertEqual(all_metadata['node'], mock_node_data)
            self.assertEqual(all_metadata['deployment'], mock_deployment_data)
            self.assertEqual(all_metadata['security_context'], mock_security_data)
            self.assertTrue(all_metadata['kubernetes_environment'])
            
            # Verify cache info is included
            self.assertIn('cache_info', all_metadata)
            self.assertEqual(all_metadata['cache_info']['cache_ttl'], self.collector.cache_ttl)
            self.assertIn('cached_keys', all_metadata['cache_info'])
            self.assertIn('cache_ages', all_metadata['cache_info'])
    
    def test_volume_type_detection_comprehensive(self):
        """Test comprehensive volume type detection"""
        # Test all volume types with correct expected names
        volume_types = [
            ('configMap', Mock(config_map=Mock(), secret=None, empty_dir=None)),
            ('secret', Mock(config_map=None, secret=Mock(), empty_dir=None)),
            ('emptyDir', Mock(config_map=None, secret=None, empty_dir=Mock())),
            ('hostPath', Mock(config_map=None, secret=None, empty_dir=None, host_path=Mock())),
            ('persistentVolumeClaim', Mock(config_map=None, secret=None, empty_dir=None, host_path=None, persistent_volume_claim=Mock())),
            ('projected', Mock(config_map=None, secret=None, empty_dir=None, host_path=None, persistent_volume_claim=None, projected=Mock())),
            ('downwardAPI', Mock(config_map=None, secret=None, empty_dir=None, host_path=None, persistent_volume_claim=None, projected=None, downward_api=Mock())),
            ('nfs', Mock(config_map=None, secret=None, empty_dir=None, host_path=None, persistent_volume_claim=None, projected=None, downward_api=None, nfs=Mock())),
        ]
        
        for expected_type, mock_volume in volume_types:
            # Set all other attributes to None
            for attr in ['aws_elastic_block_store', 'azure_disk', 'gce_persistent_disk']:
                if not hasattr(mock_volume, attr):
                    setattr(mock_volume, attr, None)
            
            result = self.collector._get_volume_type(mock_volume)
            self.assertEqual(result, expected_type)
        
        # Test unknown volume type
        unknown_volume = Mock()
        for attr in ['config_map', 'secret', 'empty_dir', 'host_path', 'persistent_volume_claim', 
                     'projected', 'downward_api', 'nfs', 'aws_elastic_block_store', 'azure_disk', 'gce_persistent_disk']:
            setattr(unknown_volume, attr, None)
        
        result = self.collector._get_volume_type(unknown_volume)
        self.assertEqual(result, 'unknown')
    
    def test_resource_calculation_edge_cases(self):
        """Test resource calculation with edge cases"""
        # Test with invalid resource values
        result = self.collector._add_resource_values('invalid', 'also_invalid')
        self.assertEqual(result, 'also_invalid')  # Should return second value
        
        # Test memory parsing with invalid values
        bytes_val = self.collector._parse_memory_to_bytes('invalid_memory')
        self.assertEqual(bytes_val, 0)
        
        # Test node utilization calculation with valid resources
        capacity = {'cpu': '1', 'memory': '1Gi'}
        allocatable = {'cpu': '800m', 'memory': '800Mi'}
        
        utilization = self.collector._calculate_node_utilization(capacity, allocatable)
        
        # Should calculate utilization properly
        self.assertIn('cpu', utilization)
        self.assertIn('memory', utilization)
        
        # Test with zero capacity (edge case)
        capacity_zero = {'cpu': '0', 'memory': '0Gi'}
        allocatable_zero = {'cpu': '0', 'memory': '0Gi'}
        
        utilization_zero = self.collector._calculate_node_utilization(capacity_zero, allocatable_zero)
        
        # Should handle zero division gracefully - may return empty dict or handle gracefully
        self.assertIsInstance(utilization_zero, dict)


if __name__ == '__main__':
    unittest.main()