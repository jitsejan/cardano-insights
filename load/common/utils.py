"""
Shared utilities for dlt pipelines running on Fargate.
"""
import os
import json
import boto3
import structlog
from datetime import datetime
from typing import Dict, Any


def setup_logging() -> None:
    """Configure structured logging for container environment."""
    log_level = os.getenv("LOG_LEVEL", "INFO")
    
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def emit_completion_event(
    source: str, 
    detail_type: str, 
    detail: Dict[str, Any]
) -> None:
    """
    Emit EventBridge event to trigger downstream processing.
    
    Args:
        source: Event source (e.g., "techint.lido")
        detail_type: Event type (e.g., "ingestion.complete") 
        detail: Event detail payload
    """
    try:
        eventbridge = boto3.client('events')
        bus_name = os.getenv("EVENTBRIDGE_BUS_NAME", "default")
        
        response = eventbridge.put_events(
            Entries=[
                {
                    'Source': source,
                    'DetailType': detail_type,
                    'Detail': json.dumps(detail),
                    'EventBusName': bus_name
                }
            ]
        )
        
        print(f"✅ Event emitted to {bus_name}: {source}/{detail_type}")
        print(f"   Detail: {detail}")
        
        if response.get('FailedEntryCount', 0) > 0:
            print(f"⚠️ Some events failed: {response}")
            
    except Exception as e:
        print(f"❌ Failed to emit event: {e}")
        # Don't fail the pipeline if event emission fails
        pass


def get_s3_credentials() -> Dict[str, str]:
    """Get S3 credentials for dlt filesystem destination."""
    return {
        "bucket_url": f"s3://{os.getenv('S3_BUCKET')}/{os.getenv('S3_PREFIX', 'bronze/lido')}",
        "aws_access_key_id": os.getenv("AWS_ACCESS_KEY_ID"),
        "aws_secret_access_key": os.getenv("AWS_SECRET_ACCESS_KEY"), 
        "aws_session_token": os.getenv("AWS_SESSION_TOKEN"),  # For role-based auth
        "region_name": os.getenv("AWS_REGION", "us-east-1")
    }