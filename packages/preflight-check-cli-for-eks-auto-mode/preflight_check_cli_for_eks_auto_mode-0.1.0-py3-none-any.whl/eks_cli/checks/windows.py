from .base import BaseCheck
from botocore.exceptions import ClientError

class WindowsCheck(BaseCheck):
    """Check for Windows nodes"""
    
    def _execute_check(self):
        windows_resources = []
        
        # Check managed node groups for Windows AMI types
        node_groups = self.eks_client.list_nodegroups(clusterName=self.cluster_name)
        for ng_name in node_groups.get('nodegroups', []):
            try:
                ng_details = self.eks_client.describe_nodegroup(
                    clusterName=self.cluster_name,
                    nodegroupName=ng_name
                )['nodegroup']
                
                ami_type = ng_details.get('amiType', '')
                if 'WINDOWS' in ami_type.upper():
                    windows_resources.append(f"Node group: {ng_name} ({ami_type})")
            except ClientError:
                continue
        
        if windows_resources:
            return self._create_result(
                'FAIL',
                f'Found {len(windows_resources)} Windows resources',
                [
                    'Windows is not supported in Auto Mode',
                    'Remove Windows nodes before migration'
                ]
            )
        else:
            return self._create_result(
                'PASS',
                'No Windows nodes found'
            )