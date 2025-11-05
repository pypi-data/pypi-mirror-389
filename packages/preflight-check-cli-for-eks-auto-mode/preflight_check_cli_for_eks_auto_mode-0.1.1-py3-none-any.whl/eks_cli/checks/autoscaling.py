from .base import BaseCheck
from botocore.exceptions import ClientError

class AutoscalingCheck(BaseCheck):
    """Check for existing autoscaling solutions"""
    
    def _execute_check(self):
        autoscaling_found = []
        
        # Check for Karpenter
        if self._check_karpenter():
            autoscaling_found.append("Karpenter")
        
        # Check for Cluster Autoscaler
        if self._check_cluster_autoscaler():
            autoscaling_found.append("Cluster Autoscaler")
        
        # Check for ASGs
        if self._check_asgs():
            autoscaling_found.append("Auto Scaling Groups")
        
        if autoscaling_found:
            return self._create_result(
                'WARN',
                f'Found: {", ".join(autoscaling_found)}',
                [
                    'Remove existing autoscaling solutions before enabling Auto Mode',
                    'Auto Mode will manage scaling automatically with Karpenter'
                ]
            )
        else:
            return self._create_result(
                'PASS',
                'No conflicting autoscaling solutions found'
            )
    
    def _check_karpenter(self):
        """Check if Karpenter is installed"""
        try:
            addons = self.eks_client.list_addons(clusterName=self.cluster_name)
            return 'karpenter' in addons.get('addons', [])
        except ClientError:
            return False
    
    def _check_cluster_autoscaler(self):
        """Check if Cluster Autoscaler addon is installed"""
        try:
            addons = self.eks_client.list_addons(clusterName=self.cluster_name)
            return 'cluster-autoscaler' in addons.get('addons', [])
        except ClientError:
            return False
    
    def _check_asgs(self):
        """Check if node groups use ASGs"""
        node_groups = self.eks_client.list_nodegroups(clusterName=self.cluster_name)
        return len(node_groups['nodegroups']) > 0