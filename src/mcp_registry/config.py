import os
from typing import List
import logging
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    """
    Application configuration settings loaded from environment variables
    """
    # General settings
    APP_NAME: str = "MCP Registry"
    APP_DESCRIPTION: str = "A high-performance, LLM-friendly Model Context Protocol registry server"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Database settings
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/mcp_registry")
    
    # Security settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "super-secret-key-change-in-production")
    REGISTRY_ADMIN_KEY: str = os.getenv("REGISTRY_ADMIN_KEY", "admin-api-key-change-in-production")
    
    # Application settings
    DEFAULT_USER_ID: str = os.getenv("DEFAULT_USER_ID", "cl123456789")
    DEFAULT_APPLICATION_STATUS: str = "ACTIVE"
    DEFAULT_ENVIRONMENT_STATUS: str = "ACTIVE"
    DEFAULT_API_KEY_EXPIRY_DAYS: int = 365  # 1 year
    
    # CORS settings
    ALLOWED_ORIGINS: List[str] = os.getenv("ALLOWED_ORIGINS", "*").split(",")
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Create settings instance
settings = Settings()

# Configure logging
logging_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
logging.basicConfig(
    level=logging_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
