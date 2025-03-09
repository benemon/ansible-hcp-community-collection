DOCUMENTATION = r"""
    name: hcp_terraform_variable_sets
    author: benemon
    version_added: "0.0.7"
    short_description: List variable sets from HCP Terraform
    description:
        - This lookup returns variable sets from HCP Terraform
        - Variable sets allow reusing variables across multiple workspaces and projects
        - Results can be filtered by organization, project, or workspace
    options:
        token:
            description:
                - HCP Terraform API token
                - Can be specified via TFE_TOKEN environment variable
            required: true
            type: str
            env:
                - name: TFE_TOKEN
        hostname:
            description:
                - HCP Terraform API hostname
                - Can be specified via TFE_HOSTNAME environment variable
                - Defaults to https://app.terraform.io
            required: false
            type: str
            default: "https://app.terraform.io"
            env:
                - name: TFE_HOSTNAME
        organization:
            description:
                - Name of the organization to list variable sets for
                - Required if listing organization-scoped variable sets
            required: false
            type: str
        project_id:
            description:
                - ID of the project to list variable sets for
                - If specified, returns variable sets for this project
            required: false
            type: str
        workspace_id:
            description:
                - ID of the workspace to list variable sets for
                - If specified, returns variable sets for this workspace
            required: false
            type: str
        page_size:
            description: 
                - Number of results to return per page
                - Default is determined by the API
            required: false
            type: int
        max_pages:
            description:
                - Maximum number of pages to retrieve
                - If not specified, all pages will be retrieved
            required: false
            type: int
        disable_pagination:
            description: 
                - If True, returns only the first page of results
            required: false
            type: bool
            default: false
        name:
            description:
                - Filter variable sets by name (case-sensitive)
                - This is a client-side filter applied after retrieving results
            required: false
            type: str
        id:
            description:
                - Fetch a specific variable set by ID
                - If specified, other filters are ignored
            required: false
            type: str
        q:
            description:
                - Search query to filter variable sets
                - This is passed directly to the API as a query parameter
            required: false
            type: str
    notes:
        - Authentication requires a valid HCP Terraform API token
        - One of organization, project_id, workspace_id, or id must be specified
        - Variable sets can be scoped to an organization, project, or workspace
        - Returns raw API response from HCP Terraform
    seealso:
        - module: benemon.hcp_community_collection.hcp_terraform_variable_set
        - name: Terraform API Documentation
          link: https://developer.hashicorp.com/terraform/cloud-docs/api-docs/variable-sets
"""

EXAMPLES = r"""
# List all variable sets for an organization
- name: Get organization variable sets
  ansible.builtin.debug:
    msg: "{{ lookup('benemon.hcp_community_collection.hcp_terraform_variable_sets', 
            organization='my-organization') }}"

# List variable sets for a specific project
- name: Get project variable sets
  ansible.builtin.debug:
    msg: "{{ lookup('benemon.hcp_community_collection.hcp_terraform_variable_sets',
            project_id='prj-123456') }}"

# List variable sets for a specific workspace
- name: Get workspace variable sets
  ansible.builtin.debug:
    msg: "{{ lookup('benemon.hcp_community_collection.hcp_terraform_variable_sets',
            workspace_id='ws-123456') }}"

# Get a specific variable set by ID
- name: Get variable set by ID
  ansible.builtin.debug:
    msg: "{{ lookup('benemon.hcp_community_collection.hcp_terraform_variable_sets',
            id='varset-123456') }}"

# Filter variable sets by name
- name: Get variable sets with a specific name
  ansible.builtin.debug:
    msg: "{{ lookup('benemon.hcp_community_collection.hcp_terraform_variable_sets',
            organization='my-organization',
            name='AWS Credentials') }}"

# Search for variable sets using the API search functionality
- name: Search for variable sets containing "AWS"
  ansible.builtin.debug:
    msg: "{{ lookup('benemon.hcp_community_collection.hcp_terraform_variable_sets',
            organization='my-organization',
            q='AWS') }}"

# Extract specific fields from the result
- name: Get variable set IDs and names
  ansible.builtin.set_fact:
    varsets: "{{ lookup('benemon.hcp_community_collection.hcp_terraform_variable_sets',
                organization='my-organization').data | 
                map('combine', {'name': item.attributes.name, 'id': item.id}) | list }}"
  vars:
    item: "{{ item }}"
"""

from ansible.errors import AnsibleError
from ansible.utils.display import Display
from ansible_collections.benemon.hcp_community_collection.plugins.module_utils.hcp_terraform_lookup import HCPTerraformLookup

display = Display()

class LookupModule(HCPTerraformLookup):
  def run(self, terms, variables=None, **kwargs):
      """Retrieve variable sets from HCP Terraform."""
      variables = variables or {}
      
      # Process parameters
      params = self._parse_parameters(terms, variables)
      
      # Set hostname for base URL
      self.base_url = self._get_hostname(params)
      
      try:
          # Initialize query_params
          query_params = {}
          
          # Add search query if present
          if 'q' in params:
              query_params['q'] = params['q']
          
          # Determine the endpoint based on the specified scope
          if params.get('id'):
              # Specific variable set by ID
              endpoint = f"varsets/{params['id']}"
              
          elif params.get('organization'):
              # Organization-level variable sets
              endpoint = f"organizations/{params['organization']}/varsets"
              
          elif params.get('project_id'):
              # Project-level variable sets
              endpoint = f"projects/{params['project_id']}/varsets"
              
          elif params.get('workspace_id'):
              # Workspace-level variable sets
              endpoint = f"workspaces/{params['workspace_id']}/varsets"
              
          else:
              raise AnsibleError("One of 'organization', 'project_id', 'workspace_id', or 'id' must be specified")
          
          display.vvv(f"Looking up variable sets from endpoint: {endpoint}")
          
          # Handle name filter (client-side)
          name_filter = params.get('name')
          
          # Use the pagination handler from the base class
          results = self._handle_pagination(endpoint, params, query_params)
          
          # Apply client-side name filtering if specified
          if name_filter and 'data' in results and isinstance(results['data'], list):
              filtered_data = [
                  varset for varset in results['data']
                  if 'attributes' in varset and 
                  'name' in varset['attributes'] and 
                  varset['attributes']['name'] == name_filter
              ]
              results['data'] = filtered_data
          
          # Return the raw results, preserving the original structure
          display.vvv(f"Successfully retrieved variable sets response")
          return [results]
          
      except Exception as e:
          display.error(f"Error retrieving variable sets: {str(e)}")
          raise AnsibleError(f"Error retrieving variable sets: {str(e)}")