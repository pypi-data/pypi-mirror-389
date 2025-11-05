from .base import BaseCheck
from botocore.exceptions import ClientError

class IdentityCheck(BaseCheck):
    """Check for IRSA v1 or Pod Identity usage"""
    
    def _execute_check(self):
        has_oidc = self._check_oidc_provider()
        has_pod_identity = self._check_pod_identity()
        
        if has_pod_identity:
            return self._create_result(
                'PASS',
                'Using Pod Identity',
                ['Pod Identity is the recommended method for Auto Mode']
            )
        elif has_oidc:
            return self._create_result(
                'WARN',
                'Using IRSA v1 (OIDC)',
                ['Consider migrating to Pod Identity for better Auto Mode compatibility']
            )
        else:
            return self._create_result(
                'WARN',
                'No identity methods detected',
                ['Consider using Pod Identity for workload authentication']
            )
    
    def _check_oidc_provider(self):
        """Check if OIDC provider exists for IRSA"""
        try:
            cluster_oidc = self.cluster_info.get('identity', {}).get('oidc', {})
            return cluster_oidc.get('issuer') is not None
        except (KeyError, AttributeError, TypeError):
            return False
    
    def _check_pod_identity(self):
        """Check for Pod Identity associations"""
        try:
            associations = self.eks_client.list_pod_identity_associations(clusterName=self.cluster_name)
            return len(associations.get('associations', [])) > 0
        except ClientError:
            return False