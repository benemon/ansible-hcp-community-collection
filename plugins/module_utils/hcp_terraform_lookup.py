from ansible.plugins.lookup import LookupBase
from ansible.errors import AnsibleError
from ansible.utils.display import Display
import os
import requests
import sys
import time
import random

display = Display()

class HCPTerraformLookup(LookupBase):
    """Base class for HCP Terraform lookup plugins."""
    
    def __init__(self, *args, **kwargs):
        """Initialize the base class with common configuration."""
        super().__init__(*args, **kwargs)
        self.base_url = None  # Will be set during run() based on hostname
        
        # Warn macOS users about potential fork() safety issues
        if sys.platform == 'darwin' and 'OBJC_DISABLE_INITIALIZE_FORK_SAFETY' not in os.environ:
            display.warning(
                'On macOS, you may need to set OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES '
                'if you encounter fork()-related crashes'
            )

    def _get_headers(self, token):
        """Return authentication headers for API requests."""
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/vnd.api+json"
        }

    def _get_auth_token(self, variables):
        """
        Get authentication token for HCP Terraform using this precedence:
        1. Variables: token parameter
        2. Environment: TFE_TOKEN
        """
        token = variables.get('token') or os.environ.get('TFE_TOKEN')
        if not token:
            raise AnsibleError(
                'No valid authentication found. Please set either token parameter '
                'or TFE_TOKEN environment variable.'
            )
        return token

    def _get_hostname(self, variables):
        """
        Get HCP Terraform API hostname using this precedence:
        1. Variables: hostname parameter
        2. Environment: TFE_HOSTNAME
        3. Default: https://app.terraform.io
        """
        hostname = variables.get('hostname') or os.environ.get('TFE_HOSTNAME', 'https://app.terraform.io')
        # Ensure we're using the API v2 endpoint
        if not hostname.endswith('/api/v2'):
            return hostname.rstrip('/') + '/api/v2'
        return hostname

    def _make_request(self, method, endpoint, variables, params=None, max_retries=5):
        """Make request to HCP Terraform API with retries."""
        token = self._get_auth_token(variables)
        headers = self._get_headers(token)
        
        # Handle endpoint with or without leading slash
        if endpoint.startswith('/'):
            url = f"{self.base_url}{endpoint}"
        else:
            url = f"{self.base_url}/{endpoint}"

        base_delay = 2
        max_delay = 64

        for attempt in range(max_retries):
            try:
                display.vvv(f"Making {method} request to {url}")
                if params:
                    display.vvv(f"With parameters: {params}")
                    
                response = requests.request(method, url, headers=headers, params=params)
                
                # Handle rate limiting
                if response.status_code == 429:
                    if attempt == max_retries - 1:
                        raise AnsibleError('Maximum retry attempts reached for rate limit (429 Too Many Requests)')
                    
                    # Check for Retry-After header
                    retry_after = response.headers.get('Retry-After')
                    if retry_after:
                        try:
                            delay = float(retry_after)
                        except (ValueError, TypeError):
                            # Fall back to exponential backoff if header is invalid
                            delay = min(base_delay * (2 ** attempt) + random.uniform(0, 1), max_delay)
                    else:
                        # Use exponential backoff with jitter if no Retry-After header
                        delay = min(base_delay * (2 ** attempt) + random.uniform(0, 1), max_delay)
                    
                    display.vvv(f"Rate limit exceeded. Retrying in {delay:.2f} seconds (attempt {attempt + 1}/{max_retries})")
                    time.sleep(delay)
                    continue
                
                # Handle server errors with retry
                if response.status_code in [500, 502, 503, 504] and attempt < max_retries - 1:
                    delay = min(base_delay * (2 ** attempt) + random.uniform(0, 1), max_delay)
                    display.vvv(f"Server error {response.status_code}. Retrying in {delay:.2f} seconds")
                    time.sleep(delay)
                    continue
                    
                # For all other errors, just raise the exception
                response.raise_for_status()
                
                # Return JSON response if content exists
                if response.text:
                    return response.json()
                return {}
                
            except requests.exceptions.RequestException as e:
                if attempt == max_retries - 1:
                    raise AnsibleError(f'Error making request to HCP Terraform API: {str(e)}')
                # Calculate delay for non-429 errors
                delay = min(base_delay * (2 ** attempt) + random.uniform(0, 1), max_delay)
                time.sleep(delay)
                continue
            except Exception as e:
                raise AnsibleError(f'Unexpected error during API request: {str(e)}')

    def _parse_parameters(self, terms, variables):
        """Parse parameters from terms and variables."""
        params = {}
        
        # Process terms
        for term in terms:
            if isinstance(term, str) and '=' in term:
                key, value = term.split('=', 1)
                params[key] = value
                
        # Add other variables
        for key, value in variables.items():
            if key not in params:
                params[key] = value
                
        return params

    def _validate_params(self, params, required_params):
        """Validate required parameters are present."""
        for param in required_params:
            if param not in params or not params[param]:
                raise AnsibleError(f'Missing required parameter: {param}')

    def _handle_pagination(self, endpoint, variables, query_params=None):
        """Handle paginated requests for Terraform API while preserving structure."""
        if query_params is None:
            query_params = {}
                
        # Extract pagination settings
        page_size = variables.get('page_size')
        if page_size:
            try:
                page_size = int(page_size)
                query_params['page[size]'] = page_size
            except ValueError:
                raise AnsibleError(f"Invalid page_size: {page_size}")
                    
        max_pages = variables.get('max_pages')
        if max_pages:
            try:
                max_pages = int(max_pages)
            except ValueError:
                raise AnsibleError(f"Invalid max_pages: {max_pages}")
        
        # If pagination is disabled, make single request
        if variables.get('disable_pagination', False):
            return self._make_request('GET', endpoint, variables, query_params)

        # For API endpoints that return collections, we'll combine the data arrays
        # but preserve the rest of the response structure
        response = self._make_request('GET', endpoint, variables, query_params)
        
        # If the response doesn't have pagination info, return the raw response
        if 'meta' not in response or 'pagination' not in response['meta']:
            return response
        
        # Extract pagination info
        pagination = response['meta']['pagination']
        total_pages = pagination.get('total-pages', 1)
        current_page = pagination.get('current-page', 1)
        
        # Respect max_pages if set
        if max_pages:
            total_pages = min(total_pages, max_pages)
        
        # If there's only one page, return the response as is
        if total_pages <= 1:
            return response
        
        # For paginated results, we'll combine the data arrays
        all_data = response.get('data', [])
        
        # Continue paginating if needed
        while current_page < total_pages:
            current_page += 1
            query_params['page[number]'] = current_page
            
            try:
                page_response = self._make_request('GET', endpoint, variables, query_params)
                if 'data' in page_response and isinstance(page_response['data'], list):
                    all_data.extend(page_response['data'])
            except Exception as e:
                display.warning(f"Error processing page {current_page}: {str(e)}")
                break
        
        # Create a copy of the original response
        combined_response = response.copy()
        # Replace the data array with our combined one
        combined_response['data'] = all_data
        # Update the pagination info
        if 'meta' in combined_response and 'pagination' in combined_response['meta']:
            combined_response['meta']['pagination']['current-page'] = total_pages
            combined_response['meta']['pagination']['next-page'] = None
        
        return combined_response