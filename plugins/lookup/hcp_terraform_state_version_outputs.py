#!/usr/bin/python
DOCUMENTATION = r"""
    name: hcp_terraform_state_version_outputs
    author: benemon
    version_added: "0.0.7"
    short_description: Retrieve output values from Terraform state versions in HCP Terraform
    description:
        - This lookup returns output values from state versions in HCP Terraform workspaces.
        - It can be used to retrieve all outputs or filter to specific outputs by name.
        - Sensitive values may be returned as null unless you have proper permissions.
    options:
        token:
            description:
                - HCP Terraform API token.
                - Can be specified via TFE_TOKEN environment variable.
            required: true
            type: str
            env:
                - name: TFE_TOKEN
        hostname:
            description:
                - HCP Terraform API hostname.
                - Can be specified via TFE_HOSTNAME environment variable.
                - Defaults to https://app.terraform.io.
            required: false
            type: str
            default: "https://app.terraform.io"
            env:
                - name: TFE_HOSTNAME
        organization:
            description:
                - Name of the organization containing the workspace.
                - Required when workspace_name is used and not retrieving outputs by state_version_id.
            required: false
            type: str
        workspace_name:
            description:
                - Name of the workspace to retrieve outputs from.
                - Either workspace_name with organization, or workspace_id must be provided if not retrieving outputs by state_version_id.
            required: false
            type: str
        workspace_id:
            description:
                - ID of the workspace to retrieve outputs from.
                - Alternative to providing organization and workspace_name.
            required: false
            type: str
        state_version_id:
            description:
                - ID of a specific state version to retrieve outputs from.
                - If specified, uses this state version rather than the current one.
            required: false
            type: str
        output_id:
            description:
                - ID of a specific output to retrieve.
                - If specified, only that output is retrieved.
            required: false
            type: str
        output_name:
            description:
                - Name of a specific output to retrieve.
                - If specified, only returns the value of the output with this name.
            required: false
            type: str
        raw_output:
            description:
                - If True, returns the raw API response.
                - If False, returns a simplified dict of output names and values.
            required: false
            type: bool
            default: false
        page_size:
            description: 
                - Number of results to return per page when listing outputs.
            required: false
            type: int
        max_pages:
            description:
                - Maximum number of pages to retrieve when listing outputs.
                - If not specified, all pages will be retrieved.
            required: false
            type: int
        disable_pagination:
            description: 
                - If True, returns only the first page of results when listing outputs.
            required: false
            type: bool
            default: false
        wait_for_processing:
            description:
                - Whether to wait for HCP Terraform to finish processing the state version.
                - State version outputs might not be immediately available after upload.
            required: false
            type: bool
            default: false
        wait_timeout:
            description:
                - Maximum time in seconds to wait for state processing to complete.
                - Only applies when wait_for_processing is True.
            required: false
            type: int
            default: 120
    notes:
        - Authentication requires a valid HCP Terraform API token.
        - State version outputs might not be immediately available after a state version is uploaded.
        - Sensitive values will be returned as null unless you have proper permissions.
    seealso:
        - name: Terraform API Documentation - State Version Outputs
          link: https://developer.hashicorp.com/terraform/cloud-docs/api-docs/state-version-outputs
        - module: benemon.hcp_community_collection.hcp_terraform_state_versions
"""

EXAMPLES = r"""
# Get all outputs from the current state version of a workspace
- name: Get all outputs from a workspace
  ansible.builtin.debug:
    msg: "{{ lookup('benemon.hcp_community_collection.hcp_terraform_state_version_outputs', 
            organization='my-organization',
            workspace_name='my-workspace') }}"

# Get all outputs from the current state version of a workspace by ID
- name: Get all outputs using workspace ID
  ansible.builtin.debug:
    msg: "{{ lookup('benemon.hcp_community_collection.hcp_terraform_state_version_outputs', 
            workspace_id='ws-abcd1234') }}"

# Get outputs from a specific state version
- name: Get outputs from specific state version
  ansible.builtin.debug:
    msg: "{{ lookup('benemon.hcp_community_collection.hcp_terraform_state_version_outputs', 
            state_version_id='sv-abcd1234') }}"

# Get a specific output by name
- name: Get a specific output
  ansible.builtin.debug:
    msg: "VPC ID: {{ lookup('benemon.hcp_community_collection.hcp_terraform_state_version_outputs', 
                    organization='my-organization',
                    workspace_name='my-workspace',
                    output_name='vpc_id') }}"

# Get a specific output by ID
- name: Get a specific output by ID
  ansible.builtin.debug:
    msg: "{{ lookup('benemon.hcp_community_collection.hcp_terraform_state_version_outputs', 
            output_id='wsout-abcd1234') }}"

# Get raw API response with full output details
- name: Get raw output data
  ansible.builtin.debug:
    msg: "{{ lookup('benemon.hcp_community_collection.hcp_terraform_state_version_outputs', 
            organization='my-organization',
            workspace_name='my-workspace',
            raw_output=true) }}"

# Set outputs as variables for later use
- name: Get all outputs and store as variables
  ansible.builtin.set_fact:
    terraform_outputs: "{{ lookup('benemon.hcp_community_collection.hcp_terraform_state_version_outputs', 
                          organization='my-organization',
                          workspace_name='my-workspace') }}"

# Use the stored output variables
- name: Use output variables
  ansible.builtin.debug:
    msg: "The subnet IDs are {{ terraform_outputs.subnet_ids }}"

# Wait for state processing to complete before getting outputs
- name: Get outputs with processing wait
  ansible.builtin.debug:
    msg: "{{ lookup('benemon.hcp_community_collection.hcp_terraform_state_version_outputs', 
            organization='my-organization',
            workspace_name='my-workspace',
            wait_for_processing=true) }}"
"""

