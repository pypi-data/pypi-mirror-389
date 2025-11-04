"""
Executor that routes to either API or local execution.
"""
import boto3
import click
from cost_calculator.api_client import is_api_configured, call_lambda_api


def get_credentials_dict(config):
    """
    Extract credentials from config in format needed for API.
    
    Returns:
        dict with access_key, secret_key, session_token
    """
    if 'aws_profile' in config:
        # Get temporary credentials from SSO session
        session = boto3.Session(profile_name=config['aws_profile'])
        credentials = session.get_credentials()
        frozen_creds = credentials.get_frozen_credentials()
        
        return {
            'access_key': frozen_creds.access_key,
            'secret_key': frozen_creds.secret_key,
            'session_token': frozen_creds.token
        }
    else:
        # Use static credentials
        creds = config['credentials']
        result = {
            'access_key': creds['aws_access_key_id'],
            'secret_key': creds['aws_secret_access_key']
        }
        if 'aws_session_token' in creds:
            result['session_token'] = creds['aws_session_token']
        return result


def execute_trends(config, weeks):
    """
    Execute trends analysis via API or locally.
    
    Returns:
        dict: trends data
    """
    accounts = config['accounts']
    
    if is_api_configured():
        # Use API
        click.echo("Using Lambda API...")
        credentials = get_credentials_dict(config)
        return call_lambda_api('trends', credentials, accounts, weeks=weeks)
    else:
        # Use local execution
        click.echo("Using local execution...")
        from cost_calculator.trends import analyze_trends
        
        # Initialize boto3 client
        if 'aws_profile' in config:
            session = boto3.Session(profile_name=config['aws_profile'])
        else:
            creds = config['credentials']
            session_kwargs = {
                'aws_access_key_id': creds['aws_access_key_id'],
                'aws_secret_access_key': creds['aws_secret_access_key'],
                'region_name': creds.get('region', 'us-east-1')
            }
            if 'aws_session_token' in creds:
                session_kwargs['aws_session_token'] = creds['aws_session_token']
            session = boto3.Session(**session_kwargs)
        
        ce_client = session.client('ce', region_name='us-east-1')
        return analyze_trends(ce_client, accounts, weeks)


def execute_monthly(config, months):
    """
    Execute monthly analysis via API or locally.
    
    Returns:
        dict: monthly data
    """
    accounts = config['accounts']
    
    if is_api_configured():
        # Use API
        click.echo("Using Lambda API...")
        credentials = get_credentials_dict(config)
        return call_lambda_api('monthly', credentials, accounts, months=months)
    else:
        # Use local execution
        click.echo("Using local execution...")
        from cost_calculator.monthly import analyze_monthly_trends
        
        # Initialize boto3 client
        if 'aws_profile' in config:
            session = boto3.Session(profile_name=config['aws_profile'])
        else:
            creds = config['credentials']
            session_kwargs = {
                'aws_access_key_id': creds['aws_access_key_id'],
                'aws_secret_access_key': creds['aws_secret_access_key'],
                'region_name': creds.get('region', 'us-east-1')
            }
            if 'aws_session_token' in creds:
                session_kwargs['aws_session_token'] = creds['aws_session_token']
            session = boto3.Session(**session_kwargs)
        
        ce_client = session.client('ce', region_name='us-east-1')
        return analyze_monthly_trends(ce_client, accounts, months)


def execute_drill(config, weeks, service_filter=None, account_filter=None, usage_type_filter=None):
    """
    Execute drill-down analysis via API or locally.
    
    Returns:
        dict: drill data
    """
    accounts = config['accounts']
    
    if is_api_configured():
        # Use API
        click.echo("Using Lambda API...")
        credentials = get_credentials_dict(config)
        kwargs = {'weeks': weeks}
        if service_filter:
            kwargs['service'] = service_filter
        if account_filter:
            kwargs['account'] = account_filter
        if usage_type_filter:
            kwargs['usage_type'] = usage_type_filter
        return call_lambda_api('drill', credentials, accounts, **kwargs)
    else:
        # Use local execution
        click.echo("Using local execution...")
        from cost_calculator.drill import analyze_drill_down
        
        # Initialize boto3 client
        if 'aws_profile' in config:
            session = boto3.Session(profile_name=config['aws_profile'])
        else:
            creds = config['credentials']
            session_kwargs = {
                'aws_access_key_id': creds['aws_access_key_id'],
                'aws_secret_access_key': creds['aws_secret_access_key'],
                'region_name': creds.get('region', 'us-east-1')
            }
            if 'aws_session_token' in creds:
                session_kwargs['aws_session_token'] = creds['aws_session_token']
            session = boto3.Session(**session_kwargs)
        
        ce_client = session.client('ce', region_name='us-east-1')
        return analyze_drill_down(
            ce_client, accounts, weeks,
            service_filter=service_filter,
            account_filter=account_filter,
            usage_type_filter=usage_type_filter
        )
