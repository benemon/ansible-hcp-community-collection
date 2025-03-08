DOCUMENTATION = r"""
    name: hcp_terraform_projects
    author: benemon
    version_added: "0.0.7"
    short_description: List projects for HCP Terraform
    description:
        - This lookup returns projects from HCP Terraform
        - Projects are used to organize workspaces within organizations
        - Results can be filtered by organization ID
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
                - Name of the organization to filter projects for
                - Required to list projects for a specific organization
            required: true
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
                - Filter projects by name (case-sensitive)
                - This is a client-side filter applied after retrieving results
            required: false
            type: str
    notes:
        - Authentication requires a valid HCP Terraform API token
        - Projects are organization-specific
        - Returns raw API response from HCP Terraform
    seealso:
        - module: benemon.hcp_community_collection.hcp_terraform_workspace
        - name: Terraform API Documentation
          link: https://developer.hashicorp.com/terraform/cloud-docs/api-docs/projects
"""

EXAMPLES = r"""
# List all projects for an organization
- name: Get projects
  ansible.builtin.debug:
    msg: "{{ lookup('benemon.hcp_community_collection.hcp_terraform_projects', 
            organization='my-organization') }}"

# List projects with explicit token and hostname
- name: Get projects with specific credentials
  ansible.builtin.debug:
    msg: "{{ lookup('benemon.hcp_community_collection.hcp_terraform_projects',
            token='your_terraform_token',
            hostname='https://app.terraform.io',
            organization='my-organization') }}"

# Get project ID and use it in workspace creation
- name: Get project ID
  ansible.builtin.set_fact:
    project_id: "{{ lookup('benemon.hcp_community_collection.hcp_terraform_projects',
                  organization='my-organization',
                  name='My Project').data | selectattr('attributes.name', 'equalto', 'My Project') | map(attribute='id') | first }}"

- name: Create workspace in project
  benemon.hcp_community_collection.hcp_terraform_workspace:
    name: "new-workspace"
    organization: "my-organization"
    project_id: "{{ project_id }}"

# Extract specific fields using a comprehension
- name: Get a list of project names and IDs
  ansible.builtin.set_fact:
    projects: "{{ lookup('benemon.hcp_community_collection.hcp_terraform_projects',
                organization='my-organization').data | 
                map('combine', {'name': item.attributes.name, 'id': item.id}) | list }}"
  vars:
    item: "{{ item }}"
"""

RETURN = r"""
  _raw:
    description: Raw API response from HCP Terraform containing project information
    type: dict
    contains:
      data:
        description: List of project objects
        type: list
        elements: dict
        contains:
          id:
            description: The ID of the project
            type: str
          type:
            description: The type of resource (always 'projects')
            type: str
          attributes:
            description: Project attributes
            type: dict
            contains:
              name:
                description: The name of the project
                type: str
              created-at:
                description: When the project was created
                type: str
              permissions:
                description: User permissions for this project
                type: dict
          relationships:
            description: Related resources
            type: dict
            contains:
              organization:
                description: The organization this project belongs to
                type: dict
          links:
            description: URL links related to this project
            type: dict
      links:
        description: Pagination links (if applicable)
        type: dict
      meta:
        description: Metadata about the response (if applicable)
        type: dict
"""

from ansible.errors import AnsibleError
from ansible.utils.display import Display
from ansible_collections.benemon.hcp_community_collection.plugins.module_utils.hcp_terraform_lookup import HCPTerraformLookup

display = Display()

class LookupModule(HCPTerraformLookup):
    def run(self, terms, variables=None, **kwargs):
        """Retrieve projects from HCP Terraform."""
        variables = variables or {}
        
        # Process parameters
        params = self._parse_parameters(terms, variables)
        
        # Set hostname for base URL
        self.base_url = self._get_hostname(params)
        
        # Validate required parameters
        required_params = ['organization']
        self._validate_params(params, required_params)
        
        # Build endpoint
        organization = params['organization']
        endpoint = f"organizations/{organization}/projects"
        
        display.vvv(f"Looking up projects for organization {organization}")
        
        try:
            # Build query parameters
            query_params = {}
            
            # Handle client-side name filtering
            name_filter = params.get('name')
            
            # Use the pagination handler from the base class
            results = self._handle_pagination(endpoint, params, query_params)
            
            # Apply client-side name filtering if specified
            if name_filter and 'data' in results:
                filtered_data = [
                    project for project in results['data']
                    if 'attributes' in project and 
                    'name' in project['attributes'] and 
                    project['attributes']['name'] == name_filter
                ]
                results['data'] = filtered_data
            
            # Return the raw results, preserving the original structure
            display.vvv(f"Successfully retrieved projects response")
            return [results]
        except Exception as e:
            display.error(f"Error retrieving projects: {str(e)}")
            raise AnsibleError(f"Error retrieving projects: {str(e)}")