RETURN = r"""
  _raw:
    description: Output values from the state version.
    type: dict
    sample: {"vpc_id": "vpc-12345", "subnet_ids": ["subnet-1", "subnet-2"]}
    returned: When raw_output=false and output_name is not specified
  _raw:
    description: A single output value.
    type: raw
    sample: "vpc-12345"
    returned: When output_name is specified and the output exists
  _raw:
    description: Raw API response containing full output details.
    type: dict
    returned: When raw_output=true
    contains:
      data:
        description: List of output objects or a single output object.
        type: list or dict
        contains:
          id:
            description: The ID of the output.
            type: str
            sample: "wsout-abcd1234"
          type:
            description: The type of resource.
            type: str
            sample: "state-version-outputs"
          attributes:
            description: Output attributes.
            type: dict
            contains:
              name:
                description: The name of the output.
                type: str
                sample: "vpc_id"
              sensitive:
                description: Whether the output is sensitive.
                type: bool
                sample: false
              type:
                description: The data type of the output.
                type: str
                sample: "string"
              value:
                description: The output value.
                type: raw
                sample: "vpc-12345"
              detailed-type:
                description: Detailed type information.
                type: str or list
                sample: "string"
          links:
            description: Links related to this output.
            type: dict
            sample: {"self": "/api/v2/state-version-outputs/wsout-abcd1234"}
"""

from ansible.errors import AnsibleError
from ansible.utils.display import Display
from ansible_collections.benemon.hcp_community_collection.plugins.module_utils.hcp_terraform_lookup import HCPTerraformLookup
import time

display = Display()

