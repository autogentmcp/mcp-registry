import asyncio
import logging
from contextlib import asynccontextmanager
from prisma import Prisma

# Configure logging
logger = logging.getLogger(__name__)

# Create a Prisma client
prisma = Prisma()

# Initialize the Prisma client
async def init_prisma():
    await prisma.connect()
    
# Close the Prisma client
async def close_prisma():
    await prisma.disconnect()

# Context manager for using Prisma in FastAPI endpoints
@asynccontextmanager
async def get_db():
    try:
        yield prisma
    except Exception as e:
        logger.error(f"Database error: {e}")
        raise

# Alternative context manager that handles connection for each request if needed
@asynccontextmanager
async def get_prisma():
    client = Prisma()
    try:
        await client.connect()
        yield client
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        raise
    finally:
        await client.disconnect()

# Initialize Prisma on startup
async def init_db():
    try:
        await init_prisma()
        logger.info("Prisma client connected successfully")
    except Exception as e:
        logger.error(f"Error connecting to database: {e}")
        raise
