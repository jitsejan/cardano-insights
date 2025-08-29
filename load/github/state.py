"""
DynamoDB state tracking for GitHub pipeline production environment.
"""
import boto3
import os
from datetime import datetime, timezone
from typing import Optional, Tuple
from botocore.exceptions import ClientError


class DynamoDBStateTracker:
    """Manages pipeline state using DynamoDB for production environments."""
    
    def __init__(self):
        """Initialize DynamoDB client and table configuration."""
        from .settings import GitHubSettings
        
        self.dynamodb = boto3.resource('dynamodb', region_name=GitHubSettings.AWS_REGION)
        self.table_name = GitHubSettings.DYNAMODB_STATE_TABLE
        self.table = self.dynamodb.Table(self.table_name)
        
    def check_data_freshness(
        self, 
        table_name: str, 
        repo_name: Optional[str] = None,
        freshness_window_days: int = 7
    ) -> Tuple[bool, Optional[datetime]]:
        """
        Check if data is fresh based on DynamoDB state tracking.
        
        Args:
            table_name: Type of data (repositories, pull_requests, releases)
            repo_name: Repository name (owner/repo format)
            freshness_window_days: Number of days to consider fresh
            
        Returns:
            Tuple of (is_fresh, last_updated_datetime)
        """
        try:
            # Create composite key for the state record
            partition_key = f"{table_name}#{repo_name}" if repo_name else table_name
            
            response = self.table.get_item(
                Key={'pipeline_state_id': partition_key}
            )
            
            if 'Item' not in response:
                print(f"No state found for {partition_key} - full refresh needed")
                return False, None
            
            item = response['Item']
            last_updated_str = item.get('last_updated')
            
            if not last_updated_str:
                print(f"No last_updated timestamp for {partition_key} - full refresh needed")
                return False, None
            
            # Parse the ISO timestamp
            last_updated = datetime.fromisoformat(last_updated_str.replace('Z', '+00:00'))
            
            # Check if data is within freshness window
            now = datetime.now(timezone.utc)
            days_since_update = (now - last_updated).total_seconds() / (24 * 3600)
            
            is_fresh = days_since_update <= freshness_window_days
            
            print(f"State for {partition_key}: last_updated={last_updated_str}, "
                  f"days_ago={days_since_update:.1f}, fresh={is_fresh}")
            
            return is_fresh, last_updated
            
        except ClientError as e:
            print(f"DynamoDB error checking freshness for {partition_key}: {e}")
            return False, None
        except Exception as e:
            print(f"Error checking freshness for {partition_key}: {e}")
            return False, None
    
    def update_state(
        self, 
        table_name: str, 
        repo_name: Optional[str] = None,
        additional_metadata: Optional[dict] = None
    ) -> None:
        """
        Update the state tracking record in DynamoDB.
        
        Args:
            table_name: Type of data (repositories, pull_requests, releases)
            repo_name: Repository name (owner/repo format)
            additional_metadata: Optional metadata to store with state
        """
        try:
            partition_key = f"{table_name}#{repo_name}" if repo_name else table_name
            now = datetime.now(timezone.utc).isoformat()
            
            item = {
                'pipeline_state_id': partition_key,
                'last_updated': now,
                'table_name': table_name,
                'environment': os.getenv('ENVIRONMENT', 'prod')
            }
            
            if repo_name:
                item['repository_name'] = repo_name
                
            if additional_metadata:
                item.update(additional_metadata)
            
            self.table.put_item(Item=item)
            print(f"Updated state for {partition_key} at {now}")
            
        except ClientError as e:
            print(f"DynamoDB error updating state for {partition_key}: {e}")
        except Exception as e:
            print(f"Error updating state for {partition_key}: {e}")


def get_state_tracker() -> Optional[DynamoDBStateTracker]:
    """
    Get appropriate state tracker based on environment.
    Returns None for non-prod environments (they use DuckDB).
    """
    from .settings import GitHubSettings
    
    if GitHubSettings.ENVIRONMENT == 'prod':
        try:
            return DynamoDBStateTracker()
        except Exception as e:
            print(f"Failed to initialize DynamoDB state tracker: {e}")
            return None
    
    return None