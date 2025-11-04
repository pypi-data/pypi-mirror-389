# UCBLLogger Enhanced EKS Examples

This document provides comprehensive examples and use case scenarios for the Enhanced UCBLLogger in EKS environments. Each example demonstrates real-world scenarios with detailed explanations and best practices.

## Table of Contents

1. [Quick Start Examples](#quick-start-examples)
2. [Use Case Scenarios](#use-case-scenarios)
3. [Integration Examples](#integration-examples)
4. [Advanced Configuration Examples](#advanced-configuration-examples)
5. [Troubleshooting Examples](#troubleshooting-examples)
6. [Performance Optimization Examples](#performance-optimization-examples)

## Quick Start Examples

### Basic Enhanced Logger Setup

```python
from ucbl_logger.enhanced import EnhancedEKSLogger

# Minimal setup for EKS environment
logger = EnhancedEKSLogger(
    service_name="my-application",
    namespace="production"
)

logger.info("Service started successfully")
```

### Environment-Based Configuration

```python
import os
from ucbl_logger.enhanced import EnhancedEKSLogger
from ucbl_logger.enhanced.config import SamplingConfig, BufferConfig

# Production configuration
if os.getenv('ENVIRONMENT') == 'production':
    logger = EnhancedEKSLogger(
        service_name=os.getenv('SERVICE_NAME', 'my-application'),
        namespace=os.getenv('NAMESPACE', 'production'),
        enable_sampling=True,
        sampling_config=SamplingConfig(
            default_rate=0.1,  # Sample 10% of logs
            preserve_errors=True
        ),
        enable_cloudwatch=True,
        enable_performance_monitoring=True
    )
else:
    # Development configuration - no sampling, more verbose
    logger = EnhancedEKSLogger(
        service_name=os.getenv('SERVICE_NAME', 'my-application-dev'),
        namespace=os.getenv('NAMESPACE', 'development'),
        enable_sampling=False,
        enable_cloudwatch=False,
        log_level='DEBUG'
    )

logger.info("Logger configured for environment", 
           metadata={"environment": os.getenv('ENVIRONMENT')})
```

## Use Case Scenarios

### 1. Data Processing Service

**Scenario**: A data processing service that handles user requests and generates responses. Needs comprehensive logging for debugging, performance monitoring, and cost optimization.

```python
import time
from ucbl_logger.enhanced import EnhancedEKSLogger
from ucbl_logger.enhanced.config import SamplingConfig, PerformanceThresholds

# Configure logger for data processing service
logger = EnhancedEKSLogger(
    service_name="data-query-processor",
    namespace="ai-platform",
    enable_tracing=True,
    enable_performance_monitoring=True,
    enable_sampling=True,
    sampling_config=SamplingConfig(
        default_rate=0.2,  # Sample 20% of logs
        level_rates={
            'DEBUG': 0.05,   # Only 5% of debug logs
            'INFO': 0.2,     # 20% of info logs
            'WARNING': 0.8,  # 80% of warnings
            'ERROR': 1.0,    # All errors
            'CRITICAL': 1.0  # All critical logs
        },
        preserve_errors=True,
        volume_threshold=1000  # Activate sampling at 1000 logs/min
    ),
    performance_config=PerformanceThresholds(
        cpu_warning=70.0,
        memory_warning=75.0,
        collection_interval=60  # Check every minute
    )
)

def process_user_query(user_id, query, session_id):
    """Process a user query with comprehensive logging"""
    
    # Start distributed trace for the entire operation
    correlation_id = logger.start_trace("query_processing")
    
    logger.info("Query processing started", 
               correlation_id=correlation_id,
               metadata={
                   "user_id": user_id,
                   "session_id": session_id,
                   "query_length": len(query),
                   "query_type": "semantic_search"
               })
    
    try:
        # Step 1: Query validation and preprocessing
        logger.debug("Validating query", correlation_id=correlation_id)
        if not query or len(query.strip()) < 3:
            logger.warning("Invalid query received", 
                          correlation_id=correlation_id,
                          metadata={"validation_error": "query_too_short"})
            return {"error": "Query too short"}
        
        # Step 2: Semantic embedding generation
        start_time = time.time()
        logger.info("Generating semantic embeddings", correlation_id=correlation_id)
        
        # Simulate embedding generation
        time.sleep(0.1)
        embedding_time = time.time() - start_time
        
        logger.info("Embeddings generated successfully", 
                   correlation_id=correlation_id,
                   metadata={
                       "embedding_time_ms": embedding_time * 1000,
                       "embedding_dimensions": 1536
                   })
        
        # Step 3: Vector search
        start_time = time.time()
        logger.info("Performing vector search", correlation_id=correlation_id)
        
        # Simulate vector search
        time.sleep(0.05)
        search_time = time.time() - start_time
        
        logger.info("Vector search completed", 
                   correlation_id=correlation_id,
                   metadata={
                       "search_time_ms": search_time * 1000,
                       "results_found": 15,
                       "similarity_threshold": 0.8
                   })
        
        # Step 4: Response generation
        start_time = time.time()
        logger.info("Generating response", correlation_id=correlation_id)
        
        # Simulate response generation
        time.sleep(0.2)
        generation_time = time.time() - start_time
        
        response = {
            "answer": "Generated response based on semantic search",
            "confidence": 0.92,
            "sources": ["doc1.pdf", "doc2.pdf"],
            "processing_time_ms": (embedding_time + search_time + generation_time) * 1000
        }
        
        logger.info("Response generated successfully", 
                   correlation_id=correlation_id,
                   metadata={
                       "generation_time_ms": generation_time * 1000,
                       "response_confidence": response["confidence"],
                       "sources_count": len(response["sources"]),
                       "total_processing_time_ms": response["processing_time_ms"]
                   })
        
        # End trace successfully
        logger.end_trace(correlation_id, success=True, 
                        metadata={"total_time_ms": response["processing_time_ms"]})
        
        return response
        
    except Exception as e:
        logger.error("Query processing failed", 
                    correlation_id=correlation_id,
                    metadata={
                        "error_type": type(e).__name__,
                        "error_message": str(e)
                    })
        
        # End trace with failure
        logger.end_trace(correlation_id, success=False, 
                        metadata={"error": str(e)})
        
        return {"error": "Processing failed"}

# Example usage
if __name__ == "__main__":
    # Process multiple queries to demonstrate logging
    queries = [
        ("user123", "What is machine learning?", "session_abc"),
        ("user456", "How does neural network training work?", "session_def"),
        ("user789", "", "session_ghi"),  # Invalid query
    ]
    
    for user_id, query, session_id in queries:
        result = process_user_query(user_id, query, session_id)
        print(f"Result: {result}")
    
    # Log performance metrics
    logger.log_performance_metrics()
    
    # Get health status
    health = logger.get_health_status()
    print(f"Logger health: {health}")
```

### 2. Microservice with High-Volume Logging

**Scenario**: A high-traffic microservice that needs intelligent sampling to control costs while preserving important logs.

```python
from ucbl_logger.enhanced import EnhancedEKSLogger
from ucbl_logger.enhanced.config import SamplingConfig, BufferConfig, CloudWatchConfig

# Configure for high-volume scenario
logger = EnhancedEKSLogger(
    service_name="high-traffic-api",
    namespace="production",
    enable_sampling=True,
    sampling_config=SamplingConfig(
        enabled=True,
        strategy="adaptive",  # Automatically adjust based on volume
        default_rate=0.05,    # Very aggressive sampling (5%)
        volume_threshold=500, # Start sampling at 500 logs/min
        adaptive_enabled=True,
        preserve_errors=True,
        preserve_patterns=[
            r"payment.*failed",     # Always preserve payment failures
            r"security.*violation", # Always preserve security events
            r"user.*login"          # Always preserve login events
        ]
    ),
    buffer_config=BufferConfig(
        max_size=50000,        # Large buffer for high volume
        flush_interval=10,     # Flush every 10 seconds
        async_flush=True,      # Non-blocking flushes
        compression_enabled=True
    ),
    cloudwatch_config=CloudWatchConfig(
        batch_size=1000,       # Large batches for efficiency
        enable_compression=True,
        enable_deduplication=True,
        cost_optimization=True
    )
)

def handle_api_request(request_id, endpoint, user_id, request_data):
    """Handle API request with intelligent logging"""
    
    correlation_id = logger.start_trace("api_request")
    
    # Always log API requests (high business value)
    logger.info("API request received", 
               correlation_id=correlation_id,
               metadata={
                   "request_id": request_id,
                   "endpoint": endpoint,
                   "user_id": user_id,
                   "request_size": len(str(request_data)),
                   "user_agent": request_data.get("user_agent", "unknown")
               })
    
    # Debug logs will be heavily sampled
    logger.debug("Processing request data", 
                correlation_id=correlation_id,
                metadata={"data_keys": list(request_data.keys())})
    
    # Simulate processing
    if endpoint == "/payment":
        # Payment processing - always preserve these logs
        logger.info("Processing payment", 
                   correlation_id=correlation_id,
                   metadata={
                       "amount": request_data.get("amount"),
                       "currency": request_data.get("currency", "USD"),
                       "payment_method": request_data.get("method", "card")
                   })
        
        # Simulate payment failure (will always be preserved)
        if request_data.get("amount", 0) > 10000:
            logger.error("Payment failed - amount too high", 
                        correlation_id=correlation_id,
                        metadata={
                            "failure_reason": "amount_limit_exceeded",
                            "attempted_amount": request_data.get("amount")
                        })
            return {"error": "Payment failed"}
    
    elif endpoint == "/search":
        # Search requests - can be sampled more aggressively
        logger.debug("Performing search", 
                    correlation_id=correlation_id,
                    metadata={
                        "query": request_data.get("query"),
                        "filters": request_data.get("filters", {})
                    })
    
    # Response logging
    logger.info("API request completed", 
               correlation_id=correlation_id,
               metadata={
                   "response_time_ms": 150,  # Simulated
                   "status_code": 200
               })
    
    logger.end_trace(correlation_id, success=True)
    return {"status": "success"}

# Simulate high-volume traffic
if __name__ == "__main__":
    import random
    import time
    
    endpoints = ["/search", "/payment", "/profile", "/analytics"]
    
    print("Simulating high-volume traffic...")
    
    for i in range(1000):  # Simulate 1000 requests
        endpoint = random.choice(endpoints)
        request_data = {
            "user_agent": "Mozilla/5.0",
            "query": f"search term {i}" if endpoint == "/search" else None,
            "amount": random.randint(10, 15000) if endpoint == "/payment" else None,
            "method": "card" if endpoint == "/payment" else None
        }
        
        handle_api_request(f"req_{i}", endpoint, f"user_{i%100}", request_data)
        
        # Small delay to simulate realistic traffic
        if i % 100 == 0:
            print(f"Processed {i} requests...")
            time.sleep(0.1)
    
    # Check sampling statistics
    stats = logger.get_sampling_statistics()
    print(f"Sampling statistics: {stats}")
```

### 3. Batch Processing Job with Performance Monitoring

**Scenario**: A batch job that processes large datasets and needs performance monitoring to optimize resource usage.

```python
from ucbl_logger.enhanced import EnhancedEKSLogger
from ucbl_logger.enhanced.config import PerformanceThresholds

# Configure for batch processing
logger = EnhancedEKSLogger(
    service_name="data-processing-batch",
    namespace="batch-jobs",
    enable_performance_monitoring=True,
    performance_config=PerformanceThresholds(
        cpu_warning=80.0,
        cpu_critical=95.0,
        memory_warning=85.0,
        memory_critical=95.0,
        collection_interval=30,  # Check every 30 seconds
        enable_detailed_metrics=True
    ),
    enable_sampling=False,  # Don't sample batch job logs
    enable_cloudwatch=True
)

def process_batch_job(job_id, input_files, batch_size=1000):
    """Process batch job with performance monitoring"""
    
    correlation_id = logger.start_trace("batch_processing")
    
    logger.info("Batch job started", 
               correlation_id=correlation_id,
               metadata={
                   "job_id": job_id,
                   "input_files_count": len(input_files),
                   "batch_size": batch_size,
                   "estimated_records": len(input_files) * 10000  # Estimate
               })
    
    total_processed = 0
    
    try:
        for file_index, input_file in enumerate(input_files):
            file_correlation_id = logger.start_trace("file_processing", parent_id=correlation_id)
            
            logger.info("Processing file", 
                       correlation_id=file_correlation_id,
                       metadata={
                           "file_name": input_file,
                           "file_index": file_index + 1,
                           "total_files": len(input_files)
                       })
            
            # Log performance metrics before processing
            logger.log_performance_metrics(correlation_id=file_correlation_id)
            
            # Simulate file processing
            records_in_file = 10000  # Simulated
            batches = (records_in_file + batch_size - 1) // batch_size
            
            for batch_index in range(batches):
                batch_correlation_id = logger.start_trace("batch_processing", parent_id=file_correlation_id)
                
                start_record = batch_index * batch_size
                end_record = min(start_record + batch_size, records_in_file)
                records_in_batch = end_record - start_record
                
                logger.debug("Processing batch", 
                           correlation_id=batch_correlation_id,
                           metadata={
                               "batch_index": batch_index + 1,
                               "total_batches": batches,
                               "records_in_batch": records_in_batch,
                               "start_record": start_record,
                               "end_record": end_record
                           })
                
                # Simulate processing time
                import time
                time.sleep(0.01)  # Simulate work
                
                total_processed += records_in_batch
                
                # Log progress every 10 batches
                if (batch_index + 1) % 10 == 0:
                    logger.info("Batch progress", 
                               correlation_id=batch_correlation_id,
                               metadata={
                                   "batches_completed": batch_index + 1,
                                   "total_batches": batches,
                                   "progress_percent": ((batch_index + 1) / batches) * 100,
                                   "records_processed": total_processed
                               })
                    
                    # Check performance and log if concerning
                    performance_metrics = logger.get_current_performance_metrics()
                    if performance_metrics:
                        cpu_usage = performance_metrics.get('cpu_percent', 0)
                        memory_usage = performance_metrics.get('memory_percent', 0)
                        
                        if cpu_usage > 90 or memory_usage > 90:
                            logger.warning("High resource usage detected", 
                                         correlation_id=batch_correlation_id,
                                         metadata={
                                             "cpu_usage_percent": cpu_usage,
                                             "memory_usage_percent": memory_usage,
                                             "recommendation": "Consider reducing batch size"
                                         })
                
                logger.end_trace(batch_correlation_id, success=True)
            
            logger.info("File processing completed", 
                       correlation_id=file_correlation_id,
                       metadata={
                           "records_processed": records_in_file,
                           "batches_processed": batches
                       })
            
            logger.end_trace(file_correlation_id, success=True)
        
        # Final performance summary
        final_metrics = logger.get_current_performance_metrics()
        
        logger.info("Batch job completed successfully", 
                   correlation_id=correlation_id,
                   metadata={
                       "total_records_processed": total_processed,
                       "files_processed": len(input_files),
                       "final_cpu_usage": final_metrics.get('cpu_percent', 0),
                       "final_memory_usage": final_metrics.get('memory_percent', 0)
                   })
        
        logger.end_trace(correlation_id, success=True, 
                        metadata={"records_processed": total_processed})
        
        return {"status": "success", "records_processed": total_processed}
        
    except Exception as e:
        logger.error("Batch job failed", 
                    correlation_id=correlation_id,
                    metadata={
                        "error_type": type(e).__name__,
                        "error_message": str(e),
                        "records_processed_before_failure": total_processed
                    })
        
        logger.end_trace(correlation_id, success=False, metadata={"error": str(e)})
        raise

# Example usage
if __name__ == "__main__":
    input_files = [f"data_file_{i}.csv" for i in range(5)]
    
    try:
        result = process_batch_job("job_12345", input_files, batch_size=500)
        print(f"Job completed: {result}")
        
        # Get final health status
        health = logger.get_health_status()
        print(f"Final logger health: {health}")
        
    except Exception as e:
        print(f"Job failed: {e}")
```

### 4. Security-Sensitive Application

**Scenario**: An application handling sensitive data that needs comprehensive security monitoring and data redaction.

```python
from ucbl_logger.enhanced import EnhancedEKSLogger
from ucbl_logger.enhanced.config import SecurityConfig

# Configure with enhanced security
logger = EnhancedEKSLogger(
    service_name="secure-data-processor",
    namespace="security",
    enable_security_monitoring=True,
    security_config=SecurityConfig(
        enable_data_redaction=True,
        redaction_patterns=[
            r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email
            r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',  # Credit cards
            r'\b[A-Za-z0-9]{32,}\b',  # API keys
            r'Bearer\s+[A-Za-z0-9\-._~+/]+=*',  # Bearer tokens
        ],
        audit_redactions=True,
        security_event_threshold=5  # Alert after 5 security events
    ),
    enable_tracing=True
)

def process_user_data(user_id, personal_data):
    """Process user data with security monitoring"""
    
    correlation_id = logger.start_trace("user_data_processing")
    
    # Log data processing start (PII will be redacted)
    logger.info("Processing user data", 
               correlation_id=correlation_id,
               metadata={
                   "user_id": user_id,
                   "data_fields": list(personal_data.keys()),
                   "processing_type": "profile_update"
               })
    
    # Simulate security checks
    security_checks = [
        "authentication_valid",
        "authorization_verified", 
        "data_validation_passed",
        "rate_limit_check"
    ]
    
    for check in security_checks:
        logger.debug(f"Security check: {check}", 
                    correlation_id=correlation_id,
                    metadata={"security_check": check, "status": "passed"})
    
    # Process sensitive data (will be redacted in logs)
    if "email" in personal_data:
        logger.info("Updating email address", 
                   correlation_id=correlation_id,
                   metadata={
                       "old_email": personal_data.get("old_email", ""),  # Will be redacted
                       "new_email": personal_data.get("email", ""),     # Will be redacted
                       "email_verified": False
                   })
    
    if "ssn" in personal_data:
        logger.info("Processing SSN", 
                   correlation_id=correlation_id,
                   metadata={
                       "ssn": personal_data["ssn"],  # Will be redacted
                       "ssn_format_valid": True
                   })
    
    # Simulate security event
    if personal_data.get("suspicious_activity", False):
        logger.warning("Suspicious activity detected", 
                      correlation_id=correlation_id,
                      metadata={
                          "activity_type": "multiple_failed_attempts",
                          "source_ip": "192.168.1.100",  # Could be redacted if configured
                          "user_agent": "suspicious_bot",
                          "security_level": "medium"
                      })
        
        # Log security event
        logger.log_security_event(
            event_type="suspicious_activity",
            severity="medium",
            description="Multiple failed authentication attempts",
            metadata={
                "user_id": user_id,
                "correlation_id": correlation_id,
                "source": "authentication_service"
            }
        )
    
    logger.info("User data processing completed", 
               correlation_id=correlation_id,
               metadata={
                   "fields_updated": len(personal_data),
                   "security_checks_passed": len(security_checks)
               })
    
    logger.end_trace(correlation_id, success=True)

def handle_authentication_attempt(username, password, source_ip):
    """Handle authentication with security logging"""
    
    correlation_id = logger.start_trace("authentication_attempt")
    
    logger.info("Authentication attempt", 
               correlation_id=correlation_id,
               metadata={
                   "username": username,
                   "source_ip": source_ip,
                   "auth_method": "password"
               })
    
    # Simulate authentication logic
    if password == "weak_password":
        logger.warning("Weak password detected", 
                      correlation_id=correlation_id,
                      metadata={
                          "username": username,
                          "password_strength": "weak",
                          "recommendation": "force_password_change"
                      })
        
        logger.log_security_event(
            event_type="weak_password",
            severity="low",
            description="User attempting to use weak password",
            metadata={
                "username": username,
                "correlation_id": correlation_id
            }
        )
    
    if username == "admin" and source_ip.startswith("192.168."):
        logger.error("Unauthorized admin access attempt", 
                    correlation_id=correlation_id,
                    metadata={
                        "username": username,
                        "source_ip": source_ip,
                        "access_level": "admin",
                        "network": "internal"
                    })
        
        logger.log_security_event(
            event_type="unauthorized_access",
            severity="high",
            description="Unauthorized admin access attempt from internal network",
            metadata={
                "username": username,
                "source_ip": source_ip,
                "correlation_id": correlation_id
            }
        )
        
        logger.end_trace(correlation_id, success=False, 
                        metadata={"failure_reason": "unauthorized_access"})
        return False
    
    logger.info("Authentication successful", 
               correlation_id=correlation_id,
               metadata={
                   "username": username,
                   "auth_duration_ms": 150
               })
    
    logger.end_trace(correlation_id, success=True)
    return True

# Example usage
if __name__ == "__main__":
    # Test data processing with PII
    user_data = {
        "email": "john.doe@example.com",
        "ssn": "123-45-6789",
        "phone": "555-123-4567",
        "api_key": "sk_test_1234567890abcdef1234567890abcdef",
        "suspicious_activity": True
    }
    
    process_user_data("user_12345", user_data)
    
    # Test authentication scenarios
    auth_attempts = [
        ("john_doe", "strong_password123!", "203.0.113.1"),
        ("admin", "weak_password", "192.168.1.100"),  # Should trigger security alert
        ("jane_smith", "another_strong_pass", "198.51.100.1")
    ]
    
    for username, password, ip in auth_attempts:
        success = handle_authentication_attempt(username, password, ip)
        print(f"Auth for {username}: {'Success' if success else 'Failed'}")
    
    # Check security monitoring status
    security_status = logger.get_security_status()
    print(f"Security status: {security_status}")
    
    # Get redaction statistics
    redaction_stats = logger.get_redaction_statistics()
    print(f"Redaction statistics: {redaction_stats}")
```

## Integration Examples

### Flask Web Application Integration

```python
from flask import Flask, request, jsonify
from ucbl_logger.enhanced import EnhancedEKSLogger
import uuid

app = Flask(__name__)

# Initialize logger for Flask app
logger = EnhancedEKSLogger(
    service_name="flask-api",
    namespace="web-services",
    enable_tracing=True,
    enable_performance_monitoring=True
)

@app.before_request
def before_request():
    """Set up tracing for each request"""
    request.correlation_id = request.headers.get('X-Correlation-ID') or str(uuid.uuid4())
    request.start_time = time.time()
    
    logger.info("Request started", 
               correlation_id=request.correlation_id,
               metadata={
                   "method": request.method,
                   "path": request.path,
                   "remote_addr": request.remote_addr,
                   "user_agent": request.headers.get('User-Agent', '')
               })

@app.after_request
def after_request(response):
    """Log request completion"""
    duration = (time.time() - request.start_time) * 1000
    
    logger.info("Request completed", 
               correlation_id=request.correlation_id,
               metadata={
                   "status_code": response.status_code,
                   "duration_ms": duration,
                   "response_size": len(response.get_data())
               })
    
    # Add correlation ID to response headers
    response.headers['X-Correlation-ID'] = request.correlation_id
    return response

@app.route('/api/search')
def search():
    """Search endpoint with detailed logging"""
    query = request.args.get('q', '')
    
    logger.info("Search request", 
               correlation_id=request.correlation_id,
               metadata={
                   "query": query,
                   "query_length": len(query)
               })
    
    # Simulate search logic
    results = [{"id": 1, "title": "Result 1"}, {"id": 2, "title": "Result 2"}]
    
    logger.info("Search completed", 
               correlation_id=request.correlation_id,
               metadata={
                   "results_count": len(results),
                   "query": query
               })
    
    return jsonify({"results": results, "correlation_id": request.correlation_id})

if __name__ == '__main__':
    app.run(debug=True)
```

### Celery Task Integration

```python
from celery import Celery
from ucbl_logger.enhanced import EnhancedEKSLogger

# Initialize Celery
celery_app = Celery('tasks')

# Initialize logger for Celery tasks
logger = EnhancedEKSLogger(
    service_name="celery-worker",
    namespace="background-jobs",
    enable_tracing=True,
    enable_performance_monitoring=True
)

@celery_app.task(bind=True)
def process_document(self, document_id, document_path):
    """Process document with comprehensive logging"""
    
    correlation_id = logger.start_trace("document_processing")
    
    logger.info("Document processing task started", 
               correlation_id=correlation_id,
               metadata={
                   "task_id": self.request.id,
                   "document_id": document_id,
                   "document_path": document_path,
                   "worker_id": self.request.hostname
               })
    
    try:
        # Simulate document processing steps
        steps = ["download", "parse", "analyze", "index"]
        
        for step in steps:
            step_correlation_id = logger.start_trace(f"document_{step}", parent_id=correlation_id)
            
            logger.info(f"Starting {step} step", 
                       correlation_id=step_correlation_id,
                       metadata={"step": step, "document_id": document_id})
            
            # Simulate processing time
            import time
            time.sleep(1)
            
            logger.info(f"Completed {step} step", 
                       correlation_id=step_correlation_id,
                       metadata={"step": step, "duration_ms": 1000})
            
            logger.end_trace(step_correlation_id, success=True)
        
        logger.info("Document processing completed", 
                   correlation_id=correlation_id,
                   metadata={
                       "document_id": document_id,
                       "steps_completed": len(steps)
                   })
        
        logger.end_trace(correlation_id, success=True)
        return {"status": "success", "document_id": document_id}
        
    except Exception as e:
        logger.error("Document processing failed", 
                    correlation_id=correlation_id,
                    metadata={
                        "document_id": document_id,
                        "error": str(e)
                    })
        
        logger.end_trace(correlation_id, success=False, metadata={"error": str(e)})
        raise
```

## Advanced Configuration Examples

### Multi-Environment Configuration

```python
import os
from ucbl_logger.enhanced import EnhancedEKSLogger
from ucbl_logger.enhanced.config import (
    SamplingConfig, BufferConfig, CloudWatchConfig, 
    PerformanceThresholds, SecurityConfig
)

def create_environment_logger():
    """Create logger based on environment"""
    
    environment = os.getenv('ENVIRONMENT', 'development')
    service_name = os.getenv('SERVICE_NAME', 'my-service')
    namespace = os.getenv('NAMESPACE', 'default')
    
    if environment == 'production':
        return EnhancedEKSLogger(
            service_name=service_name,
            namespace=namespace,
            log_level='WARN',
            enable_sampling=True,
            sampling_config=SamplingConfig(
                default_rate=0.05,  # Very aggressive sampling
                preserve_errors=True,
                adaptive_enabled=True
            ),
            buffer_config=BufferConfig(
                max_size=50000,
                flush_interval=10,
                async_flush=True
            ),
            cloudwatch_config=CloudWatchConfig(
                batch_size=1000,
                enable_compression=True,
                cost_optimization=True
            ),
            performance_config=PerformanceThresholds(
                collection_interval=300,  # 5 minutes
                cpu_warning=70.0
            ),
            security_config=SecurityConfig(
                enable_data_redaction=True,
                audit_redactions=True
            )
        )
    
    elif environment == 'staging':
        return EnhancedEKSLogger(
            service_name=service_name,
            namespace=namespace,
            log_level='INFO',
            enable_sampling=True,
            sampling_config=SamplingConfig(
                default_rate=0.2,  # Moderate sampling
                preserve_errors=True
            ),
            buffer_config=BufferConfig(
                max_size=20000,
                flush_interval=5
            ),
            performance_config=PerformanceThresholds(
                collection_interval=60  # 1 minute
            )
        )
    
    else:  # development
        return EnhancedEKSLogger(
            service_name=service_name,
            namespace=namespace,
            log_level='DEBUG',
            enable_sampling=False,  # No sampling in dev
            enable_cloudwatch=False,  # Local logging only
            buffer_config=BufferConfig(
                max_size=5000,
                flush_interval=2
            ),
            performance_config=PerformanceThresholds(
                collection_interval=30  # 30 seconds
            )
        )

# Usage
logger = create_environment_logger()
```

### Custom Metrics Integration

```python
from ucbl_logger.enhanced import EnhancedEKSLogger
from prometheus_client import Counter, Histogram, Gauge

# Initialize logger with custom metrics
logger = EnhancedEKSLogger(
    service_name="metrics-demo",
    namespace="monitoring"
)

# Define custom Prometheus metrics
request_counter = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint'])
request_duration = Histogram('http_request_duration_seconds', 'HTTP request duration')
active_connections = Gauge('active_connections', 'Active connections')

def handle_request_with_metrics(method, endpoint):
    """Handle request with custom metrics and logging"""
    
    correlation_id = logger.start_trace("request_handling")
    
    # Increment request counter
    request_counter.labels(method=method, endpoint=endpoint).inc()
    
    # Start timing
    with request_duration.time():
        logger.info("Processing request", 
                   correlation_id=correlation_id,
                   metadata={
                       "method": method,
                       "endpoint": endpoint
                   })
        
        # Simulate request processing
        import time
        time.sleep(0.1)
        
        # Update active connections gauge
        active_connections.set(42)  # Simulated value
        
        logger.info("Request completed", 
                   correlation_id=correlation_id,
                   metadata={
                       "method": method,
                       "endpoint": endpoint,
                       "active_connections": 42
                   })
    
    logger.end_trace(correlation_id, success=True)

# Usage
handle_request_with_metrics("GET", "/api/users")
handle_request_with_metrics("POST", "/api/orders")
```

## Performance Optimization Examples

### Memory-Optimized Configuration

```python
from ucbl_logger.enhanced import EnhancedEKSLogger
from ucbl_logger.enhanced.config import BufferConfig, SamplingConfig

# Configuration for memory-constrained environments
logger = EnhancedEKSLogger(
    service_name="memory-optimized-service",
    namespace="resource-constrained",
    enable_sampling=True,
    sampling_config=SamplingConfig(
        default_rate=0.01,  # Very aggressive sampling
        volume_threshold=100,  # Low threshold
        preserve_errors=True
    ),
    buffer_config=BufferConfig(
        max_size=1000,  # Small buffer
        flush_interval=1,  # Frequent flushes
        memory_threshold=0.7,  # Flush at 70% memory usage
        enable_compression=True
    ),
    enable_performance_monitoring=False,  # Disable to save memory
    enable_cloudwatch=True
)

# Monitor memory usage
def memory_aware_logging():
    """Demonstrate memory-aware logging"""
    
    import psutil
    
    for i in range(1000):
        # Check memory usage
        memory_percent = psutil.virtual_memory().percent
        
        if memory_percent > 80:
            # Reduce logging when memory is high
            if i % 100 == 0:  # Only log every 100th message
                logger.warning("High memory usage, reducing log frequency", 
                             metadata={"memory_percent": memory_percent})
        else:
            logger.debug(f"Processing item {i}", 
                        metadata={"item_id": i, "memory_percent": memory_percent})

memory_aware_logging()
```

### High-Throughput Configuration

```python
from ucbl_logger.enhanced import EnhancedEKSLogger
from ucbl_logger.enhanced.config import BufferConfig, CloudWatchConfig

# Configuration for high-throughput scenarios
logger = EnhancedEKSLogger(
    service_name="high-throughput-service",
    namespace="performance",
    buffer_config=BufferConfig(
        max_size=100000,  # Very large buffer
        flush_interval=30,  # Less frequent flushes
        async_flush=True,  # Non-blocking
        batch_processing=True,
        worker_threads=4  # Multiple workers
    ),
    cloudwatch_config=CloudWatchConfig(
        batch_size=2000,  # Large batches
        parallel_streams=5,  # Multiple streams
        enable_compression=True,
        compression_level=1  # Fast compression
    ),
    enable_sampling=True,
    sampling_config=SamplingConfig(
        default_rate=0.1,
        adaptive_enabled=True,
        performance_aware=True  # Adjust based on system load
    )
)

def high_throughput_processing():
    """Simulate high-throughput processing"""
    
    import threading
    import time
    
    def worker(worker_id):
        """Worker thread for processing"""
        for i in range(1000):
            logger.info(f"Worker {worker_id} processing item {i}", 
                       metadata={
                           "worker_id": worker_id,
                           "item_id": i,
                           "thread_name": threading.current_thread().name
                       })
            
            # Simulate very fast processing
            time.sleep(0.001)
    
    # Start multiple worker threads
    threads = []
    for worker_id in range(10):
        thread = threading.Thread(target=worker, args=(worker_id,))
        threads.append(thread)
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    print("High-throughput processing completed")

high_throughput_processing()
```

This comprehensive examples document demonstrates real-world usage scenarios for the Enhanced UCBLLogger, showing how to configure and use it effectively in different EKS environments and use cases. Each example includes detailed explanations and best practices for optimal performance and cost management.

## Related Files

- **Core Examples**: 
  - [`examples/enhanced_eks_logger_example.py`](examples/enhanced_eks_logger_example.py) - Complete enhanced logger demonstration
  - [`examples/cloudwatch_integration_example.py`](examples/cloudwatch_integration_example.py) - CloudWatch integration examples
  - [`examples/sampling_engine_example.py`](examples/sampling_engine_example.py) - Intelligent sampling demonstrations
  - [`examples/performance_monitoring_example.py`](examples/performance_monitoring_example.py) - Performance monitoring examples
  - [`examples/kubernetes_metadata_example.py`](examples/kubernetes_metadata_example.py) - Kubernetes metadata collection examples

- **Configuration**: 
  - [`docs/configuration-guide.md`](docs/configuration-guide.md) - Comprehensive configuration guide
  - [`deployment/kubernetes/`](deployment/kubernetes/) - Kubernetes deployment examples
  - [`deployment/monitoring/`](deployment/monitoring/) - Monitoring configuration examples

- **Documentation**: 
  - [`docs/deployment-best-practices.md`](docs/deployment-best-practices.md) - Production deployment guide
  - [`docs/troubleshooting-guide.md`](docs/troubleshooting-guide.md) - Troubleshooting procedures