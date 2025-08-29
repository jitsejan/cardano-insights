"""
Environment configuration for Lido pipeline.
Manages environment variables and AWS secrets integration.
"""
import os
from typing import Optional


class LidoSettings:
    """Configuration settings for Lido Catalyst pipeline."""
    
    # API Configuration
    LIDO_BASE_URL: str = os.getenv("LIDO_BASE_URL", "https://www.lidonation.com/api/catalyst-explorer")
    
    # AWS Configuration  
    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")
    S3_BUCKET: str = os.getenv("S3_BUCKET", "")
    S3_PREFIX: str = os.getenv("S3_PREFIX", "bronze/lido")
    
    # Runtime Configuration
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "dev")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Pipeline Configuration
    MAX_PAGES_DEV: int = int(os.getenv("MAX_PAGES_DEV", "5"))
    MAX_PAGES_PROD: Optional[int] = None  # No limit for prod
    
    # EventBridge Configuration
    EVENTBRIDGE_BUS_NAME: str = os.getenv("EVENTBRIDGE_BUS_NAME", "default")
    
    @classmethod
    def validate(cls) -> None:
        """Validate required configuration."""
        if not cls.S3_BUCKET:
            raise ValueError("S3_BUCKET environment variable is required")
        
        if cls.ENVIRONMENT not in ["dev", "prod"]:
            raise ValueError("ENVIRONMENT must be 'dev' or 'prod'")
    
    @classmethod
    def get_max_pages(cls) -> Optional[int]:
        """Get max pages based on environment."""
        return cls.MAX_PAGES_DEV if cls.ENVIRONMENT == "dev" else cls.MAX_PAGES_PROD