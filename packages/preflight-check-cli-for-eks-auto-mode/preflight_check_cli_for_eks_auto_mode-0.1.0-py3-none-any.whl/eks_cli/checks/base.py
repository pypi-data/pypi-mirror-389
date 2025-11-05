from botocore.exceptions import ClientError
from ..security import secure_error_message

class BaseCheck:
    """Base class for all CLI checks"""
    
    def __init__(self, checker):
        try:
            self.checker = checker
            self.cluster_name = checker.cluster_name
            self.region = checker.region
            self.cluster_info = checker.cluster_info
            self.eks_client = checker.eks_client
            self.ec2_client = checker.ec2_client
            self.iam_client = checker.iam_client
        except AttributeError as e:
            raise ValueError(f"Invalid checker configuration: {e}")
    
    def run(self):
        """Run the check and return result"""
        try:
            return self._execute_check()
        except ClientError as e:
            return self._create_result('ERROR', f'AWS API error: {e.response["Error"]["Code"]}')
        except Exception as e:
            return self._create_result('ERROR', f'Check failed: {secure_error_message(e)}')
    
    def _execute_check(self):
        """Execute the actual check logic - to be implemented by subclasses"""
        try:
            raise NotImplementedError("Subclasses must implement _execute_check method")
        except NotImplementedError:
            raise
        except Exception as e:
            raise RuntimeError(f"Unexpected error in check execution: {e}")
    
    def _create_result(self, status, details, recommendations=None):
        """Create standardized result format"""
        if status not in ['PASS', 'WARN', 'FAIL', 'ERROR']:
            status = 'ERROR'
        
        result = {
            'status': status,
            'details': str(details) if details else 'No details available'
        }
        if recommendations:
            result['recommendations'] = [str(r) for r in recommendations if r]
        return result