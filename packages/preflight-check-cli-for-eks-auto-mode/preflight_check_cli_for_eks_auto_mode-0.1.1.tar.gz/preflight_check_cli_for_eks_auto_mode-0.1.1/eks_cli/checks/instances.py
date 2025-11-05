from .base import BaseCheck
from botocore.exceptions import ClientError
import re

class InstancesCheck(BaseCheck):
    """Check for incompatible instance types"""
    
    # Compile regex pattern once for better performance
    _SMALL_INSTANCE_PATTERN = re.compile(r'\.(nano|micro|small)$')
    
    def _execute_check(self):
        small_instances = []
        
        # Check managed node groups only
        node_groups = self.eks_client.list_nodegroups(clusterName=self.cluster_name)
        for ng_name in node_groups.get('nodegroups', []):
            try:
                ng_details = self.eks_client.describe_nodegroup(
                    clusterName=self.cluster_name,
                    nodegroupName=ng_name
                )['nodegroup']
                
                for instance_type in ng_details.get('instanceTypes', []):
                    if self._SMALL_INSTANCE_PATTERN.search(instance_type):
                        small_instances.append(f"{ng_name}: {instance_type}")
            except ClientError:
                continue
        
        if small_instances:
            return self._create_result(
                'FAIL',
                f'Found {len(small_instances)} small instances',
                ['Replace small instances with medium or larger']
            )
        else:
            return self._create_result(
                'PASS',
                'No small instances found'
            )