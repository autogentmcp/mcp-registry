"""
MCP Registry Server Runner

This script launches the MCP Registry server using uvicorn.
"""
import uvicorn
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("run_server")

if __name__ == "__main__":
    logger.info("Starting MCP Registry server...")
    uvicorn.run(
        "src.mcp_registry.server:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        log_level="info"
    )
