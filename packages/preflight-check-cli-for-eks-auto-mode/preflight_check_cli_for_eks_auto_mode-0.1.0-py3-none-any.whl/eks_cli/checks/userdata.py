from .base import BaseCheck
from botocore.exceptions import ClientError

class UserDataCheck(BaseCheck):
    """Check for user data configuration"""
    
    def _execute_check(self):
        user_data_resources = []
        
        # Check managed node groups for launch templates with user data
        node_groups = self.eks_client.list_nodegroups(clusterName=self.cluster_name)
        for ng_name in node_groups.get('nodegroups', []):
            try:
                ng_details = self.eks_client.describe_nodegroup(
                    clusterName=self.cluster_name,
                    nodegroupName=ng_name
                )['nodegroup']
                
                # If using launch template, check for user data
                launch_template = ng_details.get('launchTemplate')
                if launch_template:
                    lt_id = launch_template.get('id')
                    lt_version = launch_template.get('version', '$Latest')
                    
                    if lt_id and self._has_user_data(lt_id, lt_version):
                        user_data_resources.append(f"Node group {ng_name}: launch template {lt_id}")
            except ClientError:
                continue
        
        if user_data_resources:
            resource_summary = ', '.join(user_data_resources[:3])
            if len(user_data_resources) > 3:
                resource_summary += '...'
            
            return self._create_result(
                'FAIL',
                f'Found {len(user_data_resources)} user data resources',
                [
                    'User data not supported in Auto Mode',
                    'Remove custom user data configurations',
                    f'Resources: {resource_summary}'
                ]
            )
        else:
            return self._create_result(
                'PASS',
                'No user data found'
            )
    
    def _has_user_data(self, lt_id, lt_version):
        """Check if launch template has user data"""
        try:
            if not lt_id:
                return False
            
            lt_details = self.ec2_client.describe_launch_template_versions(
                LaunchTemplateId=lt_id,
                Versions=[lt_version]
            )
            
            for version in lt_details.get('LaunchTemplateVersions', []):
                if version.get('LaunchTemplateData', {}).get('UserData'):
                    return True
            return False
        except (ClientError, ValueError):
            # If we can't check the launch template, assume it might have user data
            return True