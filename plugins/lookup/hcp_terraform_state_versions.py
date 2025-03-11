DOCUMENTATION = r"""
    name: hcp_terraform_state_versions
    author: benemon
    version_added: "0.0.7"
    short_description: Retrieve state versions from HCP Terraform workspaces
    description:
        - This lookup returns state version information from HCP Terraform workspaces.
        - It does not return the actual state file content for security reasons.
        - Can retrieve the current state version or list state versions for a workspace.
    options:
        token:
            description: HCP Terraform API token (can use TFE_TOKEN env var)
            required: true
            type: str
            env: [TFE_TOKEN]
        hostname:
            description: HCP Terraform API hostname (defaults to app.terraform.io)
            required: false
            type: str
            default: "https://app.terraform.io"
            env: [TFE_HOSTNAME]
        organization:
            description: Organization name containing the workspace
            required: false
            type: str
        workspace_name:
            description: Name of the workspace to retrieve state versions from
            required: false
            type: str
        workspace_id:
            description: ID of the workspace to retrieve state versions from
            required: false
            type: str
        state_version_id:
            description: ID of a specific state version to retrieve
            required: false
            type: str
        get_current:
            description: Get current state version (true) or list all (false)
            required: false
            type: bool
            default: true
        status:
            description: Filter state versions by status when listing
            required: false
            type: str
            choices: ['pending', 'finalized', 'discarded']
        wait_for_processing:
            description: Wait for state version resources to be processed
            required: false
            type: bool
            default: false
        wait_timeout:
            description: Maximum time in seconds to wait for processing
            required: false
            type: int
            default: 120
        include_outputs:
            description: Include outputs in the state version response
            required: false
            type: bool
            default: false
        include_resources:
            description: Include detailed resource information in response
            required: false
            type: bool
            default: false
"""

RETURN = r"""
_raw:
    description: State version information from HCP Terraform.
    type: list
    elements: dict
    contains:
        data:
            description: The state version data.
            type: dict
            contains:
                id:
                    description: The ID of the state version.
                    type: str
                    sample: sv-123456
                type:
                    description: The type of the resource.
                    type: str
                    sample: state-versions
                attributes:
                    description: Attributes of the state version.
                    type: dict
"""

from ansible.errors import AnsibleError
from ansible.utils.display import Display
from ansible_collections.benemon.hcp_community_collection.plugins.module_utils.hcp_terraform_lookup import HCPTerraformLookup
import time

