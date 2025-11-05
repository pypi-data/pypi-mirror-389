from .base import BaseCheck
from botocore.exceptions import ClientError

class AMIsCheck(BaseCheck):
    """Check for custom AMI usage"""
    
    MANAGED_AMI_TYPES = {
        'AL2_x86_64', 'AL2_x86_64_GPU', 'AL2_ARM_64', 
        'AL2023_x86_64_STANDARD', 'AL2023_ARM_64_STANDARD', 
        'BOTTLEROCKET_ARM_64', 'BOTTLEROCKET_x86_64'
    }
    
    def _execute_check(self):
        custom_ami_resources = []
        
        # Check managed node groups for launch templates (which may have custom AMIs)
        node_groups = self.eks_client.list_nodegroups(clusterName=self.cluster_name)
        for ng_name in node_groups.get('nodegroups', []):
            try:
                ng_details = self.eks_client.describe_nodegroup(
                    clusterName=self.cluster_name,
                    nodegroupName=ng_name
                )['nodegroup']
                
                # Check if using launch template
                if ng_details.get('launchTemplate'):
                    lt_id = ng_details['launchTemplate']['id']
                    custom_ami_resources.append(f"Node group {ng_name}: uses launch template {lt_id}")
                
                # Check AMI type - if it's not a standard AWS managed type
                ami_type = ng_details.get('amiType', '')
                if ami_type and ami_type not in self.MANAGED_AMI_TYPES:
                    custom_ami_resources.append(f"Node group {ng_name}: custom AMI type {ami_type}")
            except ClientError:
                continue
        
        if custom_ami_resources:
            resource_summary = ', '.join(custom_ami_resources[:3])
            if len(custom_ami_resources) > 3:
                resource_summary += '...'
            
            return self._create_result(
                'FAIL',
                f'Found {len(custom_ami_resources)} custom AMI resources',
                [
                    'Custom AMIs not supported in Auto Mode',
                    'Switch to AWS managed AMIs',
                    f'Resources: {resource_summary}'
                ]
            )
        else:
            return self._create_result(
                'PASS',
                'Using AWS managed AMIs'
            )