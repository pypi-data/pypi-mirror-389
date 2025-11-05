from packaging import version
from .base import BaseCheck

class VersionCheck(BaseCheck):
    """Check Kubernetes version compatibility"""
    
    REQUIRED_VERSION = "1.29"
    _REQUIRED_VERSION_PARSED = version.parse(REQUIRED_VERSION)
    
    def _execute_check(self):
        k8s_version = self.cluster_info.get('version')
        if not k8s_version:
            raise ValueError("Kubernetes version not found in cluster info")
        
        try:
            parsed_version = version.parse(k8s_version)
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid Kubernetes version format: {k8s_version}")
        
        if parsed_version >= self._REQUIRED_VERSION_PARSED:
            return self._create_result(
                'PASS',
                f'Kubernetes {k8s_version} (compatible)'
            )
        else:
            return self._create_result(
                'FAIL',
                f'Kubernetes {k8s_version} (requires {self.REQUIRED_VERSION}+)',
                ['Upgrade cluster to Kubernetes 1.29 or higher']
            )