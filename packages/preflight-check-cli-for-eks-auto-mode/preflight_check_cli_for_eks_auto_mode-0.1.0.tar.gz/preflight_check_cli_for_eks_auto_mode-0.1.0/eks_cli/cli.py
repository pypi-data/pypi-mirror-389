#!/usr/bin/env python3

import click
import json
import yaml
import sys
import os
import html
from datetime import datetime
from tabulate import tabulate
from pathlib import Path
from eks_cli.checker import EKSAutoModeCLIChecker
from eks_cli.security import SecurityValidator, CredentialProtector, secure_error_message

@click.group()
@click.version_option(version='0.1.0', prog_name='Preflight Check CLI for EKS Auto Mode')
def cli():
    """Preflight Check CLI for EKS Auto Mode - Quick cluster readiness assessment"""
    pass

@cli.command()
@click.option('--cluster', '-c', required=True, help='EKS cluster name')
@click.option('--region', '-r', help='AWS region')
@click.option('--profile', '-p', help='AWS profile name')
@click.option('--output', '-o', type=click.Choice(['table', 'json', 'yaml', 'html']), default='table', help='Output format')
@click.option('--checks', help='Comma-separated list of checks to run')
@click.option('--verbose', '-v', is_flag=True, help='Include detailed recommendations')
@click.option('--quiet', '-q', is_flag=True, help='Minimal output, exit codes only')
def check(cluster, region, profile, output, checks, verbose, quiet):
    """Perform Auto Mode compatibility assessment"""
    
    try:
        # Enhanced input validation
        cluster = SecurityValidator.validate_cluster_name(cluster)
        region = SecurityValidator.validate_region(region)
        profile = SecurityValidator.validate_profile(profile)
        check_list = SecurityValidator.validate_checks_list(checks)
    except ValueError as e:
        if not quiet:
            click.echo(f"Input validation error: {secure_error_message(e)}", err=True)
        sys.exit(3)
    
    try:
        checker = EKSAutoModeCLIChecker(cluster, region, profile)
        
        # Validate AWS credentials and account access
        try:
            credential_info = CredentialProtector.validate_credentials(checker.session)
            if not CredentialProtector.validate_account_access(checker.session):
                if not quiet:
                    click.echo("Warning: Account access validation failed", err=True)
        except Exception as e:
            if not quiet:
                click.echo(f"Credential validation error: {secure_error_message(e)}", err=True)
            sys.exit(3)
        
        results = checker.run_checks(check_list)
        
        if quiet:
            # Only exit with appropriate code
            exit_code = _get_exit_code(results)
            sys.exit(exit_code)
        
        if output == 'json':
            click.echo(json.dumps(results, indent=2, default=str))
        elif output == 'yaml':
            click.echo(yaml.dump(results, default_flow_style=False))
        elif output == 'html':
            _generate_html_report(results)
        else:
            _print_table_output(results, verbose)
        
        # Exit with appropriate code
        exit_code = _get_exit_code(results)
        sys.exit(exit_code)
        
    except ValueError as e:
        if not quiet:
            click.echo(f"Error: {secure_error_message(e)}", err=True)
        sys.exit(3)
    except Exception as e:
        if not quiet:
            click.echo(f"Unexpected error: {secure_error_message(e)}", err=True)
        sys.exit(3)

@cli.command('list-checks')
def list_checks():
    """List all available validation checks"""
    checks = [
        ('version', 'Kubernetes version compatibility (1.29+)'),
        ('iam', 'IAM roles and Auto Mode policies'),
        ('instances', 'Instance type compatibility'),
        ('windows', 'Windows node detection'),
        ('ssh', 'SSH/SSM access detection'),
        ('amis', 'Custom AMI usage'),
        ('userdata', 'User data configuration'),
        ('addons', 'Addon compatibility analysis'),
        ('autoscaling', 'Autoscaling configuration'),
        ('identity', 'IRSA v1 and Pod Identity detection'),
        ('loadbalancers', 'ALB and NLB detection')
    ]
    
    click.echo("Available validation checks:")
    for check_name, description in checks:
        click.echo(f"  {check_name:<12} {description}")

