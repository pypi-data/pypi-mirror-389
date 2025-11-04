# Security Monitoring Whitelist Feature

## Overview

The ucbl-logger security monitoring system includes a comprehensive whitelist feature to prevent false positives in containerized environments, particularly Kubernetes/EKS deployments. This feature allows legitimate system mounts, filesystem types, and devices to be excluded from security alerts while maintaining robust security monitoring.

## Problem Statement

Container orchestration platforms like Kubernetes mount various system paths and use specific filesystem types that are legitimate and necessary for operation. Without a whitelist, the security monitor generates false positive alerts for:

- Kubernetes service account tokens (`/run/secrets/kubernetes.io/serviceaccount`)
- EKS IAM role tokens (`/run/secrets/eks.amazonaws.com/serviceaccount`)
- Istio sidecar mounts (`/var/run/secrets/istio`, `/etc/istio`)
- Standard container filesystems (overlay, tmpfs, proc, sysfs)
- Temporary directories (`/tmp`, `/var/tmp`)

## Features

### 1. Kubernetes-Aware Mode

Automatically whitelists common Kubernetes patterns when enabled.

**Environment Variable:**
```bash
UCBL_SECURITY_KUBERNETES_MODE=true  # Default: true
```

**Default Kubernetes Whitelists:**

**Allowed Mounts:**
- `/run/secrets/kubernetes.io/serviceaccount` - K8s service account tokens
- `/run/secrets/eks.amazonaws.com/serviceaccount` - EKS IAM role tokens
- `/var/run/secrets/kubernetes.io` - K8s secrets
- `/var/run/secrets/istio` - Istio certificates
- `/etc/istio` - Istio configuration
- `/tmp` - Temporary files
- `/var/tmp` - Temporary files
- `/proc` - Process information
- `/sys` - System information
- `/dev/shm` - Shared memory

**Allowed Filesystem Types:**
- `overlay` - Container overlay filesystem
- `tmpfs` - Temporary filesystem
- `proc` - Process filesystem
- `sysfs` - System filesystem
- `devtmpfs` - Device filesystem

**Allowed Devices:**
- `overlay` - Overlay device
- `tmpfs` - Temporary filesystem device
- `proc` - Process filesystem device
- `sysfs` - System filesystem device
- `devtmpfs` - Device filesystem device
- `shm` - Shared memory device

### 2. Custom Whitelists

Override or extend default whitelists with custom values.

**Environment Variables:**

```bash
# Custom mount points (comma-separated)
UCBL_SECURITY_ALLOWED_MOUNTS="/tmp,/run/secrets/kubernetes.io/serviceaccount,/custom/mount"

# Custom filesystem types (comma-separated)
UCBL_SECURITY_ALLOWED_FS_TYPES="overlay,tmpfs,ext4"

# Custom devices (comma-separated)
UCBL_SECURITY_ALLOWED_DEVICES="overlay,tmpfs,sda1"
```

### 3. Path Matching

The whitelist supports both exact and prefix matching:

- **Exact Match**: `/tmp` matches only `/tmp`
- **Prefix Match**: `/tmp` also matches `/tmp/subdir`, `/tmp/file.txt`, etc.

## Configuration Examples

### Example 1: Standard Kubernetes Deployment

```yaml
env:
  - name: UCBL_ENABLE_SECURITY_MONITORING
    value: "true"
  - name: UCBL_SECURITY_KUBERNETES_MODE
    value: "true"
```

This enables security monitoring with automatic Kubernetes whitelisting.

### Example 2: Custom Whitelist

```yaml
env:
  - name: UCBL_ENABLE_SECURITY_MONITORING
    value: "true"
  - name: UCBL_SECURITY_KUBERNETES_MODE
    value: "false"
  - name: UCBL_SECURITY_ALLOWED_MOUNTS
    value: "/tmp,/app/data,/custom/mount"
  - name: UCBL_SECURITY_ALLOWED_FS_TYPES
    value: "overlay,tmpfs,nfs"
```

This uses custom whitelists instead of Kubernetes defaults.

### Example 3: Extended Kubernetes Whitelist

