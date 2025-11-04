"""
API client for calling Lambda backend.
Falls back to local execution if API is not configured.
"""
import os
import json
import requests
from pathlib import Path


def get_api_config():
    """
    Get API configuration from environment or config file.
    
    Returns:
        dict with 'base_url' and 'api_secret', or None if not configured
    """
    # Try environment variables first
    base_url = os.environ.get('COST_API_URL')
    api_secret = os.environ.get('COST_API_SECRET')
    
    if base_url and api_secret:
        return {
            'base_url': base_url.rstrip('/'),
            'api_secret': api_secret
        }
    
    # Try config file
    config_dir = Path.home() / '.config' / 'cost-calculator'
    api_config_file = config_dir / 'api_config.json'
    
    if api_config_file.exists():
        with open(api_config_file, 'r') as f:
            config = json.load(f)
            if 'base_url' in config and 'api_secret' in config:
                return {
                    'base_url': config['base_url'].rstrip('/'),
                    'api_secret': config['api_secret']
                }
    
    return None


def call_lambda_api(endpoint, credentials, accounts, **kwargs):
    """
    Call Lambda API endpoint.
    
    Args:
        endpoint: API endpoint name ('trends', 'monthly', 'drill')
        credentials: dict with AWS credentials
        accounts: list of account IDs
        **kwargs: additional parameters for the specific endpoint
    
    Returns:
        dict: API response data
    
    Raises:
        Exception: if API call fails
    """
    api_config = get_api_config()
    
    if not api_config:
        raise Exception("API not configured. Set COST_API_URL and COST_API_SECRET environment variables.")
    
    # Map endpoint names to URLs
    endpoint_urls = {
        'trends': f"{api_config['base_url']}/trends",
        'monthly': f"{api_config['base_url']}/monthly",
        'drill': f"{api_config['base_url']}/drill"
    }
    
    # For the actual Lambda URLs (no path)
    if '/trends' not in api_config['base_url']:
        # Base URL is the function URL itself
        url = api_config['base_url']
    else:
        url = endpoint_urls.get(endpoint)
    
    if not url:
        raise Exception(f"Unknown endpoint: {endpoint}")
    
    # Build request payload
    payload = {
        'credentials': credentials,
        'accounts': accounts
    }
    payload.update(kwargs)
    
    # Make API call
    headers = {
        'X-API-Secret': api_config['api_secret'],
        'Content-Type': 'application/json'
    }
    
    response = requests.post(url, headers=headers, json=payload, timeout=300)
    
    if response.status_code != 200:
        raise Exception(f"API call failed: {response.status_code} - {response.text}")
    
    return response.json()


def is_api_configured():
    """Check if API is configured."""
    return get_api_config() is not None