def _print_table_output(results, verbose):
    """Print results in table format"""
    
    # Header
    click.echo(f"\nPreflight Check CLI for EKS Auto Mode - {results['cluster']}")
    click.echo(f"Region: {results['region']} | Timestamp: {results['timestamp']}")
    click.echo(f"Overall Status: {_format_status(results['overall_status'])}")
    click.echo()
    
    # Prepare table data
    table_data = []
    for check_name, check_result in results['checks'].items():
        status = check_result['status']
        details = check_result.get('details', '')
        
        # Truncate details for table display
        if len(details) > 50:
            details = details[:47] + '...'
        
        table_data.append([
            check_name,
            _format_status(status),
            details
        ])
    
    # Print table
    headers = ['Check', 'Status', 'Details']
    click.echo(tabulate(table_data, headers=headers, tablefmt='grid'))
    
    # Print recommendations if verbose
    if verbose:
        click.echo("\nRecommendations:")
        for check_name, check_result in results['checks'].items():
            if 'recommendations' in check_result and check_result['recommendations']:
                click.echo(f"\n{check_name.upper()}:")
                for rec in check_result['recommendations']:
                    click.echo(f"  • {rec}")

def _format_status(status):
    """Format status with colors"""
    colors = {
        'PASS': 'green',
        'WARN': 'yellow', 
        'FAIL': 'red',
        'ERROR': 'red',
        'READY': 'green',
        'REQUIRES_CHANGES': 'yellow',
        'NOT_READY': 'red'
    }
    return click.style(status, fg=colors.get(status, 'white'))