```yaml
env:
  - name: UCBL_ENABLE_SECURITY_MONITORING
    value: "true"
  - name: UCBL_SECURITY_KUBERNETES_MODE
    value: "true"
  - name: UCBL_SECURITY_ALLOWED_MOUNTS
    value: "/run/secrets/kubernetes.io/serviceaccount,/run/secrets/eks.amazonaws.com/serviceaccount,/etc/istio,/var/run/secrets/istio,/tmp,/app/custom"
```

This extends the Kubernetes whitelist with an additional custom mount.

## API Usage

### Python Code Example

```python
from ucbl_logger.enhanced.security.advanced_monitor import RuntimeSecurityMonitor

# Initialize with Kubernetes mode
monitor = RuntimeSecurityMonitor()

# The whitelist is automatically configured from environment variables
# Check if a path is whitelisted
is_safe = monitor._is_path_whitelisted('/tmp/myfile')

# Check if a filesystem type is whitelisted
is_safe_fs = monitor._is_fs_type_whitelisted('overlay')

# Check if a device is whitelisted
is_safe_device = monitor._is_device_whitelisted('tmpfs')
```

## Security Considerations

### What Gets Whitelisted

✅ **Safe to Whitelist:**
- Standard Kubernetes mounts
- Service account tokens
- Istio sidecar mounts
- Temporary directories
- Standard container filesystems

### What Should NOT Be Whitelisted

❌ **Never Whitelist:**
- `/var/run/docker.sock` - Docker socket (container escape vector)
- `/dev/mem` - Physical memory access
- `/dev/kmem` - Kernel memory access
- `/host` - Host filesystem mounts
- Suspicious network ports (4444, 5555, etc.)

### Defense in Depth

The whitelist feature is part of a defense-in-depth strategy:

1. **Whitelist** - Reduces false positives for known-good patterns
2. **Monitoring** - Continues to monitor non-whitelisted activity
3. **Alerting** - Generates alerts for suspicious activity
4. **Logging** - Records all security events for audit

## Troubleshooting

### Issue: False Positive Alerts

**Symptom:** Security alerts for legitimate Kubernetes mounts

**Solution:**
```bash
# Enable Kubernetes mode
UCBL_SECURITY_KUBERNETES_MODE=true
```

### Issue: Custom Mount Not Whitelisted

**Symptom:** Alerts for application-specific mounts

**Solution:**
```bash
# Add custom mount to whitelist
UCBL_SECURITY_ALLOWED_MOUNTS="/tmp,/run/secrets/kubernetes.io/serviceaccount,/my/custom/mount"
```

### Issue: Container Escape False Positive

**Symptom:** "Host root filesystem access detected" in Kubernetes

**Solution:**
```bash
# Kubernetes mode automatically disables problematic checks
UCBL_SECURITY_KUBERNETES_MODE=true
```

## Logging

The whitelist configuration is logged at initialization:

```
INFO:ucbl_logger.enhanced.security.advanced_monitor:Security whitelist initialized (K8s mode: True)
DEBUG:ucbl_logger.enhanced.security.advanced_monitor:Allowed mounts: 10 entries
DEBUG:ucbl_logger.enhanced.security.advanced_monitor:Allowed FS types: {'overlay', 'tmpfs', 'proc', 'sysfs', 'devtmpfs'}
DEBUG:ucbl_logger.enhanced.security.advanced_monitor:Allowed devices: {'overlay', 'tmpfs', 'proc', 'sysfs', 'devtmpfs', 'shm'}
```

## Version History

- **v1.0.21** - Added whitelist feature with Kubernetes-aware mode
- **v1.0.20** - Initial security monitoring (caused false positives)

## Best Practices

1. **Always enable Kubernetes mode** in K8s/EKS deployments
2. **Use custom whitelists sparingly** - only for application-specific needs
3. **Review whitelist periodically** - ensure it's not too permissive
4. **Monitor security logs** - even with whitelisting enabled
5. **Test in non-production first** - validate whitelist configuration

## Related Documentation

- [Security Monitoring Overview](./README.md)
- [Enhanced EKS Logger](../README.md)
- [Configuration Guide](../config.py)
