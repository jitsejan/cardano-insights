"""
Environment configuration for GitHub pipeline.
Manages environment variables and AWS secrets integration.
"""
import os
from typing import Optional


class GitHubSettings:
    """Configuration settings for GitHub data pipeline."""
    
    # API Configuration
    GITHUB_BASE_URL: str = os.getenv("GITHUB_BASE_URL", "https://api.github.com")
    @classmethod
    def get_github_token(cls) -> str:
        return os.getenv("GITHUB_TOKEN", "")
    
    # AWS Configuration  
    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")
    S3_BUCKET: str = os.getenv("S3_BUCKET", "")
    S3_PREFIX: str = os.getenv("S3_PREFIX", "bronze/github")
    
    # Runtime Configuration
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "dev")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Pipeline Configuration
    FRESHNESS_WINDOW_DAYS: int = int(os.getenv("FRESHNESS_WINDOW_DAYS", "7"))
    MAX_PRS_DEV: int = int(os.getenv("MAX_PRS_DEV", "50"))
    MAX_RELEASES_DEV: int = int(os.getenv("MAX_RELEASES_DEV", "10"))
    
    # Default repositories
    DEFAULT_REPOS = [
        "cardano-foundation/cardano-wallet",
        "input-output-hk/cardano-node",
        "input-output-hk/plutus",
        "Emurgo/cardano-serialization-lib",
    ]
    
    # EventBridge Configuration
    EVENTBRIDGE_BUS_NAME: str = os.getenv("EVENTBRIDGE_BUS_NAME", "default")
    
    # State Tracking Configuration
    DYNAMODB_STATE_TABLE: str = os.getenv("DYNAMODB_STATE_TABLE", "github-pipeline-state")
    
    @classmethod
    def validate(cls) -> None:
        """Validate required configuration."""
        if not cls.S3_BUCKET:
            raise ValueError("S3_BUCKET environment variable is required")
        
        if cls.ENVIRONMENT not in ["dev", "prod"]:
            raise ValueError("ENVIRONMENT must be 'dev' or 'prod'")
    
    @classmethod
    def get_repo_limits(cls) -> dict:
        """Get repository limits based on environment."""
        if cls.ENVIRONMENT == "dev":
            return {
                "max_prs": cls.MAX_PRS_DEV,
                "max_releases": cls.MAX_RELEASES_DEV
            }
        return {"max_prs": None, "max_releases": None}