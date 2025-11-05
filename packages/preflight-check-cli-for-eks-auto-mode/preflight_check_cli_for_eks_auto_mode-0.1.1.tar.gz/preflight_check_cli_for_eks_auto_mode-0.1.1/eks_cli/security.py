"""Security utilities for input validation and credential protection"""

import re
import os
import logging
from typing import Optional, Dict, Any

# Configure secure logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

class SecurityValidator:
    """Enhanced security validation for CLI inputs and AWS operations"""
    
    # AWS resource naming constraints
    CLUSTER_NAME_PATTERN = re.compile(r'^[a-zA-Z0-9][a-zA-Z0-9_-]{0,99}$')
    REGION_PATTERN = re.compile(r'^[a-z0-9-]{2,25}$')
    PROFILE_PATTERN = re.compile(r'^[a-zA-Z0-9_.-]{1,64}$')
    
    # Maximum input lengths
    MAX_CLUSTER_NAME_LENGTH = 100
    MAX_REGION_LENGTH = 25
    MAX_PROFILE_LENGTH = 64
    
    @classmethod
    def validate_cluster_name(cls, cluster_name: str) -> str:
        """Validate and sanitize cluster name"""
        if not cluster_name or not isinstance(cluster_name, str):
            raise ValueError("Cluster name must be a non-empty string")
        
        cluster_name = cluster_name.strip()
        
        if len(cluster_name) > cls.MAX_CLUSTER_NAME_LENGTH:
            raise ValueError(f"Cluster name exceeds maximum length of {cls.MAX_CLUSTER_NAME_LENGTH}")
        
        if not cls.CLUSTER_NAME_PATTERN.match(cluster_name):
            raise ValueError("Invalid cluster name format. Must contain only alphanumeric characters, hyphens, and underscores")
        
        return cluster_name
    
    @classmethod
    def validate_region(cls, region: Optional[str]) -> Optional[str]:
        """Validate AWS region format"""
        if not region:
            return None
        
        if not isinstance(region, str):
            raise ValueError("Region must be a string")
        
        region = region.strip()
        
        if len(region) > cls.MAX_REGION_LENGTH:
            raise ValueError(f"Region exceeds maximum length of {cls.MAX_REGION_LENGTH}")
        
        if not cls.REGION_PATTERN.match(region):
            raise ValueError("Invalid AWS region format")
        
        return region
    
    @classmethod
    def validate_profile(cls, profile: Optional[str]) -> Optional[str]:
        """Validate AWS profile name"""
        if not profile:
            return None
        
        if not isinstance(profile, str):
            raise ValueError("Profile must be a string")
        
        profile = profile.strip()
        
        if len(profile) > cls.MAX_PROFILE_LENGTH:
            raise ValueError(f"Profile name exceeds maximum length of {cls.MAX_PROFILE_LENGTH}")
        
        if not cls.PROFILE_PATTERN.match(profile):
            raise ValueError("Invalid AWS profile name format")
        
        return profile
    
    @classmethod
    def validate_checks_list(cls, checks: Optional[str]) -> Optional[list]:
        """Validate and sanitize checks parameter"""
        if not checks:
            return None
        
        if not isinstance(checks, str):
            raise ValueError("Checks must be a string")
        
        # Split and validate each check name
        check_list = []
        for check in checks.split(','):
            check = check.strip()
            if not re.match(r'^[a-zA-Z_]{1,20}$', check):
                raise ValueError(f"Invalid check name format: {check}")
            check_list.append(check)
        
        if len(check_list) > 20:  # Reasonable limit
            raise ValueError("Too many checks specified")
        
        return check_list

class CredentialProtector:
    """Protect AWS credentials from exposure"""
    
    SENSITIVE_ENV_VARS = {
        'AWS_ACCESS_KEY_ID',
        'AWS_SECRET_ACCESS_KEY', 
        'AWS_SESSION_TOKEN',
        'AWS_SECURITY_TOKEN'
    }
    
    @classmethod
    def validate_credentials(cls, session) -> Dict[str, Any]:
        """Validate AWS credentials and return safe metadata"""
        try:
            credentials = session.get_credentials()
            if not credentials:
                raise ValueError("No AWS credentials found")
            
            # Get caller identity safely
            sts_client = session.client('sts')
            identity = sts_client.get_caller_identity()
            
            return {
                'account_id': identity.get('Account'),
                'user_id': identity.get('UserId'),
                'arn': identity.get('Arn'),
                'credential_type': 'temporary' if credentials.token else 'long-term'
            }
        except Exception as e:
            raise ValueError(f"Credential validation failed: {str(e)}")
    
    @classmethod
    def sanitize_environment(cls) -> Dict[str, str]:
        """Remove sensitive environment variables from logs"""
        env_copy = os.environ.copy()
        for var in cls.SENSITIVE_ENV_VARS:
            if var in env_copy:
                env_copy[var] = '[REDACTED]'
        return env_copy
    
    @classmethod
    def validate_account_access(cls, session, expected_account: Optional[str] = None) -> bool:
        """Validate account access and prevent cross-account issues"""
        try:
            identity = cls.validate_credentials(session)
            current_account = identity['account_id']
            
            if expected_account and current_account != expected_account:
                logger.warning(f"Account mismatch: expected {expected_account}, got {current_account}")
                return False
            
            return True
        except Exception as e:
            logger.error(f"Account validation failed: {e}")
            return False

def secure_error_message(error: Exception) -> str:
    """Sanitize error messages to prevent information disclosure"""
    error_str = str(error)
    
    # Remove potential sensitive information
    sensitive_patterns = [
        r'aws_access_key_id=\S+',
        r'aws_secret_access_key=\S+',
        r'aws_session_token=\S+',
        r'arn:aws:iam::\d+:',
        r'AKIA[0-9A-Z]{16}',
        r'[A-Za-z0-9/+=]{40}'
    ]
    
    for pattern in sensitive_patterns:
        error_str = re.sub(pattern, '[REDACTED]', error_str, flags=re.IGNORECASE)
    
    return error_str