def _generate_html_report(results):
    """Generate HTML report in results folder using EKS Automode Preflight Report V2 format"""
    try:
        # Secure path handling
        results_dir = Path('results').resolve()
        results_dir.mkdir(exist_ok=True)
        
        # Validate results directory is within expected bounds
        current_dir = Path.cwd()
        if not results_dir.is_relative_to(current_dir):
            raise ValueError("Results directory must be within current working directory")
    except (OSError, ValueError) as e:
        click.echo(f"Error creating results directory: {e}", err=True)
        return
    
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Preflight Check CLI for EKS Auto Mode - Report V2</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        :root {{
            --primary-color: rgb(35, 47, 62);
            --secondary-color: rgb(255, 153, 0);
            --success-color: rgb(22, 160, 133);
            --warning-color: rgb(243, 156, 18);
            --danger-color: rgb(231, 76, 60);
            --info-color: rgb(52, 152, 219);
            --light-bg: rgb(248, 249, 250);
            --white: rgb(255, 255, 255);
            --text-dark: rgb(44, 62, 80);
            --text-muted: rgb(127, 140, 141);
            --border-color: rgb(233, 236, 239);
        }}
        
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        body {{
            font-family: 'Amazon Ember', 'Helvetica Neue', Helvetica, Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: var(--text-dark);
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}
        
        .report-header {{
            background: var(--white);
            border-radius: 12px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            border-left: 6px solid var(--secondary-color);
        }}
        
        .report-title {{
            display: flex;
            align-items: center;
            gap: 15px;
            margin-bottom: 20px;
        }}
        
        .report-title h1 {{
            color: var(--primary-color);
            font-size: 2.2rem;
            font-weight: 700;
        }}
        
        .aws-logo {{
            width: 60px;
            height: 36px;
            background: var(--secondary-color);
            border-radius: 4px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
            font-size: 14px;
        }}
        
        .cluster-info {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }}
        
        .info-card {{
            background: var(--light-bg);
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid var(--info-color);
        }}
        
        .info-label {{
            font-size: 0.9rem;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 8px;
        }}
        
        .info-value {{
            font-size: 1.1rem;
            font-weight: 600;
            color: var(--text-dark);
        }}
        
        .status-overview {{
            background: var(--white);
            border-radius: 12px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            text-align: center;
        }}
        
        .overall-status {{
            font-size: 2rem;
            font-weight: 700;
            margin: 20px 0;
            padding: 15px 30px;
            border-radius: 50px;
            display: inline-block;
        }}
        
        .status-ready {{ background: rgb(213, 244, 230); color: var(--success-color); }}
        .status-requires-changes {{ background: rgb(254, 249, 231); color: var(--warning-color); }}
        .status-not-ready {{ background: rgb(250, 219, 216); color: var(--danger-color); }}
        
        .checks-container {{
            background: var(--white);
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }}
        
        .checks-header {{
            background: var(--primary-color);
            color: var(--white);
            padding: 25px 30px;
            display: flex;
            align-items: center;
            gap: 15px;
        }}
        
        .checks-header h2 {{
            font-size: 1.5rem;
            font-weight: 600;
        }}
        
        .checks-table {{
            width: 100%;
            border-collapse: collapse;
        }}
        
        .checks-table th {{
            background: var(--light-bg);
            padding: 20px;
            text-align: left;
            font-weight: 600;
            color: var(--text-dark);
            border-bottom: 2px solid var(--border-color);
        }}
        
        .checks-table td {{
            padding: 20px;
            border-bottom: 1px solid var(--border-color);
            vertical-align: top;
        }}
        
        .check-name {{
            font-weight: 600;
            color: var(--text-dark);
            text-transform: capitalize;
        }}
        
        .status-badge {{
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            display: inline-flex;
            align-items: center;
            gap: 6px;
        }}
        
        .badge-pass {{ background: rgb(213, 244, 230); color: var(--success-color); }}
        .badge-warn {{ background: rgb(254, 249, 231); color: var(--warning-color); }}
        .badge-fail {{ background: rgb(250, 219, 216); color: var(--danger-color); }}
        .badge-error {{ background: rgb(244, 244, 244); color: rgb(108, 117, 125); }}
        
        .recommendations {{
            background: var(--white);
            border-radius: 12px;
            padding: 30px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }}
        
        .recommendations h2 {{
            color: var(--primary-color);
            margin-bottom: 25px;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .rec-item {{
            background: var(--light-bg);
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
            border-left: 4px solid var(--info-color);
        }}
        
        .rec-title {{
            font-weight: 600;
            color: var(--text-dark);
            margin-bottom: 12px;
            text-transform: capitalize;
        }}
        
        .rec-list {{
            list-style: none;
            padding: 0;
        }}
        
        .rec-list li {{
            padding: 8px 0;
            padding-left: 25px;
            position: relative;
            color: var(--text-dark);
            line-height: 1.5;
        }}
        
        .rec-list li:before {{
            content: '→';
            position: absolute;
            left: 0;
            color: var(--info-color);
            font-weight: bold;
        }}
        
        .footer {{
            text-align: center;
            padding: 30px;
            color: rgba(255,255,255,0.8);
            font-size: 0.9rem;
        }}
        
        .footer p {{
            margin: 5px 0;
        }}
        
        @media (max-width: 768px) {{
            .container {{ padding: 15px; }}
            .report-header {{ padding: 20px; }}
            .report-title h1 {{ font-size: 1.8rem; }}
            .cluster-info {{ grid-template-columns: 1fr; }}
            .checks-table th, .checks-table td {{ padding: 15px 10px; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="report-header">
            <div class="report-title">
                <div class="aws-logo">AWS</div>
                <h1>Preflight Check CLI for EKS Auto Mode - Report V2</h1>
            </div>
            <div class="cluster-info">
                <div class="info-card">
                    <div class="info-label">Cluster Name</div>
                    <div class="info-value">{html.escape(results['cluster'])}</div>
                </div>
                <div class="info-card">
                    <div class="info-label">AWS Region</div>
                    <div class="info-value">{html.escape(results['region'])}</div>
                </div>
                <div class="info-card">
                    <div class="info-label">Assessment Date</div>
                    <div class="info-value">{html.escape(datetime.now().strftime('%B %d, %Y'))}</div>
                </div>
                <div class="info-card">
                    <div class="info-label">Report Version</div>
                    <div class="info-value">V2.0</div>
                </div>
            </div>
        </div>
        
        <div class="status-overview">
            <h2><i class="fas fa-chart-line"></i> Overall Assessment</h2>
            <div class="overall-status status-{html.escape(results['overall_status'].lower().replace('_', '-'))}">
                {html.escape(results['overall_status'].replace('_', ' '))}
            </div>
        </div>
        
        <div class="checks-container">
            <div class="checks-header">
                <i class="fas fa-tasks"></i>
                <h2>Compatibility Assessment Results</h2>
            </div>
            <table class="checks-table">
                <thead>
                    <tr>
                        <th>Check Category</th>
                        <th>Status</th>
                        <th>Assessment Details</th>
                    </tr>
                </thead>
                <tbody>
"""
    
    for check_name, check_result in results['checks'].items():
        status = check_result['status'].lower()
        icon_map = {
            'pass': 'fa-check-circle',
            'warn': 'fa-exclamation-triangle', 
            'fail': 'fa-times-circle',
            'error': 'fa-exclamation-circle'
        }
        icon = icon_map.get(status, 'fa-question-circle')
        
        html_content += f"""
                    <tr>
                        <td class="check-name">{html.escape(check_name.replace('_', ' ').title())}</td>
                        <td>
                            <span class="status-badge badge-{html.escape(status)}">
                                <i class="fas {html.escape(icon)}"></i>
                                {html.escape(check_result['status'])}
                            </span>
                        </td>
                        <td>{html.escape(check_result.get('details', 'No additional details available'))}</td>
                    </tr>
"""
    
    html_content += """
                </tbody>
            </table>
        </div>
        
        <div class="recommendations">
            <h2><i class="fas fa-lightbulb"></i> Recommendations & Action Items</h2>
"""
    
    has_recommendations = False
    for check_name, check_result in results['checks'].items():
        if 'recommendations' in check_result and check_result['recommendations']:
            has_recommendations = True
            html_content += f"""
            <div class="rec-item">
                <div class="rec-title">{html.escape(check_name.replace('_', ' ').title())}</div>
                <ul class="rec-list">
"""
            for rec in check_result['recommendations']:
                html_content += f"<li>{html.escape(str(rec))}</li>"
            html_content += "</ul></div>"
    
    if not has_recommendations:
        html_content += """
            <div class="rec-item">
                <div class="rec-title">✅ All Checks Passed</div>
                <p>Your EKS cluster appears to be ready for Auto Mode migration. No specific action items required at this time.</p>
            </div>
        """
    
    html_content += f"""
        </div>
        
        <div class="footer">
            <p><strong>Preflight Check CLI for EKS Auto Mode v0.1.0</strong></p>
            <p>Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p UTC')}</p>
            <p>© 2024 Amazon Web Services, Inc. or its affiliates. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
"""
    
    # Enhanced secure filename generation
    safe_cluster_name = SecurityValidator.validate_cluster_name(results['cluster'])
    safe_cluster_name = ''.join(c for c in safe_cluster_name if c.isalnum() or c in '-_')[:50]  # Limit length
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    filename = results_dir / f"EKS-Automode-Preflight-Report-V2-{safe_cluster_name}-{timestamp}.html"
    
    try:
        # Validate filename is safe
        if not filename.is_relative_to(results_dir):
            raise ValueError("Invalid filename path")
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        click.echo(f"📊 Preflight Check CLI for EKS Auto Mode Report V2 generated: {filename}")
    except (OSError, IOError, ValueError) as e:
        click.echo(f"Error writing HTML report: {secure_error_message(e)}", err=True)

def _get_exit_code(results):
    """Determine exit code based on results"""
    overall_status = results['overall_status']
    
    if overall_status == 'READY':
        return 0
    elif overall_status == 'REQUIRES_CHANGES':
        return 1
    elif overall_status == 'NOT_READY':
        return 2
    else:
        return 3

if __name__ == '__main__':
    cli()