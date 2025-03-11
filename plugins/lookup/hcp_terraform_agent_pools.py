#!/usr/bin/python
DOCUMENTATION = r"""
    name: hcp_terraform_agent_pools
    author: benemon
    version_added: "0.0.7"
    short_description: List agent pools for HCP Terraform with server-side filtering
    description:
        - This lookup returns agent pools from HCP Terraform.
        - Agent pools are used to group agents that can be used for workspace execution in 'agent' mode.
        - Results can be filtered by organization and further refined using the 'q' parameter for server-side filtering.
        - Can also filter by allowed workspaces to see which agent pools a specific workspace can use.
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
                - Name of the organization to filter agent pools for.
                - Required to list agent pools for a specific organization.
            required: true
            type: str
        page_size:
            description: 
                - Number of results to return per page.
                - Default is determined by the API.
            required: false
            type: int
        max_pages:
            description:
                - Maximum number of pages to retrieve.
                - If not specified, all pages will be retrieved.
            required: false
            type: int
        disable_pagination:
            description: 
                - If True, returns only the first page of results.
            required: false
            type: bool
            default: false
        name:
            description:
                - Client-side filter to return only agent pools with an exact matching name (case-sensitive).
            required: false
            type: str
        q:
            description:
                - Server-side search query to filter agent pools.
                - This query is passed directly to the API endpoint for filtering.
            required: false
            type: str
        sort:
            description:
                - Field to sort the results by.
                - Valid values are "name" and "created-at".
                - Prepend with a hyphen for descending order (e.g., "-name").
            required: false
            type: str
            choices: ["name", "created-at", "-name", "-created-at"]
        allowed_workspace_name:
            description:
                - Filter agent pools to those associated with the given workspace.
                - The workspace must have permission to use the agent pool.
            required: false
            type: str
    notes:
        - Authentication requires a valid HCP Terraform API token.
        - Agent pools are organization-specific.
        - Returns raw API response from HCP Terraform.
    seealso:
        - module: benemon.hcp_community_collection.hcp_terraform_agent_pool
        - module: benemon.hcp_community_collection.hcp_terraform_workspace
        - name: Terraform API Documentation
          link: https://developer.hashicorp.com/terraform/cloud-docs/api-docs/agent-pools
"""

EXAMPLES = r"""
# List all agent pools for an organization
- name: Get agent pools for an organization
  ansible.builtin.debug:
    msg: "{{ lookup('benemon.hcp_community_collection.hcp_terraform_agent_pools', organization='my-organization') }}"

# List agent pools using server-side filtering with a search query
- name: Get agent pools using server-side filtering
  ansible.builtin.debug:
    msg: "{{ lookup('benemon.hcp_community_collection.hcp_terraform_agent_pools', 
            token='your_terraform_token',
            hostname='https://app.terraform.io',
            organization='my-organization',
            q='prod') }}"

# Get agent pool ID by filtering with a client-side name filter
- name: Get agent pool ID for a pool with an exact name
  ansible.builtin.set_fact:
    agent_pool_id: "{{ lookup('benemon.hcp_community_collection.hcp_terraform_agent_pools',
                      organization='my-organization',
                      name='Production Agents')._raw.data | 
                      selectattr('attributes.name', 'equalto', 'Production Agents') | 
                      map(attribute='id') | first }}"

# Get agent pools that a specific workspace is allowed to use
- name: Get agent pools available to a workspace
  ansible.builtin.debug:
    msg: "{{ lookup('benemon.hcp_community_collection.hcp_terraform_agent_pools',
            organization='my-organization',
            allowed_workspace_name='my-workspace') }}"

# Sort agent pools by name in descending order
- name: Get agent pools sorted by name (Z to A)
  ansible.builtin.debug:
    msg: "{{ lookup('benemon.hcp_community_collection.hcp_terraform_agent_pools',
            organization='my-organization',
            sort='-name') }}"

# Extract specific fields using a comprehension
- name: Get a list of agent pool names and IDs
  ansible.builtin.set_fact:
    agent_pools: "{{ lookup('benemon.hcp_community_collection.hcp_terraform_agent_pools',
                    organization='my-organization')._raw.data | 
                    map('combine', {'name': item.attributes.name, 'id': item.id}) | list }}"
  vars:
    item: "{{ item }}"
"""

