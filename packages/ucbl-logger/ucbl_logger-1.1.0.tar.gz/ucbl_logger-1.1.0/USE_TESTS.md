# UCBLLogger Test Usage Guide

This guide explains how to properly run and use the tests in the UCBLLogger project, especially for GitHub Actions and CI/CD environments.

## Table of Contents

1. [Test Structure Overview](#test-structure-overview)
2. [Common Test Failures](#common-test-failures)
3. [Local Testing Setup](#local-testing-setup)
4. [GitHub Actions Configuration](#github-actions-configuration)
5. [Test Dependencies](#test-dependencies)
6. [Running Tests](#running-tests)
7. [Troubleshooting](#troubleshooting)
8. [Test Categories](#test-categories)

## Test Structure Overview

The UCBLLogger project contains comprehensive tests organized as follows:

```
tests/
├── __init__.py
├── test_enhanced_eks_integration.py    # End-to-end integration tests
├── test_cloudwatch_integration.py      # CloudWatch functionality tests
├── test_kubernetes_metadata.py         # Kubernetes metadata collection tests
├── test_health_monitoring.py          # Health monitoring tests
├── test_performance_monitoring.py     # Performance monitoring tests
├── test_sampling_engine.py            # Log sampling tests
├── test_tracing.py                    # Distributed tracing tests
├── test_enhanced_security.py          # Security features tests
├── test_buffer_management.py          # Buffer management tests
├── test_logger.py                     # Core logger tests
└── test_log_methods.py                # Basic logging methods tests
```

## Common Test Failures

### 1. Missing Dependencies

**Problem**: Tests fail with `ImportError` or `ModuleNotFoundError`

**Solution**: Install all required dependencies:

```bash
# Install basic dependencies
pip install -r requirements.txt

# Install test dependencies
pip install pytest pytest-mock pytest-asyncio

# Install optional EKS dependencies
pip install kubernetes>=28.1.0 psutil>=5.8.0 boto3>=1.26.0
```

### 2. AWS/CloudWatch Tests Failing

**Problem**: CloudWatch integration tests fail without AWS credentials

**Solution**: Mock AWS services or skip tests in CI:

```python
# Set environment variable to skip AWS tests
export SKIP_AWS_TESTS=true

# Or mock boto3 in tests
@patch('boto3.client')
def test_cloudwatch_feature(self, mock_boto3):
    # Test implementation
    pass
```

### 3. Kubernetes API Tests Failing

**Problem**: Kubernetes metadata tests fail without cluster access

**Solution**: Tests are designed to gracefully degrade:

```python
# Tests automatically detect Kubernetes environment
# and use fallback methods when API is unavailable
```

### 4. Threading/Async Issues

**Problem**: Tests hang or fail due to threading issues

**Solution**: Ensure proper cleanup in tests:

```python
def tearDown(self):
    # Stop any background threads
    if hasattr(self, 'logger'):
        self.logger.shutdown()
```

## Local Testing Setup

### Prerequisites

1. **Python 3.6+** (recommended: Python 3.9+)
2. **Virtual Environment** (recommended)

### Setup Steps

```bash
# 1. Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 2. Install the package in development mode
pip install -e .

# 3. Install test dependencies
pip install pytest pytest-mock pytest-asyncio pytest-cov

# 4. Install optional dependencies for full testing
pip install kubernetes psutil boto3

# 5. Run tests
pytest tests/ -v
```

### Environment Variables for Testing

```bash
# Skip tests that require external services
export SKIP_AWS_TESTS=true
export SKIP_K8S_TESTS=true

# Set test environment
export ENVIRONMENT=test
export UCBL_LOG_LEVEL=DEBUG

# Mock Kubernetes environment
export KUBERNETES_NAMESPACE=test-namespace
export HOSTNAME=test-pod
export KUBERNETES_SERVICE_ACCOUNT=test-sa
```

## GitHub Actions Configuration

Create `.github/workflows/test.yml`:

```yaml
name: Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, "3.10", "3.11"]

    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Cache pip dependencies
      uses: actions/cache@v3
      with:
        path: ~/.cache/pip
        key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt', '**/pyproject.toml') }}
        restore-keys: |
          ${{ runner.os }}-pip-
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install pytest pytest-mock pytest-asyncio pytest-cov
        pip install -e .
        # Install optional dependencies for comprehensive testing
        pip install kubernetes psutil boto3 || echo "Optional dependencies failed, continuing..."
    
    - name: Set test environment variables
      run: |
        echo "SKIP_AWS_TESTS=true" >> $GITHUB_ENV
        echo "ENVIRONMENT=test" >> $GITHUB_ENV
        echo "UCBL_LOG_LEVEL=DEBUG" >> $GITHUB_ENV
        echo "KUBERNETES_NAMESPACE=test-namespace" >> $GITHUB_ENV
        echo "HOSTNAME=test-pod" >> $GITHUB_ENV
    
    - name: Run basic tests
      run: |
        pytest tests/test_logger.py tests/test_log_methods.py -v --tb=short
    
    - name: Run core functionality tests
      run: |
        pytest tests/test_enhanced_eks_integration.py -v --tb=short -k "not test_concurrent_logging_thread_safety"
    
    - name: Run unit tests (no external dependencies)
      run: |
        pytest tests/test_sampling_engine.py tests/test_buffer_management.py -v --tb=short
    
    - name: Run integration tests with mocking
      run: |
        pytest tests/test_cloudwatch_integration.py tests/test_kubernetes_metadata.py -v --tb=short
    
    - name: Run health and performance tests
      run: |
        pytest tests/test_health_monitoring.py tests/test_performance_monitoring.py -v --tb=short
    
    - name: Run security and tracing tests
      run: |
        pytest tests/test_enhanced_security.py tests/test_tracing.py -v --tb=short
    
    - name: Generate coverage report
      run: |
        pytest --cov=ucbl_logger --cov-report=xml --cov-report=html tests/
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        flags: unittests
        name: codecov-umbrella
        fail_ci_if_error: false

  test-minimal:
    runs-on: ubuntu-latest
    name: Test minimal installation
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: "3.9"
    
    - name: Install minimal dependencies only
      run: |
        python -m pip install --upgrade pip
        pip install pytest pytest-mock
        pip install -e .
    
    - name: Run core tests only
      run: |
        pytest tests/test_logger.py tests/test_log_methods.py -v
      env:
        SKIP_AWS_TESTS: true
        SKIP_K8S_TESTS: true
        SKIP_ENHANCED_TESTS: true
```

## Test Dependencies

### Required Dependencies

```txt
# Core testing
pytest>=7.0.0
pytest-mock>=3.10.0

# For async tests
pytest-asyncio>=0.21.0

# For coverage
pytest-cov>=4.0.0
```

### Optional Dependencies

```txt
# For CloudWatch tests
boto3>=1.26.0
moto>=4.0.0  # For mocking AWS services

# For Kubernetes tests
kubernetes>=28.1.0

# For performance tests
psutil>=5.8.0

# For enhanced features
opentelemetry-api>=1.15.0  # Optional tracing
```

### Development Dependencies

```txt
# Code quality
black>=22.0.0
flake8>=5.0.0
mypy>=1.0.0

# Documentation
sphinx>=5.0.0
sphinx-rtd-theme>=1.2.0
```

## Running Tests

### Basic Test Commands

```bash
# Run all tests
pytest tests/

# Run with verbose output
pytest tests/ -v

# Run specific test file
pytest tests/test_logger.py -v

# Run specific test method
pytest tests/test_logger.py::TestUCBLLogger::test_basic_logging -v

# Run tests with coverage
pytest tests/ --cov=ucbl_logger --cov-report=html

# Run tests in parallel (if pytest-xdist installed)
pytest tests/ -n auto
```

### Test Categories

```bash
# Core functionality tests (always run)
pytest tests/test_logger.py tests/test_log_methods.py -v

# Enhanced features tests (require optional dependencies)
pytest tests/test_enhanced_eks_integration.py -v

# External service tests (require mocking or real services)
pytest tests/test_cloudwatch_integration.py tests/test_kubernetes_metadata.py -v

# Performance tests (may be slow)
pytest tests/test_performance_monitoring.py -v -s

# Security tests
pytest tests/test_enhanced_security.py -v

# Integration tests (comprehensive)
pytest tests/test_enhanced_eks_integration.py -v
```

### Selective Test Running

```bash
# Skip slow tests
pytest tests/ -m "not slow"

# Skip external service tests
pytest tests/ -k "not cloudwatch and not kubernetes"

# Run only unit tests
pytest tests/ -k "not integration"

# Run with specific markers
pytest tests/ -m "unit"
```

## Troubleshooting

### Common Issues and Solutions

#### 1. Import Errors

**Error**: `ModuleNotFoundError: No module named 'ucbl_logger'`

**Solution**:
```bash
# Install in development mode
pip install -e .

# Or add to Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

#### 2. AWS Credential Errors

**Error**: `NoCredentialsError: Unable to locate credentials`

**Solution**:
```bash
# Set environment variable to skip AWS tests
export SKIP_AWS_TESTS=true

# Or mock AWS in tests
pytest tests/test_cloudwatch_integration.py -v --tb=short
```

#### 3. Kubernetes API Errors

**Error**: `kubernetes.config.config_exception.ConfigException`

**Solution**:
```bash
# Tests should handle this gracefully, but you can skip them
export SKIP_K8S_TESTS=true

# Or run with mocked Kubernetes environment
export KUBERNETES_NAMESPACE=test-namespace
export HOSTNAME=test-pod
pytest tests/test_kubernetes_metadata.py -v
```

#### 4. Threading Issues

**Error**: Tests hang or timeout

**Solution**:
```bash
# Run tests with timeout
pytest tests/ --timeout=60

# Skip concurrent tests
pytest tests/ -k "not concurrent and not thread"

# Run with single thread
pytest tests/ -n 0
```

#### 5. Memory Issues

**Error**: `MemoryError` or high memory usage

**Solution**:
```bash
# Run tests individually
pytest tests/test_performance_monitoring.py -v

# Reduce test parallelism
pytest tests/ -n 1

# Skip memory-intensive tests
pytest tests/ -k "not performance and not load"
```

### Debug Mode

```bash
# Run with debug output
pytest tests/ -v -s --tb=long

# Run with pdb on failure
pytest tests/ --pdb

# Run with logging output
pytest tests/ -v -s --log-cli-level=DEBUG
```

### Test Configuration

Create `pytest.ini` in project root:

```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --tb=short
    --strict-markers
    --disable-warnings
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
    unit: marks tests as unit tests
    aws: marks tests that require AWS services
    k8s: marks tests that require Kubernetes
    performance: marks performance tests
filterwarnings =
    ignore::DeprecationWarning
    ignore::PendingDeprecationWarning
```

### Environment-Specific Test Configuration

#### Development Environment

```bash
# .env.test file
ENVIRONMENT=development
UCBL_LOG_LEVEL=DEBUG
SKIP_AWS_TESTS=false
SKIP_K8S_TESTS=false
ENABLE_PERFORMANCE_TESTS=true
```

#### CI Environment

```bash
# GitHub Actions environment
ENVIRONMENT=test
UCBL_LOG_LEVEL=INFO
SKIP_AWS_TESTS=true
SKIP_K8S_TESTS=true
ENABLE_PERFORMANCE_TESTS=false
```

#### Production Testing

```bash
# Production-like testing
ENVIRONMENT=production
UCBL_LOG_LEVEL=WARN
SKIP_AWS_TESTS=false  # Use real AWS services
SKIP_K8S_TESTS=false  # Use real Kubernetes
ENABLE_PERFORMANCE_TESTS=true
```

## Test Best Practices

### 1. Test Isolation

```python
def setUp(self):
    """Set up test fixtures"""
    self.logger = UCBLLogger(service_name="test-service")

def tearDown(self):
    """Clean up after tests"""
    if hasattr(self, 'logger'):
        self.logger.shutdown()
```

### 2. Mocking External Services

```python
@patch('boto3.client')
def test_cloudwatch_integration(self, mock_boto3):
    """Test CloudWatch with mocked AWS"""
    mock_client = Mock()
    mock_boto3.return_value = mock_client
    
    # Test implementation
    logger = EnhancedEKSLogger(enable_cloudwatch=True)
    logger.info("Test message")
    
    # Verify mock was called
    mock_boto3.assert_called_once()
```

### 3. Environment Variable Management

```python
@patch.dict(os.environ, {
    'KUBERNETES_NAMESPACE': 'test-namespace',
    'HOSTNAME': 'test-pod'
})
def test_kubernetes_metadata(self):
    """Test with controlled environment"""
    collector = KubernetesMetadataCollector()
    metadata = collector.collect_pod_metadata()
    
    self.assertEqual(metadata['namespace'], 'test-namespace')
```

### 4. Async Test Handling

```python
import asyncio
import pytest

@pytest.mark.asyncio
async def test_async_functionality():
    """Test async functionality"""
    logger = EnhancedEKSLogger()
    
    # Test async operations
    await logger.async_log("Test message")
    
    # Cleanup
    await logger.async_shutdown()
```

### 5. Performance Test Guidelines

```python
def test_performance_under_load(self):
    """Test performance with controlled load"""
    logger = EnhancedEKSLogger()
    
    start_time = time.time()
    
    # Generate controlled load
    for i in range(1000):
        logger.info(f"Message {i}")
    
    duration = time.time() - start_time
    
    # Assert reasonable performance
    self.assertLess(duration, 5.0, "Logging took too long")
    
    logger.shutdown()
```

## Continuous Integration Tips

### 1. Matrix Testing

Test across multiple Python versions and dependency combinations:

```yaml
strategy:
  matrix:
    python-version: [3.8, 3.9, "3.10", "3.11"]
    dependencies: [minimal, full]
```

### 2. Conditional Test Execution

```yaml
- name: Run AWS tests
  if: env.AWS_ACCESS_KEY_ID != ''
  run: pytest tests/test_cloudwatch_integration.py -v

- name: Run Kubernetes tests
  if: env.KUBECONFIG != ''
  run: pytest tests/test_kubernetes_metadata.py -v
```

### 3. Artifact Collection

```yaml
- name: Upload test results
  uses: actions/upload-artifact@v3
  if: always()
  with:
    name: test-results
    path: |
      htmlcov/
      coverage.xml
      pytest-report.xml
```

This comprehensive guide should help you successfully run the UCBLLogger tests in any environment, including GitHub Actions. The key is understanding the dependencies, properly mocking external services, and configuring the environment appropriately for your testing scenario.