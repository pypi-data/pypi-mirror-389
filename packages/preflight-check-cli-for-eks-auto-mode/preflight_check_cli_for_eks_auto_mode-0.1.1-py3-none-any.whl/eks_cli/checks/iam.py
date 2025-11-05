from .base import BaseCheck
from botocore.exceptions import ClientError

class IAMCheck(BaseCheck):
    """Check IAM roles and Auto Mode policies"""
    
    def _execute_check(self):
        cluster_role_arn = self.cluster_info.get('roleArn')
        if not cluster_role_arn:
            raise ValueError("Cluster role ARN not found")
        
        role_name = cluster_role_arn.split('/')[-1]
        
        # Required Auto Mode policies
        required_policies = [
            'arn:aws:iam::aws:policy/AmazonEKSClusterPolicy',
            'arn:aws:iam::aws:policy/AmazonEKSComputePolicy',
            'arn:aws:iam::aws:policy/AmazonEKSBlockStoragePolicy',
            'arn:aws:iam::aws:policy/AmazonEKSLoadBalancingPolicy',
            'arn:aws:iam::aws:policy/AmazonEKSNetworkingPolicy'
        ]
        
        # Get attached policies
        attached_policies = self.iam_client.list_attached_role_policies(RoleName=role_name)
        attached_arns = [p.get('PolicyArn', '') for p in attached_policies.get('AttachedPolicies', [])]
        
        # Check for missing policies
        missing_policies = [p for p in required_policies if p not in attached_arns]
        
        if not missing_policies:
            return self._create_result(
                'PASS',
                'All Auto Mode policies attached'
            )
        else:
            policy_names = [p.split('/')[-1] for p in missing_policies]
            return self._create_result(
                'WARN',
                f'Missing {len(missing_policies)} Auto Mode policies',
                [f'Attach missing policies: {", ".join(policy_names)}']
            )