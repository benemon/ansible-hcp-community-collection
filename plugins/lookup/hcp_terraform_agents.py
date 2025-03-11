#!/usr/bin/python
DOCUMENTATION = r"""
    name: hcp_terraform_agents
    author: benemon
    version_added: "0.0.7"
    short_description: List agents for HCP Terraform agent pools
    description:
        - This lookup returns agents from a specified HCP Terraform agent pool.
        - Agents are hosted processes that can execute Terraform runs from workspaces in 'agent' execution mode.
        - Results are filtered by agent pool ID and can be further filtered by ping time.
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
        agent_pool_id:
            description:
                - ID of the agent pool to list agents from.
                - Required to retrieve agents.
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
        last_ping_since:
            description:
                - Filter agents by their last ping time.
                - Only returns agents that pinged after the specified time.
                - Format should be ISO8601 (e.g., 2020-08-11T10:41:23Z).
            required: false
            type: str
        status:
            description:
                - Client-side filter to return only agents with the specified status.
                - Possible values are 'idle', 'busy', 'errored', or 'exited'.
            required: false
            type: str
            choices: ['idle', 'busy', 'errored', 'exited']
    notes:
        - Authentication requires a valid HCP Terraform API token.
        - Agent status can be 'idle' (ready to run jobs), 'busy' (currently running a job), 'errored' (unable to run jobs), or 'exited' (no longer connected).
        - Returns raw API response from HCP Terraform.
    seealso:
        - module: benemon.hcp_community_collection.hcp_terraform_agent_token
        - module: benemon.hcp_community_collection.hcp_terraform_agent_pool
        - name: Terraform API Documentation
          link: https://developer.hashicorp.com/terraform/cloud-docs/api-docs/agents
"""

EXAMPLES = r"""
# List all agents for a specific agent pool
- name: Get agents for an agent pool
  ansible.builtin.debug:
    msg: "{{ lookup('benemon.hcp_community_collection.hcp_terraform_agents', agent_pool_id='apool-xkuMi7x4LsEnBUdY') }}"

# List agents that have pinged since a specific time
- name: Get agents that have pinged recently
  ansible.builtin.debug:
    msg: "{{ lookup('benemon.hcp_community_collection.hcp_terraform_agents', 
            token='your_terraform_token',
            agent_pool_id='apool-xkuMi7x4LsEnBUdY',
            last_ping_since='2023-01-01T00:00:00Z') }}"

# Filter agents by status using client-side filtering
- name: Get idle agents
  ansible.builtin.set_fact:
    idle_agents: "{{ lookup('benemon.hcp_community_collection.hcp_terraform_agents',
                    agent_pool_id='apool-xkuMi7x4LsEnBUdY')._raw.data | 
                    selectattr('attributes.status', 'equalto', 'idle') | list }}"

# Extract agent names and IDs
- name: Get a list of agent names and IDs
  ansible.builtin.set_fact:
    agents: "{{ lookup('benemon.hcp_community_collection.hcp_terraform_agents',
                agent_pool_id='apool-xkuMi7x4LsEnBUdY')._raw.data | 
                map('combine', {'name': item.attributes.name, 'id': item.id, 'status': item.attributes.status}) | list }}"
  vars:
    item: "{{ item }}"

# Count agents by status
- name: Count agents by status
  ansible.builtin.set_fact:
    agent_counts: "{{ lookup('benemon.hcp_community_collection.hcp_terraform_agents',
                     agent_pool_id='apool-xkuMi7x4LsEnBUdY')._raw.data | 
                     groupby('attributes.status') | 
                     map('combine', {'status': item[0], 'count': item[1] | length}) | list }}"
  vars:
    item: "{{ item }}"
"""

RETURN = r"""
  _raw:
    description: Raw API response from HCP Terraform containing agent information.
    type: dict
    contains:
      data:
        description: List of agent objects.
        type: list
        elements: dict
        contains:
          id:
            description: The ID of the agent.
            type: str
            sample: "agent-A726QeosTCpCumAs"
          type:
            description: The type of resource (always 'agents').
            type: str
            sample: "agents"
          attributes:
            description: Agent attributes.
            type: dict
            contains:
              name:
                description: The name of the agent.
                type: str
                sample: "my-cool-agent"
              status:
                description: The status of the agent (idle, busy, errored, or exited).
                type: str
                sample: "idle"
              ip-address:
                description: The IP address of the agent.
                type: str
                sample: "123.123.123.123"
              last-ping-at:
                description: When the agent last pinged the service.
                type: str
                sample: "2020-10-09T18:52:25.246Z"
          links:
            description: URL links related to this agent.
            type: dict
            sample: {"self": "/api/v2/agents/agent-A726QeosTCpCumAs"}
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
                sample: 1
"""

from ansible.errors import AnsibleError
from ansible.utils.display import Display
from ansible_collections.benemon.hcp_community_collection.plugins.module_utils.hcp_terraform_lookup import HCPTerraformLookup

display = Display()

class LookupModule(HCPTerraformLookup):
    def run(self, terms, variables=None, **kwargs):
        """Retrieve agents from an HCP Terraform agent pool."""
        variables = variables or {}
        
        # Process parameters
        params = self._parse_parameters(terms, variables)
        
        # Set hostname for base URL
        self.base_url = self._get_hostname(params)
        
        # Validate required parameters
        required_params = ['agent_pool_id']
        self._validate_params(params, required_params)
        
        # Get agent pool ID
        agent_pool_id = params['agent_pool_id']
        
        # Build endpoint
        endpoint = f"agent-pools/{agent_pool_id}/agents"
        
        display.vvv(f"Looking up agents for agent pool {agent_pool_id}")
        
        try:
            # Build query parameters
            query_params = {}
            
            # Add last ping since filter if provided
            if 'last_ping_since' in params:
                query_params['filter[last-ping-since]'] = params['last_ping_since']
            
            # Use the pagination handler from the base class to retrieve results
            results = self._handle_pagination(endpoint, params, query_params)
            
            # Apply client-side status filtering if specified
            status_filter = params.get('status')
            if status_filter and 'data' in results:
                filtered_data = [
                    agent for agent in results['data']
                    if 'attributes' in agent and 
                    'status' in agent['attributes'] and 
                    agent['attributes']['status'] == status_filter
                ]
                results['data'] = filtered_data
            
            # Return the raw results, preserving the original structure
            display.vvv("Successfully retrieved agents response")
            return [results]
        except Exception as e:
            display.error(f"Error retrieving agents: {str(e)}")
            raise AnsibleError(f"Error retrieving agents: {str(e)}")

if __name__ == '__main__':
    # For testing purposes, you can invoke the lookup module from the command line.
    lookup = LookupModule()
    result = lookup.run([], {})
    print(result)