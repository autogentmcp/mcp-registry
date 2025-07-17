"""
Model Context Protocol Registry
A high-performance, LLM-friendly registry server for managing applications and endpoints.
"""

import asyncio

# Expose important items at package level
# Import server module only when explicitly needed
__all__ = ['main']

def main():
    """Main entry point for the package."""
    # This function is called when the package is run as a module
    from .server import app
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)