RETURN = r"""
  _raw:
    description: Raw API response from HCP Terraform containing agent pool information.
    type: dict
    contains:
      data:
        description: List of agent pool objects.
        type: list
        elements: dict
        contains:
          id:
            description: The ID of the agent pool.
            type: str
            sample: "apool-yoGUFz5zcRMMz53i"
          type:
            description: The type of resource (always 'agent-pools').
            type: str
            sample: "agent-pools"
          attributes:
            description: Agent pool attributes.
            type: dict
            contains:
              name:
                description: The name of the agent pool.
                type: str
                sample: "example-pool"
              organization-scoped:
                description: Whether the agent pool is available to all workspaces in the organization.
                type: bool
                sample: false
              created-at:
                description: When the agent pool was created.
                type: str
                sample: "2020-08-05T18:10:26.964Z"
              agent-count:
                description: Number of agents in the pool.
                type: int
                sample: 3
          relationships:
            description: Related resources.
            type: dict
            contains:
              agents:
                description: Link to the agents in this pool.
                type: dict
              authentication-tokens:
                description: Link to the authentication tokens for this pool.
                type: dict
              workspaces:
                description: The workspaces using this agent pool.
                type: dict
              allowed-workspaces:
                description: The workspaces allowed to use this agent pool.
                type: dict
          links:
            description: URL links related to this agent pool.
            type: dict
            sample: {"self": "/api/v2/agent-pools/apool-yoGUFz5zcRMMz53i"}
      links:
        description: Pagination links (if applicable).
        type: dict
      meta:
        description: Metadata about the response (if applicable).
        type: dict
        contains:
          pagination:
            description: Pagination information.
            type: dict
            contains:
              current-page:
                description: Current page number.
                type: int
                sample: 1
              total-pages:
                description: Total number of pages.
                type: int
                sample: 3
"""

from ansible.errors import AnsibleError
from ansible.utils.display import Display
from ansible_collections.benemon.hcp_community_collection.plugins.module_utils.hcp_terraform_lookup import HCPTerraformLookup

display = Display()

class LookupModule(HCPTerraformLookup):
    def run(self, terms, variables=None, **kwargs):
        """Retrieve agent pools from HCP Terraform."""
        variables = variables or {}
        
        # Process parameters
        params = self._parse_parameters(terms, variables)
        
        # Set hostname for base URL
        self.base_url = self._get_hostname(params)
        
        # Validate required parameters
        required_params = ['organization']
        self._validate_params(params, required_params)
        
        # Build endpoint using the provided organization
        organization = params['organization']
        endpoint = f"organizations/{organization}/agent-pools"
        
        display.vvv(f"Looking up agent pools for organization {organization}")
        
        try:
            # Build query parameters
            query_params = {}
            
            # Add server-side search query if provided
            if 'q' in params:
                query_params['q'] = params['q']
            
            # Add sorting if provided
            if 'sort' in params:
                query_params['sort'] = params['sort']
            
            # Add allowed workspace filter if provided
            if 'allowed_workspace_name' in params:
                query_params['filter[allowed_workspaces][name]'] = params['allowed_workspace_name']
            
            # Retrieve client-side name filter if provided
            name_filter = params.get('name')
            
            # Use the pagination handler from the base class to retrieve results
            results = self._handle_pagination(endpoint, params, query_params)
            
            # Apply client-side name filtering if specified
            if name_filter and 'data' in results:
                filtered_data = [
                    agent_pool for agent_pool in results['data']
                    if 'attributes' in agent_pool and 
                    'name' in agent_pool['attributes'] and 
                    agent_pool['attributes']['name'] == name_filter
                ]
                results['data'] = filtered_data
            
            # Return the raw results, preserving the original structure
            display.vvv("Successfully retrieved agent pools response")
            return [results]
        except Exception as e:
            display.error(f"Error retrieving agent pools: {str(e)}")
            raise AnsibleError(f"Error retrieving agent pools: {str(e)}")

if __name__ == '__main__':
    # For testing purposes, you can invoke the lookup module from the command line.
    lookup = LookupModule()
    result = lookup.run([], {})
    print(result)