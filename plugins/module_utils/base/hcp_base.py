from ansible.plugins.lookup import LookupBase
from ansible.errors import AnsibleError
from ansible.utils.display import Display
import os
import requests
import sys
import json
import time
import random 
from datetime import datetime, timezone, timedelta

display = Display()

# Module level token cache
_TOKEN_CACHE = {
    'token': None,
    'issued_at': None,
    'expires_in': None,
    'client_id': None,
    'client_secret': None
}

class HCPLookupBase(LookupBase):
    """Base class for HCP lookup plugins."""
    
    def __init__(self, *args, **kwargs):
        """Initialize the base class with common configuration."""
        super().__init__(*args, **kwargs)
        self.base_url = "https://api.cloud.hashicorp.com"

        # Warn macOS users about potential fork() safety issues
        if sys.platform == 'darwin' and 'OBJC_DISABLE_INITIALIZE_FORK_SAFETY' not in os.environ:
            display.warning(
                'On macOS, you may need to set OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES '
                'if you encounter fork()-related crashes'
            )

    def _should_refresh_token(self):
        """
        Check if token should be refreshed based on Hashicorp's 2/3 lifetime practice
        """
        global _TOKEN_CACHE
        
        if not all([_TOKEN_CACHE['token'], _TOKEN_CACHE['issued_at'], _TOKEN_CACHE['expires_in']]):
            return True

        now = datetime.now(timezone.utc)
        issued_at = _TOKEN_CACHE['issued_at']
        expires_in = timedelta(seconds=_TOKEN_CACHE['expires_in'])
        
        # Calculate how far through the token lifetime we are
        token_age = now - issued_at
        two_thirds_lifetime = (expires_in * 2) / 3

        return token_age >= two_thirds_lifetime

    def _get_auth_token(self, variables):
        """
        Get HCP authentication token using the following precedence:
        1. Direct token:
           - Environment: HCP_TOKEN
           - Variable: hcp_token
        2. Client credentials:
           - Environment: HCP_CLIENT_ID + HCP_CLIENT_SECRET
           - Variables: hcp_client_id + hcp_client_secret
        """
        # Check for direct token
        token = (variables.get('hcp_token') or 
                os.environ.get('HCP_TOKEN'))
        if token:
            return token

        # Get client credentials
        client_id = (variables.get('hcp_client_id') or 
                    os.environ.get('HCP_CLIENT_ID'))
        client_secret = (variables.get('hcp_client_secret') or 
                        os.environ.get('HCP_CLIENT_SECRET'))

        if not (client_id and client_secret):
            raise AnsibleError(
                'No valid authentication found. Please set either HCP_TOKEN/hcp_token '
                'or HCP_CLIENT_ID/hcp_client_id and HCP_CLIENT_SECRET/hcp_client_secret'
            )

        global _TOKEN_CACHE
        
        # Check if we should use cached token
        if (_TOKEN_CACHE['token'] and 
            _TOKEN_CACHE['client_id'] == client_id and
            _TOKEN_CACHE['client_secret'] == client_secret and
            not self._should_refresh_token()):
            
            display.vvv("Using cached token")
            return _TOKEN_CACHE['token']

        # Get new token and cache it
        display.vvv("Getting new token")
        token_data = self._get_token_from_credentials(client_id, client_secret)
        
        _TOKEN_CACHE.update({
            'token': token_data['access_token'],
            'issued_at': datetime.now(timezone.utc),
            'expires_in': token_data['expires_in'],
            'client_id': client_id,
            'client_secret': client_secret
        })
        
        return token_data['access_token']

    def get_token_from_credentials(self, client_id, client_secret):
        """
        Obtain token from client credentials with backoff retry logic
        """
        url = f"{self.base_url}/oauth/token"
        data = {
            'grant_type': 'client_credentials',
            'audience': 'https://api.hashicorp.cloud',
            'client_id': client_id,
            'client_secret': client_secret
        }

        max_retries = 5  # Maximum number of retry attempts
        base_delay = 1   # Initial delay in seconds
        max_delay = 32   # Maximum delay between retries

        for attempt in range(max_retries):
            try:
                response = requests.post(url, json=data)
                
                if response.status_code == 429:  # Rate limit exceeded
                    if attempt == max_retries - 1:
                        raise AnsibleError('Maximum retry attempts reached for rate limit')
                    
                    # Calculate exponential backoff with jitter
                    delay = min(base_delay * (2 ** attempt) + random.uniform(0, 1), max_delay)
                    display.vvv(f"Rate limit exceeded. Retrying in {delay:.2f} seconds (attempt {attempt + 1}/{max_retries})")
                    time.sleep(delay)
                    continue

                response.raise_for_status()
                
                json_response = response.json()
                display.vvv("Successfully obtained auth token")
                
                if not all(k in json_response for k in ['access_token', 'expires_in']):
                    display.vvv(f"Unexpected response format. Keys: {list(json_response.keys())}")
                    raise KeyError('Missing required fields in response')
                
                return json_response
                
            except requests.exceptions.RequestException as e:
                if attempt == max_retries - 1:
                    raise AnsibleError(f'Failed to obtain token from client credentials: {str(e)}')
                continue
            except KeyError as e:
                raise AnsibleError(f'Unexpected response format from auth endpoint: {str(e)}')
            except Exception as e:
                raise AnsibleError(f'Unexpected error while obtaining token: {str(e)}')

    def _get_headers(self, token):
        """Get standard headers for HCP API."""
        return {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

    def _make_request(self, method, endpoint, variables, params=None):
        """Make request to HCP API."""
        token = self._get_auth_token(variables)
        headers = self._get_headers(token)
        url = f"{self.base_url}/{endpoint}"

        try:
            display.vvv(f"Making {method} request to {url}")
            if params:
                display.vvv(f"With parameters: {json.dumps(params, indent=2)}")
                
            response = requests.request(method, url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise AnsibleError(f'Error making request to HCP API: {str(e)}')

    def _process_parameters(self, variables):
        """Process and validate all query parameters including pagination."""
        query_params = {}
        pagination_config = {
            'enabled': not variables.get('disable_pagination', False),
            'page_size': None,
            'max_pages': None
        }

        # Process pagination parameters
        if 'page_size' in variables:
            try:
                page_size = int(variables['page_size'])
                if page_size <= 0:
                    raise ValueError("page_size must be positive")
                pagination_config['page_size'] = page_size
                query_params['pagination.page_size'] = page_size
            except ValueError as e:
                raise AnsibleError(f"Invalid page_size: {str(e)}")

        if 'max_pages' in variables:
            try:
                max_pages = int(variables['max_pages'])
                if max_pages <= 0:
                    raise ValueError("max_pages must be positive")
                pagination_config['max_pages'] = max_pages
            except ValueError as e:
                raise AnsibleError(f"Invalid max_pages: {str(e)}")

        # Process standard filter parameters
        if 'name_contains' in variables:
            query_params['name_contains'] = variables['name_contains']

        if 'types' in variables:
            if isinstance(variables['types'], str):
                query_params['types'] = variables['types'].split(',')
            elif isinstance(variables['types'], (list, tuple)):
                query_params['types'] = variables['types']
            else:
                raise AnsibleError(f"Invalid types parameter format: {variables['types']}")

        display.vvv(f"Processed parameters: query_params={query_params}, "
                   f"pagination_config={pagination_config}")
        
        return query_params, pagination_config

    def _validate_params(self, terms, variables, required_params):
        """Validate required parameters are present."""
        for param in required_params:
            if param not in variables:
                raise AnsibleError(f'Missing required parameter: {param}')

    def _handle_pagination(self, endpoint, variables, query_params=None):
        """Handle paginated requests with configurable behavior."""
        # Process parameters
        params, pagination_config = self._process_parameters(variables)
        if query_params:
            params.update(query_params)

        # If pagination is disabled, make single request
        if not pagination_config['enabled']:
            response = self._make_request('GET', endpoint, variables, params)
            return self._extract_results(response)

        all_results = []
        next_token = None
        page_count = 0
        max_pages = pagination_config['max_pages']

        while True:
            # Increment page counter
            page_count += 1

            # Check max_pages limit
            if max_pages and page_count > max_pages:
                break

            # Set next page token if we have one
            if next_token:
                params['pagination.next_page_token'] = next_token

            # Make request and extract results
            try:
                response = self._make_request('GET', endpoint, variables, params)
                page_results = self._extract_results(response)
                
                if 'results' in page_results:
                    all_results.extend(page_results['results'])
                else:
                    display.warning(f"Unexpected response structure: {response}")
                    break

                # Check for next page token
                pagination = response.get('pagination', {})
                next_token = pagination.get('next_page_token')
                
                # Break if no next token
                if not next_token:
                    break

            except Exception as e:
                display.warning(f"Error processing page {page_count}: {str(e)}")
                break

        return {'results': all_results}

    def _extract_results(self, response):
        """Extract results from response using known patterns."""
        # Handle response with direct results
        if isinstance(response, list):
            return {'results': response}

        # Check for known result keys
        result_keys = ['apps', 'secrets', 'secret', 'integrations', 'version', 'channel']
        for key in result_keys:
            if key in response:
                return {'results': response[key]}

        # If we have pagination metadata but results are at root level
        if 'pagination' in response:
            # Create a new dict excluding pagination
            results = {k: v for k, v in response.items() if k != 'pagination'}
            if results:
                return {'results': [results]}

        # Return empty results if no pattern matched
        return {'results': []}