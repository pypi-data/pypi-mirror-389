import boto3
import os
from datetime import datetime, timezone
from .security import SecurityValidator, CredentialProtector, secure_error_message
from .checks.version import VersionCheck
from .checks.iam import IAMCheck
from .checks.instances import InstancesCheck
from .checks.windows import WindowsCheck
from .checks.ssh import SSHCheck
from .checks.amis import AMIsCheck
from .checks.userdata import UserDataCheck
from .checks.addons import AddonsCheck
from .checks.autoscaling import AutoscalingCheck
from .checks.identity import IdentityCheck
from .checks.loadbalancers import LoadBalancersCheck

class EKSAutoModeCLIChecker:
    def __init__(self, cluster_name, region=None, profile=None):
        # Enhanced input validation
        self.cluster_name = SecurityValidator.validate_cluster_name(cluster_name)
        region = SecurityValidator.validate_region(region)
        profile = SecurityValidator.validate_profile(profile)
        
        # Initialize AWS session with enhanced security
        try:
            # Use profile from parameter, AWS_PROFILE env var, or default
            session_kwargs = {}
            if profile:
                session_kwargs['profile_name'] = profile
            elif os.environ.get('AWS_PROFILE'):
                # Validate environment profile
                env_profile = SecurityValidator.validate_profile(os.environ['AWS_PROFILE'])
                if env_profile:
                    session_kwargs['profile_name'] = env_profile
            
            self.session = boto3.Session(**session_kwargs)
            self.region = region or self.session.region_name or 'us-east-1'
            
            # Validate credentials before proceeding
            credential_info = CredentialProtector.validate_credentials(self.session)
            
            self.eks_client = self.session.client('eks', region_name=self.region)
            self.ec2_client = self.session.client('ec2', region_name=self.region)
            self.iam_client = self.session.client('iam')
        except Exception as e:
            raise ValueError(f"Failed to initialize AWS clients: {secure_error_message(e)}")
        
        # Validate cluster exists
        try:
            self.cluster_info = self.eks_client.describe_cluster(name=self.cluster_name)['cluster']
        except self.eks_client.exceptions.ResourceNotFoundException:
            raise ValueError(f"Cluster '{self.cluster_name}' not found in region '{self.region}'")
        except Exception as e:
            raise ValueError(f"Failed to access cluster: {secure_error_message(e)}")
        
        # Initialize checks
        self.available_checks = {
            'version': VersionCheck(self),
            'iam': IAMCheck(self),
            'instances': InstancesCheck(self),
            'windows': WindowsCheck(self),
            'ssh': SSHCheck(self),
            'amis': AMIsCheck(self),
            'userdata': UserDataCheck(self),
            'addons': AddonsCheck(self),
            'autoscaling': AutoscalingCheck(self),
            'identity': IdentityCheck(self),
            'loadbalancers': LoadBalancersCheck(self)
        }
    
    def run_checks(self, check_list=None):
        """Run specified checks or all checks"""
        
        # Determine which checks to run
        if check_list:
            checks_to_run = {}
            for check_name in check_list:
                if check_name in self.available_checks:
                    checks_to_run[check_name] = self.available_checks[check_name]
                else:
                    raise ValueError(f"Unknown check: {check_name}")
        else:
            checks_to_run = self.available_checks
        
        # Run checks
        results = {
            'cluster': self.cluster_name,
            'region': self.region,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'checks': {}
        }
        
        for check_name, check_instance in checks_to_run.items():
            try:
                result = check_instance.run()
                if not isinstance(result, dict) or 'status' not in result:
                    raise ValueError(f"Invalid result format from {check_name} check")
                results['checks'][check_name] = result
            except Exception as e:
                results['checks'][check_name] = {
                    'status': 'ERROR',
                    'details': f'Check execution failed: {secure_error_message(e)}'
                }
        
        # Determine overall status
        results['overall_status'] = self._calculate_overall_status(results['checks'])
        
        return results
    
    def _calculate_overall_status(self, checks):
        """Calculate overall readiness status"""
        if not checks:
            return 'ERROR'
        
        # If cluster already has Auto Mode enabled, it's ready
        if self.cluster_info.get('computeConfig', {}).get('enabled'):
            return 'READY'
        
        statuses = [check.get('status', 'ERROR') for check in checks.values()]
        
        # Only AMI check failures result in NOT_READY
        if 'amis' in checks and checks['amis'].get('status') == 'FAIL':
            return 'NOT_READY'
        elif 'ERROR' in statuses or 'FAIL' in statuses:
            return 'REQUIRES_CHANGES'
        elif 'WARN' in statuses:
            return 'REQUIRES_CHANGES'
        else:
            return 'READY'