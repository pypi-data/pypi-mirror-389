"""
FastAPI + NiceGUI integration example with UCBLLogger
Optimized for container execution
"""

import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from nicegui import ui, app
import uvicorn
import os
import sys

# Add the ucbl_logger to path for import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from ucbl_logger.eks_logger import EKSLogger

# Global logger instance - EKS optimized
logger = EKSLogger(
    service_name=os.getenv('SERVICE_NAME', 'graphrag-toolkit'),
    namespace=os.getenv('NAMESPACE', 'default')
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan events"""
    logger.log_task_start("FastAPI Application", "System")
    logger.info("FastAPI application starting up")
    yield
    logger.info("FastAPI application shutting down")
    logger.log_task_stop("FastAPI Application")

# Create FastAPI app
fastapi_app = FastAPI(
    title="GraphRAG Toolkit with UCBLLogger",
    description="FastAPI + NiceGUI application with structured logging",
    version="1.0.0",
    lifespan=lifespan
)

@fastapi_app.get("/health")
async def health_check():
    """Health check endpoint"""
    logger.info("Health check requested")
    return {"status": "healthy", "service": "graphrag-toolkit"}

@fastapi_app.post("/api/process")
async def process_data(data: dict):
    """Example API endpoint with logging"""
    task_name = f"Process-{data.get('id', 'unknown')}"
    logger.log_task_start(task_name, "User")
    
    try:
        # Simulate processing
        logger.info(f"Processing data: {data}")
        result = {"processed": True, "data": data}
        logger.info(f"Processing completed successfully")
        return result
    except Exception as e:
        logger.error(f"Processing failed: {str(e)}")
        logger.log_risk(f"Processing error for data {data}", critical=False)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        logger.log_task_stop(task_name)

# NiceGUI interface
@ui.page('/')
def main_page():
    """Main NiceGUI page"""
    logger.log_task_start("UI Page Load", "User")
    
    with ui.column().classes('w-full max-w-2xl mx-auto p-4'):
        ui.label('GraphRAG Toolkit Dashboard').classes('text-2xl font-bold mb-4')
        
        with ui.card().classes('w-full p-4'):
            ui.label('System Status').classes('text-lg font-semibold mb-2')
            status_label = ui.label('System: Online').classes('text-green-600')
            
            async def check_status():
                logger.info("Status check initiated from UI")
                status_label.text = 'System: Checking...'
                await asyncio.sleep(1)  # Simulate check
                status_label.text = 'System: Online'
                logger.info("Status check completed")
            
            ui.button('Check Status', on_click=check_status).classes('mt-2')
        
        with ui.card().classes('w-full p-4 mt-4'):
            ui.label('Log Test').classes('text-lg font-semibold mb-2')
            
            def test_logging():
                logger.log_task_start("UI Log Test", "User")
                logger.info("Test log from NiceGUI interface")
                logger.log_risk("Test risk message", minor=True)
                logger.log_anomaly("Test anomaly detection")
                logger.log_task_stop("UI Log Test")
                ui.notify('Logging test completed - check console')
            
            ui.button('Test Logging', on_click=test_logging).classes('mt-2')
    
    logger.log_task_stop("UI Page Load")

def run_server():
    """Run the combined FastAPI + NiceGUI server"""
    logger.log_task_start("Server Startup", "System")
    
    # Configure for container execution
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', '8080'))
    
    logger.info(f"Starting server on {host}:{port}")
    
    # Configure NiceGUI for container
    ui.run_with(
        fastapi_app,
        host=host,
        port=port,
        title='GraphRAG Toolkit',
        favicon='🤖',
        show=False,  # Don't open browser in container
        reload=False  # Disable reload in production
    )

if __name__ == '__main__':
    run_server()