#!/usr/bin/env python3
"""
Example demonstrating the enhanced KubernetesMetadataCollector with real API integration
"""

import json
import logging
from ucbl_logger.enhanced.metadata import KubernetesMetadataCollector

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Demonstrate KubernetesMetadataCollector functionality"""
    
    print("=== Enhanced Kubernetes Metadata Collector Demo ===\n")
    
    # Initialize the collector
    collector = KubernetesMetadataCollector(cache_ttl=300, max_retries=3)
    
    # Check if we're in a Kubernetes environment
    is_k8s = collector.is_kubernetes_environment()
    print(f"Running in Kubernetes environment: {is_k8s}")
    
    if is_k8s:
        print("✓ Detected Kubernetes environment - will use real API calls")
    else:
        print("✓ Not in Kubernetes environment - will use fallback methods")
    
    print("\n--- Collecting Comprehensive Pod Metadata ---")
    try:
        pod_metadata = collector.collect_pod_metadata()
        print(f"Pod Name: {pod_metadata.get('pod_name', 'N/A')}")
        print(f"Namespace: {pod_metadata.get('namespace', 'N/A')}")
        print(f"Service Account: {pod_metadata.get('service_account', 'N/A')}")
        print(f"Node Name: {pod_metadata.get('node_name', 'N/A')}")
        print(f"Pod IP: {pod_metadata.get('pod_ip', 'N/A')}")
        print(f"Phase: {pod_metadata.get('phase', 'N/A')}")
        print(f"QoS Class: {pod_metadata.get('qos_class', 'N/A')}")
        print(f"Restart Policy: {pod_metadata.get('restart_policy', 'N/A')}")
        print(f"DNS Policy: {pod_metadata.get('dns_policy', 'N/A')}")
        
        labels = pod_metadata.get('labels', {})
        if labels:
            print(f"Labels: {json.dumps(labels, indent=2)}")
        else:
            print("Labels: None")
        
        # Show owner references
        owner_refs = pod_metadata.get('owner_references', [])
        if owner_refs:
            print(f"Owner References: {len(owner_refs)} found")
            for owner in owner_refs:
                print(f"  - {owner.get('kind', 'N/A')}: {owner.get('name', 'N/A')}")
        
        # Show container information
        containers = pod_metadata.get('containers', [])
        if containers:
            print(f"Containers: {len(containers)} found")
            for container in containers:
                print(f"  - {container.get('name', 'N/A')}: {container.get('image', 'N/A')}")
                ports = container.get('ports', [])
                if ports:
                    port_info = ', '.join([f"{p.get('container_port', 'N/A')}/{p.get('protocol', 'TCP')}" for p in ports])
                    print(f"    Ports: {port_info}")
        
        # Show resource information
        resource_limits = pod_metadata.get('resource_limits', {})
        resource_requests = pod_metadata.get('resource_requests', {})
        if resource_limits or resource_requests:
            print("Resources:")
            if resource_requests:
                print(f"  Requests: CPU={resource_requests.get('cpu', 'N/A')}, Memory={resource_requests.get('memory', 'N/A')}")
            if resource_limits:
                print(f"  Limits: CPU={resource_limits.get('cpu', 'N/A')}, Memory={resource_limits.get('memory', 'N/A')}")
        
        # Show volumes
        volumes = pod_metadata.get('volumes', [])
        if volumes:
            print(f"Volumes: {len(volumes)} found")
            for volume in volumes:
                print(f"  - {volume.get('name', 'N/A')} ({volume.get('type', 'N/A')})")
            
    except Exception as e:
        print(f"Error collecting pod metadata: {e}")
    
    print("\n--- Collecting Comprehensive Node Metadata ---")
    try:
        node_metadata = collector.collect_node_metadata()
        print(f"Node Name: {node_metadata.get('node_name', 'N/A')}")
        print(f"Architecture: {node_metadata.get('architecture', 'N/A')}")
        print(f"OS: {node_metadata.get('operating_system', 'N/A')}")
        print(f"OS Image: {node_metadata.get('os_image', 'N/A')}")
        print(f"Kernel Version: {node_metadata.get('kernel_version', 'N/A')}")
        print(f"Kubelet Version: {node_metadata.get('kubelet_version', 'N/A')}")
        print(f"Container Runtime: {node_metadata.get('container_runtime_version', 'N/A')}")
        print(f"Ready: {node_metadata.get('ready', 'N/A')}")
        print(f"Schedulable: {node_metadata.get('schedulable', 'N/A')}")
        
        # Show addresses
        internal_ip = node_metadata.get('internal_ip', 'N/A')
        external_ip = node_metadata.get('external_ip', 'N/A')
        hostname = node_metadata.get('hostname', 'N/A')
        print(f"Addresses: Internal={internal_ip}, External={external_ip}, Hostname={hostname}")
        
        # Show capacity and allocatable resources
        capacity = node_metadata.get('capacity', {})
        allocatable = node_metadata.get('allocatable', {})
        if capacity or allocatable:
            print("Resources:")
            if capacity:
                print(f"  Capacity: CPU={capacity.get('cpu', 'N/A')}, Memory={capacity.get('memory', 'N/A')}, Pods={capacity.get('pods', 'N/A')}")
            if allocatable:
                print(f"  Allocatable: CPU={allocatable.get('cpu', 'N/A')}, Memory={allocatable.get('memory', 'N/A')}, Pods={allocatable.get('pods', 'N/A')}")
        
        # Show parsed resources for better understanding
        capacity_parsed = node_metadata.get('capacity_parsed', {})
        if capacity_parsed and 'cpu' in capacity_parsed:
            cpu_info = capacity_parsed['cpu']
            print(f"  CPU Details: {cpu_info.get('cores', 'N/A')} cores ({cpu_info.get('millicores', 'N/A')} millicores)")
        
        if capacity_parsed and 'memory' in capacity_parsed:
            memory_info = capacity_parsed['memory']
            print(f"  Memory Details: {memory_info.get('human_readable', 'N/A')} ({memory_info.get('bytes', 'N/A')} bytes)")
        
        # Show resource utilization
        utilization = node_metadata.get('resource_utilization', {})
        if utilization:
            print("Resource Utilization:")
            for resource, util_info in utilization.items():
                reserved_pct = util_info.get('reserved_percentage', 0)
                print(f"  {resource.upper()}: {reserved_pct}% reserved by system")
        
        # Show conditions
        conditions = node_metadata.get('conditions', [])
        if conditions:
            print(f"Conditions: {len(conditions)} found")
            for condition in conditions:
                status = condition.get('status', 'Unknown')
                cond_type = condition.get('type', 'Unknown')
                print(f"  - {cond_type}: {status}")
        
        # Show taints
        taints = node_metadata.get('taints', [])
        if taints:
            print(f"Taints: {len(taints)} found")
            for taint in taints:
                key = taint.get('key', 'N/A')
                effect = taint.get('effect', 'N/A')
                print(f"  - {key}: {effect}")
        
        # Show images
        total_images = node_metadata.get('total_images', 0)
        if total_images > 0:
            print(f"Container Images: {total_images} total")
            images = node_metadata.get('images', [])
            for image in images[:3]:  # Show first 3 images
                names = image.get('names', [])
                size_bytes = image.get('size_bytes', 0)
                size_mb = size_bytes / (1024 * 1024) if size_bytes > 0 else 0
                print(f"  - {names[0] if names else 'N/A'}: {size_mb:.1f} MB")
            if total_images > 3:
                print(f"  ... and {total_images - 3} more images")
            
    except Exception as e:
        print(f"Error collecting node metadata: {e}")
    
    print("\n--- Collecting Comprehensive Deployment Metadata ---")
    try:
        deployment_metadata = collector.collect_deployment_metadata()
        
        # Show deployment information
        deployment = deployment_metadata.get('deployment', {})
        if deployment:
            print(f"Deployment: {deployment.get('name', 'N/A')}")
            print(f"  Strategy: {deployment.get('strategy_type', 'N/A')}")
            print(f"  Replicas: {deployment.get('replicas', 'N/A')} desired, {deployment.get('ready_replicas', 'N/A')} ready")
            print(f"  Generation: {deployment.get('generation', 'N/A')} (observed: {deployment.get('observed_generation', 'N/A')})")
            
            # Show rolling update strategy if available
            rolling_update = deployment.get('rolling_update_strategy', {})
            if rolling_update:
                print(f"  Rolling Update: max_surge={rolling_update.get('max_surge', 'N/A')}, max_unavailable={rolling_update.get('max_unavailable', 'N/A')}")
        
        # Show replicaset information
        replicaset = deployment_metadata.get('replicaset', {})
        if replicaset:
            print(f"ReplicaSet: {replicaset.get('name', 'N/A')}")
            print(f"  Replicas: {replicaset.get('replicas', 'N/A')} desired, {replicaset.get('ready_replicas', 'N/A')} ready")
        
        # Show controller information for non-deployment workloads
        controller = deployment_metadata.get('controller', {})
        if controller:
            print(f"Controller: {controller.get('kind', 'N/A')}/{controller.get('name', 'N/A')}")
        
        # Show services
        services = deployment_metadata.get('services', [])
        if services:
            print(f"Services: {len(services)} found")
            for service in services:
                service_name = service.get('name', 'N/A')
                service_type = service.get('type', 'N/A')
                cluster_ip = service.get('cluster_ip', 'N/A')
                print(f"  - {service_name} ({service_type}): {cluster_ip}")
                
                ports = service.get('ports', [])
                if ports:
                    port_info = ', '.join([f"{p.get('port', 'N/A')}:{p.get('target_port', 'N/A')}" for p in ports])
                    print(f"    Ports: {port_info}")
                
                # Show load balancer info if available
                lb_ingress = service.get('load_balancer_ingress', [])
                if lb_ingress:
                    for ingress in lb_ingress:
                        ip = ingress.get('ip', '')
                        hostname = ingress.get('hostname', '')
                        print(f"    LoadBalancer: {ip or hostname}")
        
        # Show ingresses
        ingresses = deployment_metadata.get('ingresses', [])
        if ingresses:
            print(f"Ingresses: {len(ingresses)} found")
            for ingress in ingresses:
                ingress_name = ingress.get('name', 'N/A')
                host = ingress.get('host', 'N/A')
                path = ingress.get('path', 'N/A')
                print(f"  - {ingress_name}: {host}{path}")
        
        # Show configmaps and secrets
        configmaps = deployment_metadata.get('configmaps', [])
        if configmaps:
            print(f"ConfigMaps: {len(configmaps)} found")
            for cm in configmaps:
                cm_name = cm.get('name', 'N/A')
                data_keys = cm.get('data_keys', [])
                print(f"  - {cm_name}: {len(data_keys)} keys")
        
        secrets = deployment_metadata.get('secrets', [])
        if secrets:
            print(f"Secrets: {len(secrets)} found (details redacted)")
            # Details of secrets are redacted for security reasons.
            # If you must log secret metadata, use only generic, non-identifying info.
            # for secret in secrets:
            #     ... # (redacted)
            #     print("  - [REDACTED]")
                
    except Exception as e:
        print(f"Error collecting deployment metadata: {e}")
    
    print("\n--- Collecting Security Context ---")
    try:
        security_context = collector.get_security_context()
        print(f"User ID: {security_context.get('user_id', 'N/A')}")
        print(f"Group ID: {security_context.get('group_id', 'N/A')}")
        print(f"Run as Non-Root: {security_context.get('run_as_non_root', 'N/A')}")
        print(f"Read-Only Root FS: {security_context.get('read_only_root_filesystem', 'N/A')}")
        
        capabilities = security_context.get('capabilities', {})
        if capabilities:
            print(f"Capabilities: {json.dumps(capabilities, indent=2)}")
            
    except Exception as e:
        print(f"Error collecting security context: {e}")
    
    print("\n--- Cache Information ---")
    all_metadata = collector.get_all_metadata()
    cache_info = all_metadata.get('cache_info', {})
    print(f"Cache TTL: {cache_info.get('cache_ttl', 'N/A')} seconds")
    print(f"Cached Keys: {cache_info.get('cached_keys', [])}")
    
    cache_ages = cache_info.get('cache_ages', {})
    if cache_ages:
        print("Cache Ages:")
        for key, age in cache_ages.items():
            print(f"  - {key}: {age:.2f} seconds old")
    
    print("\n--- Testing Cache Refresh ---")
    try:
        collector.refresh_metadata_cache()
        print("✓ Cache refreshed successfully")
    except Exception as e:
        print(f"Error refreshing cache: {e}")
    
    print("\n=== Demo Complete ===")

if __name__ == "__main__":
    main()