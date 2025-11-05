from .base import BaseCheck
from botocore.exceptions import ClientError

class LoadBalancersCheck(BaseCheck):
    """Check for ALBs and NLBs associated with EKS services and ingresses"""
    
    def _execute_check(self):
        load_balancers = []
        
        # Check for ALBs and NLBs
        albs = self._get_load_balancers_by_type('application')
        nlbs = self._get_load_balancers_by_type('network')
        
        if albs:
            load_balancers.extend([f"ALB: {alb}" for alb in albs])
        if nlbs:
            load_balancers.extend([f"NLB: {nlb}" for nlb in nlbs])
        
        if load_balancers:
            return self._create_result(
                'WARN',
                f'Found {len(load_balancers)} load balancers',
                [
                    'Load balancers will continue to work with Auto Mode',
                    'Verify load balancer configurations after migration'
                ]
            )
        else:
            return self._create_result(
                'PASS',
                'No load balancers detected'
            )
    
    def _get_load_balancers_by_type(self, lb_type):
        """Get load balancers of specified type tagged with cluster name"""
        try:
            elbv2_client = self.checker.session.client('elbv2', region_name=self.region)
            response = elbv2_client.describe_load_balancers()
            
            load_balancers = []
            tag_keys = self._get_cluster_tag_keys(lb_type)
            
            for lb in response.get('LoadBalancers', []):
                if lb.get('Type') == lb_type and self._is_cluster_load_balancer(elbv2_client, lb, tag_keys):
                    load_balancers.append(lb.get('LoadBalancerName', 'Unknown'))
            
            return load_balancers
        except ClientError:
            return []
    
    def _get_cluster_tag_keys(self, lb_type):
        """Get relevant tag keys for cluster association"""
        base_key = f'kubernetes.io/cluster/{self.cluster_name}'
        if lb_type == 'application':
            return [base_key, 'elbv2.k8s.aws/cluster']
        else:  # network
            return [base_key, 'service.k8s.aws/cluster']
    
    def _is_cluster_load_balancer(self, elbv2_client, lb, tag_keys):
        """Check if load balancer is associated with cluster"""
        try:
            tags_response = elbv2_client.describe_tags(ResourceArns=[lb['LoadBalancerArn']])
            for tag_desc in tags_response.get('TagDescriptions', []):
                for tag in tag_desc.get('Tags', []):
                    tag_key = tag.get('Key', '')
                    tag_value = tag.get('Value', '')
                    if (tag_key in tag_keys and 
                        (tag_key.startswith('kubernetes.io/cluster/') or tag_value == self.cluster_name)):
                        return True
            return False
        except ClientError:
            return False