class LookupModule(HCPTerraformLookup):
    def run(self, terms, variables=None, **kwargs):
        """Retrieve state version outputs from HCP Terraform."""
        variables = variables or {}
        
        # Process parameters
        params = self._parse_parameters(terms, variables)
        
        # Set hostname for base URL
        self.base_url = self._get_hostname(params)
        
        try:
            # Determine how to look up the outputs
            if 'output_id' in params:
                # Get a specific output by ID
                result = self._get_output_by_id(params['output_id'], params)
                
                # If raw_output is not requested and this is a single output, return just the value
                if not params.get('raw_output', False):
                    return [result.get('data', {}).get('attributes', {}).get('value')]
                return [result]
            
            # Get workspace_id from organization and workspace_name if provided
            workspace_id = None
            if 'organization' in params and 'workspace_name' in params and 'workspace_id' not in params:
                workspace_id = self._get_workspace_id(params['organization'], params['workspace_name'])
            elif 'workspace_id' in params:
                workspace_id = params['workspace_id']
            
            # Get by state_version_id or workspace_id
            if 'state_version_id' in params:
                # Check if we need to wait for processing
                if params.get('wait_for_processing', False):
                    self._wait_for_state_version_if_needed(params['state_version_id'], params.get('wait_timeout', 120))
                
                # Get all outputs for a state version
                result = self._get_outputs_by_state_version(params['state_version_id'], params)
            elif workspace_id:
                # Get outputs from current state version of a workspace
                result = self._get_current_state_version_outputs(workspace_id, params)
            else:
                raise AnsibleError("Either output_id, state_version_id, or workspace_id (or organization and workspace_name) must be provided.")
        
        
            
            # If a specific output name is requested, return just that output's value
            if 'output_name' in params and not params.get('raw_output', False):
                output_name = params['output_name']
                for output in result.get('data', []):
                    if output.get('attributes', {}).get('name') == output_name:
                        return [output.get('attributes', {}).get('value')]
                
                # If we get here, the output wasn't found
                raise AnsibleError(f"Output '{output_name}' not found in state version outputs.")
            
            # Return either raw response or processed output values
            if params.get('raw_output', False):
                return [result]
            else:
                # Convert to a simple dictionary of name:value pairs
                output_dict = {}
                for output in result.get('data', []):
                    attrs = output.get('attributes', {})
                    output_dict[attrs.get('name')] = attrs.get('value')
                return [output_dict]
        except Exception as e:
            display.error(f"Error retrieving state version outputs: {str(e)}")
            raise AnsibleError(f"Error retrieving state version outputs: {str(e)}")

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

    def _get_output_by_id(self, output_id, params):
        """Get a specific output by ID."""
        try:
            endpoint = f"/state-version-outputs/{output_id}"
            return self._make_request('GET', endpoint, variables={'token': self._get_auth_token({})})
        except Exception as e:
            raise AnsibleError(f"Error retrieving output {output_id}: {str(e)}")

    def _get_outputs_by_state_version(self, state_version_id, params):
        """Get outputs from a specific state version."""
        try:
            endpoint = f"/state-versions/{state_version_id}/outputs"
            
            # If we need to wait for processing, check the state version first
            if params.get('wait_for_processing', False):
                self._wait_for_state_version_if_needed(state_version_id, params.get('wait_timeout', 120))
            
            # Handle pagination for the outputs
            query_params = {}
            return self._handle_pagination(endpoint, params, query_params)
        except Exception as e:
            raise AnsibleError(f"Error retrieving outputs for state version {state_version_id}: {str(e)}")

    def _get_current_state_version_outputs(self, workspace_id, params):
        """Get outputs from the current state version of a workspace."""
        try:
            endpoint = f"/workspaces/{workspace_id}/current-state-version-outputs"
            
            # If we need to wait for processing, get the current state version first
            if params.get('wait_for_processing', False):
                current_state_version = self._get_current_state_version(workspace_id, params)
                if current_state_version and 'data' in current_state_version and 'id' in current_state_version['data']:
                    state_version_id = current_state_version['data']['id']
                    self._wait_for_state_version_if_needed(state_version_id, params.get('wait_timeout', 120), params)
            
            # Handle pagination for the outputs - pass the params with token
            query_params = {}
            return self._handle_pagination(endpoint, params, query_params)
        except Exception as e:
            raise AnsibleError(f"Error retrieving current state version outputs for workspace {workspace_id}: {str(e)}")

    def _get_current_state_version(self, workspace_id, params):
        """Get the current state version for a workspace."""
        try:
            endpoint = f"/workspaces/{workspace_id}/current-state-version"
            # Make sure to use the token from params correctly
            return self._make_request('GET', endpoint, variables={'token': self._get_auth_token(params)})
        except Exception as e:
            if "404" in str(e) or "not found" in str(e).lower():
                # No current state version, return None
                return None
            raise AnsibleError(f"Error retrieving current state version for workspace {workspace_id}: {str(e)}")
    
    def _wait_for_state_version_if_needed(self, state_version_id, timeout, params):
        """Wait for a state version to be fully processed if it's not already."""
        try:
            endpoint = f"/state-versions/{state_version_id}"
            state_version = self._make_request('GET', endpoint, variables={'token': self._get_auth_token(params)})
            
            # Check if resources-processed is false
            if not state_version.get('data', {}).get('attributes', {}).get('resources-processed', True):
                display.vvv(f"State version {state_version_id} needs processing, waiting...")
                return self._wait_for_state_version_processing(state_version_id, timeout, params)
            else:
                display.vvv(f"State version {state_version_id} already processed, no waiting needed")
                return state_version
        except Exception as e:
            raise AnsibleError(f"Error checking state version processing: {str(e)}")

    def _wait_for_state_version_processing(self, state_version_id, timeout):
        """Wait for a state version to be fully processed."""
        start_time = time.time()
        
        display.vvv(f"Waiting for state version {state_version_id} processing to complete")
        
        while True:
            # Check if we've exceeded the timeout
            if time.time() - start_time > timeout:
                raise AnsibleError(f"Timeout waiting for state version {state_version_id} processing to complete")
            
            try:
                # Get the state version
                endpoint = f"/state-versions/{state_version_id}"
                state_version = self._make_request('GET', endpoint, variables={'token': self._get_auth_token({})})
                
                # Check if processing is complete
                if state_version.get('data', {}).get('attributes', {}).get('resources-processed', False):
                    return state_version
            except Exception as e:
                # Ignore errors and keep trying until timeout
                display.vvv(f"Error checking state version processing: {str(e)}")
            
            # Wait before trying again
            time.sleep(5)

if __name__ == '__main__':
    # For testing purposes only
    lookup = LookupModule()
    print(lookup.run([], {}))