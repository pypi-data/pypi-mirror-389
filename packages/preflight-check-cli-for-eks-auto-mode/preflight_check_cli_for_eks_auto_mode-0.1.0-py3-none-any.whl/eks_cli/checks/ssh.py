from .base import BaseCheck
from botocore.exceptions import ClientError

class SSHCheck(BaseCheck):
    """Check for SSH/SSM access configuration"""
    
    def _execute_check(self):
        access_issues = []
        
        # Check managed node groups for SSH keys and SSM
        node_groups = self.eks_client.list_nodegroups(clusterName=self.cluster_name)
        
        for ng_name in node_groups.get('nodegroups', []):
            try:
                ng_details = self.eks_client.describe_nodegroup(
                    clusterName=self.cluster_name,
                    nodegroupName=ng_name
                )['nodegroup']
                
                # Check SSH key
                if ng_details.get('remoteAccess', {}).get('ec2SshKey'):
                    ssh_key = ng_details['remoteAccess']['ec2SshKey']
                    access_issues.append(f"SSH key in {ng_name}: {ssh_key}")
                
                # Check node role for SSM
                node_role = ng_details.get('nodeRole')
                if node_role and self._role_has_ssm_policy(node_role):
                    access_issues.append(f"SSM access in {ng_name}")
                
            except ClientError:
                continue
        
        if access_issues:
            return self._create_result(
                'FAIL',
                f'Found {len(access_issues)} access configurations',
                [
                    'SSH/SSM access not compatible with Auto Mode',
                    'Remove direct node access configurations'
                ]
            )
        else:
            return self._create_result(
                'PASS',
                'No SSH/SSM access found'
            )
    

    
    def _role_has_ssm_policy(self, role_arn):
        """Check if role has SSM policies attached"""
        try:
            if not role_arn or '/' not in role_arn:
                return False
            
            role_name = role_arn.split('/')[-1]
            policies = self.iam_client.list_attached_role_policies(RoleName=role_name)
            ssm_policies = ['AmazonSSMManagedInstanceCore', 'AmazonEC2RoleforSSM']
            
            for policy in policies.get('AttachedPolicies', []):
                if any(ssm_policy in policy.get('PolicyName', '') for ssm_policy in ssm_policies):
                    return True
            return False
        except (ClientError, ValueError, IndexError):
            return False