display = Display()
class LookupModule(HCPTerraformLookup):
    def run(self, terms, variables=None, **kwargs):
        """Retrieve state version information from HCP Terraform."""
        variables = variables or {}
        
        # Process parameters
        params = self._parse_parameters(terms, variables)
        
        # Set hostname for base URL
        self.base_url = self._get_hostname(params)
        
        try:
            # Determine how to look up the state version(s)
            if 'state_version_id' in params:
                # Get a specific state version by ID
                result = self._get_state_version_by_id(params['state_version_id'], params)
                
                # Check if we need to wait for processing
                if params.get('wait_for_processing', False) and not result.get('data', {}).get('attributes', {}).get('resources-processed', True):
                    result = self._wait_for_state_version_processing(params['state_version_id'], params.get('wait_timeout', 120))
            else:
                # Get by workspace
                if 'workspace_id' in params:
                    workspace_id = params['workspace_id']
                elif 'organization' in params and 'workspace_name' in params:
                    workspace_id = self._get_workspace_id(params['organization'], params['workspace_name'])
                else:
                    raise AnsibleError("Either workspace_id or both organization and workspace_name must be provided.")
                
                # Get either current state version or list state versions
                if params.get('get_current', True):
                    result = self._get_current_state_version(workspace_id, params)
                else:
                    result = self._list_state_versions(params['organization'], params['workspace_name'], params)
            
            display.vvv(f"Successfully retrieved state version information")
            return [result]
        except Exception as e:
            display.error(f"Error retrieving state versions: {str(e)}")
            raise AnsibleError(f"Error retrieving state versions: {str(e)}")
        
    def _parse_parameters(self, terms, variables):
        """Parse and validate parameters from terms and variables."""
        params = {}
        
        # Process terms (positional arguments)
        for term in terms:
            if '=' in term:
                key, value = term.split('=', 1)
                params[key.strip()] = value.strip()
        
        # Process variables (keyword arguments)
        for key, value in variables.items():
            params[key] = value
        
        # Validate status parameter if provided
        if 'status' in params and params['status'] not in ['pending', 'finalized', 'discarded']:
            raise AnsibleError(f"Invalid status value: {params['status']}. Must be one of: pending, finalized, discarded")
        
        # Convert boolean parameters
        for bool_param in ['get_current', 'wait_for_processing', 'include_outputs', 'include_resources']:
            if bool_param in params and not isinstance(params[bool_param], bool):
                params[bool_param] = str(params[bool_param]).lower() in ['true', 'yes', '1']
        
        # Convert integer parameters
        if 'wait_timeout' in params and not isinstance(params['wait_timeout'], int):
            try:
                params['wait_timeout'] = int(params['wait_timeout'])
            except (ValueError, TypeError):
                raise AnsibleError(f"Invalid wait_timeout value: {params['wait_timeout']}. Must be an integer.")
        
        return params

    def _get_state_version_by_id(self, state_version_id, params):
        """Get a specific state version by ID."""
        endpoint = f"/state-versions/{state_version_id}"
        
        # Add include parameters if requested
        query_params = {}
        if params.get('include_outputs', False):
            query_params['include'] = 'outputs'
        if params.get('include_resources', False):
            if 'include' in query_params:
                query_params['include'] += ',resources'
            else:
                query_params['include'] = 'resources'
        
        return self._make_request('GET', endpoint, params, query_params)

    def _get_current_state_version(self, workspace_id, params):
        """Get the current state version for a workspace."""
        endpoint = f"/workspaces/{workspace_id}/current-state-version"
        
        # Add include parameters if requested
        query_params = {}
        if params.get('include_outputs', False):
            query_params['include'] = 'outputs'
        if params.get('include_resources', False):
            if 'include' in query_params:
                query_params['include'] += ',resources'
            else:
                query_params['include'] = 'resources'
        
        return self._make_request('GET', endpoint, params, query_params)

    def _list_state_versions(self, organization, workspace_name, params):
        """List state versions for a workspace with optional filtering."""
        # Get workspace ID first
        workspace_id = self._get_workspace_id(organization, workspace_name)
        
        # Prepare query parameters for filtering
        query_params = {}
        
        # Add status filter if provided
        if 'status' in params:
            query_params['filter[status]'] = params['status']
        
        # Add include parameters if requested
        if params.get('include_outputs', False):
            query_params['include'] = 'outputs'
        if params.get('include_resources', False):
            if 'include' in query_params:
                query_params['include'] += ',resources'
            else:
                query_params['include'] = 'resources'
        
        # Make request to list state versions
        endpoint = f"/workspaces/{workspace_id}/state-versions"
        return self._handle_pagination('GET', endpoint, params, query_params)

    def _wait_for_state_version_processing(self, state_version_id, timeout):
        """Wait for a state version to be fully processed."""
        start_time = time.time()
        polling_interval = 2
        
        display.vvv(f"Waiting for state version {state_version_id} to be processed (timeout: {timeout}s)")
        
        while time.time() - start_time < timeout:
            result = self._get_state_version_by_id(state_version_id, {})
            
            if result.get('data', {}).get('attributes', {}).get('resources-processed', False):
                display.vvv(f"State version {state_version_id} processing completed")
                return result
            
            display.vvv(f"State version {state_version_id} still processing, waiting {polling_interval}s...")
            time.sleep(polling_interval)
            
            # Increase polling interval with a cap
            polling_interval = min(polling_interval * 1.5, 10)
        
        raise AnsibleError(f"Timeout waiting for state version {state_version_id} to be processed")

    def _get_workspace_id(self, organization, workspace_name):
        """Get the workspace ID from organization and workspace name."""
        try:
            endpoint = f"/organizations/{organization}/workspaces/{workspace_name}"
            response = self._make_request('GET', endpoint, variables={'token': self._get_auth_token({})})
            if 'data' in response and 'id' in response['data']:
                return response['data']['id']
            else:
                raise AnsibleError(f"Could not find workspace '{workspace_name}' in organization '{organization}'.")
        except Exception as e:
            raise AnsibleError(f"Error retrieving workspace ID: {str(e)}")

    def _handle_pagination(self, method, endpoint, variables, params=None):
        """Handle paginated API responses."""
        params = params or {}
        
        # Set initial page parameters
        if 'page[number]' not in params:
            params['page[number]'] = 1
        if 'page[size]' not in params:
            params['page[size]'] = 100
        
        # Get first page
        response = self._make_request(method, endpoint, variables, params)
        
        # If there's no pagination info, just return the response
        if 'meta' not in response or 'pagination' not in response['meta']:
            return response
        
        pagination = response['meta']['pagination']
        total_pages = pagination.get('total-pages', 1)
        
        # If there's only one page, return the response
        if total_pages <= 1:
            return response
        
        # Otherwise, fetch all pages and combine the data
        all_data = response.get('data', [])
        
        for page in range(2, total_pages + 1):
            params['page[number]'] = page
            page_response = self._make_request(method, endpoint, variables, params)
            if 'data' in page_response:
                all_data.extend(page_response['data'])
        
        # Create a combined response
        combined_response = {
            'data': all_data,
            'meta': response.get('meta', {})
        }
        
        # Update pagination info
        if 'meta' in combined_response and 'pagination' in combined_response['meta']:
            combined_response['meta']['pagination']['current-page'] = 1
            combined_response['meta']['pagination']['total-count'] = len(all_data)
        
        return combined_response

if __name__ == '__main__':
    # For testing purposes only
    lookup = LookupModule()
    print(lookup.run([], {}))