"""
Minimal FastAPI app with health check for EKS debugging
"""

import os
import sys
from fastapi import FastAPI
import uvicorn

# Add logger path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from ucbl_logger.eks_logger import EKSLogger

# Create minimal app
app = FastAPI()
logger = EKSLogger()

@app.get("/")
async def root():
    logger.info("Root endpoint accessed")
    return {"status": "ok", "service": "data-plane-core"}

@app.get("/health")
async def health():
    logger.info("Health check accessed")
    return {"status": "healthy"}

@app.get("/readiness")
async def readiness():
    logger.info("Readiness check accessed")
    return {"status": "ready"}

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    logger.info(f"Starting server on port {port}")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )