from .base import BaseCheck
from botocore.exceptions import ClientError

class AddonsCheck(BaseCheck):
    """Check addon compatibility"""
    
    AUTOMODE_ADDONS = {
        'kube-proxy', 'vpc-cni', 'coredns', 
        'ebs-csi-driver', 'aws-load-balancer-controller'
    }
    
    def _execute_check(self):
        issues = []
        
        # Check managed addons
        addons = self.eks_client.list_addons(clusterName=self.cluster_name)
        managed_addon_names = set(addons.get('addons', []))
        
        # Check for Auto Mode addons that should be removed
        conflicting_addons = managed_addon_names.intersection(self.AUTOMODE_ADDONS)
        
        if conflicting_addons:
            issues.append(f"Managed addons to remove: {', '.join(sorted(conflicting_addons))}")
        
        # Check VPC CNI specifically
        if 'vpc-cni' not in managed_addon_names:
            issues.append("VPC CNI not installed (required for Auto Mode)")
        
        if issues:
            recommendations = [
                'Remove Auto Mode addons after migration',
                'Auto Mode will manage these automatically'
            ]
            recommendations.extend(issues)
            
            return self._create_result(
                'WARN',
                f'Found {len(issues)} addon issues',
                recommendations
            )
        else:
            return self._create_result(
                'PASS',
                'Addon configuration compatible'
            )