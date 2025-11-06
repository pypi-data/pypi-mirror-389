"""
S3 storage helper for managing user data in AWS S3.
Used for Vercel deployment where local file storage doesn't persist.
"""
import os
import json
import boto3
from botocore.config import Config
from typing import Optional
from pathlib import Path


class S3Storage:
    """Helper class for storing and retrieving data from S3."""
    
    def __init__(self):
        # Get credentials from environment variables
        self.bucket_name = os.getenv('S3_USER_DATA_BUCKET', 'pingg-me.shop')
        self.folder = os.getenv('S3_USER_DATA_FOLDER', 'base-ng-folder')
        self.region = os.getenv('S3_REGION', 'ap-south-1')
        
        try:
            # Configure with timeouts to prevent hanging
            config = Config(
                connect_timeout=3,
                read_timeout=5,
                retries={'max_attempts': 2}
            )
            
            # Initialize S3 client
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=os.getenv('S3_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('S3_SECRET_ACCESS_KEY'),
                region_name=self.region,
                config=config
            )
            
            print(f"📦 S3 Storage initialized: s3://{self.bucket_name}/{self.folder}/")
        except Exception as e:
            print(f"⚠️  Warning: Failed to initialize S3 client: {e}")
            print(f"   S3_ACCESS_KEY_ID set: {bool(os.getenv('S3_ACCESS_KEY_ID'))}")
            print(f"   S3_SECRET_ACCESS_KEY set: {bool(os.getenv('S3_SECRET_ACCESS_KEY'))}")
            raise
    
    def get_key(self, filename: str) -> str:
        """Get the full S3 key for a filename."""
        return f"{self.folder}/{filename}"
    
    def load_json(self, filename: str) -> Optional[dict]:
        """Load JSON data from S3."""
        key = self.get_key(filename)
        
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=key)
            data = json.loads(response['Body'].read().decode('utf-8'))
            print(f"✅ Loaded {filename} from S3: {key}")
            return data
        except self.s3_client.exceptions.NoSuchKey:
            print(f"📄 {filename} not found in S3, starting fresh")
            return None
        except Exception as e:
            print(f"❌ Error loading {filename} from S3: {e}")
            return None
    
    def save_json(self, filename: str, data: dict) -> bool:
        """Save JSON data to S3."""
        key = self.get_key(filename)
        
        try:
            json_data = json.dumps(data, indent=2)
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=json_data.encode('utf-8'),
                ContentType='application/json'
            )
            print(f"✅ Saved {filename} to S3: {key}")
            return True
        except Exception as e:
            print(f"❌ Error saving {filename} to S3: {e}")
            return False
    
    def delete_file(self, filename: str) -> bool:
        """Delete a file from S3."""
        key = self.get_key(filename)
        
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=key)
            print(f"🗑️  Deleted {filename} from S3: {key}")
            return True
        except Exception as e:
            print(f"❌ Error deleting {filename} from S3: {e}")
            return False
    
    def list_files(self) -> list:
        """List all files in the S3 folder."""
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=f"{self.folder}/"
            )
            
            if 'Contents' not in response:
                return []
            
            files = [obj['Key'].replace(f"{self.folder}/", "") 
                    for obj in response['Contents']
                    if not obj['Key'].endswith('/')]
            return files
        except Exception as e:
            print(f"❌ Error listing files from S3: {e}")
            return []


def is_serverless_environment() -> bool:
    """
    Detect if running in a serverless environment (Vercel, AWS Lambda, etc.).
    Returns True if we should use S3 storage instead of local files.
    """
    # Check for Vercel environment
    if os.getenv('VERCEL'):
        return True
    
    # Check for AWS Lambda environment
    if os.getenv('AWS_LAMBDA_FUNCTION_NAME'):
        return True
    
    # Check for explicit override
    if os.getenv('USE_S3_STORAGE', '').lower() in ('true', '1', 'yes'):
        return True
    
    # Default to local storage for development
    return False
