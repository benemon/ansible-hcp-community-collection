#!/usr/bin/python
DOCUMENTATION = r"""
    name: hcp_terraform_projects
    author: benemon
    version_added: "0.0.7"
    short_description: List projects for HCP Terraform with server-side filtering
    description:
        - This lookup returns projects from HCP Terraform.
        - Projects are used to organize workspaces within organizations.
        - Results can be filtered by organization and further refined using the 'q' parameter, which is passed directly to the API for server-side filtering.
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
                - Name of the organization to filter projects for.
                - Required to list projects for a specific organization.
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
                - Client-side filter to return only projects with an exact matching name (case-sensitive).
            required: false
            type: str
        q:
            description:
                - Server-side search query to filter projects.
                - This query is passed directly to the API endpoint for filtering.
            required: false
            type: str
    notes:
        - Authentication requires a valid HCP Terraform API token.
        - Projects are organization-specific.
        - Returns raw API response from HCP Terraform.
    seealso:
        - module: benemon.hcp_community_collection.hcp_terraform_workspace
        - name: Terraform API Documentation
          link: https://developer.hashicorp.com/terraform/cloud-docs/api-docs/projects
"""

EXAMPLES = r"""
# List all projects for an organization
- name: Get projects for an organization
  ansible.builtin.debug:
    msg: "{{ lookup('benemon.hcp_community_collection.hcp_terraform_projects', organization='my-organization') }}"

# List projects using server-side filtering with a search query
- name: Get projects using server-side filtering
  ansible.builtin.debug:
    msg: "{{ lookup('benemon.hcp_community_collection.hcp_terraform_projects', 
            token='your_terraform_token',
            hostname='https://app.terraform.io',
            organization='my-organization',
            q='terraform') }}"

# Get project ID by filtering with a client-side name filter
- name: Get project ID for a project with an exact name
  ansible.builtin.set_fact:
    project_id: "{{ lookup('benemon.hcp_community_collection.hcp_terraform_projects',
                  organization='my-organization',
                  name='My Project')._raw.data | 
                  selectattr('attributes.name', 'equalto', 'My Project') | 
                  map(attribute='id') | first }}"

- name: Create a workspace in the specified project
  benemon.hcp_community_collection.hcp_terraform_workspace:
    name: "new-workspace"
    organization: "my-organization"
    project_id: "{{ project_id }}"

# Extract specific fields using a comprehension and a server-side query
- name: Get a list of project names and IDs
  ansible.builtin.set_fact:
    projects: "{{ lookup('benemon.hcp_community_collection.hcp_terraform_projects',
                organization='my-organization',
                q='terraform')._raw.data | 
                map('combine', {'name': item.attributes.name, 'id': item.id}) | list }}"
  vars:
    item: "{{ item }}"

# Limit number of results using pagination controls
- name: Get first page with 5 projects per page
  ansible.builtin.debug:
    msg: "{{ lookup('benemon.hcp_community_collection.hcp_terraform_projects',
            organization='my-organization',
            page_size=5,
            disable_pagination=true) }}"
"""

RETURN = r"""
  _raw:
    description: Raw API response from HCP Terraform containing project information.
    type: dict
    contains:
      data:
        description: List of project objects.
        type: list
        elements: dict
        contains:
          id:
            description: The ID of the project.
            type: str
            sample: "prj-jT92VLSFpv8FwKtc"
          type:
            description: The type of resource (always 'projects').
            type: str
            sample: "projects"
          attributes:
            description: Project attributes.
            type: dict
            contains:
              name:
                description: The name of the project.
                type: str
                sample: "AWS Infrastructure"
              created-at:
                description: When the project was created.
                type: str
                sample: "2023-05-15T18:24:16.591Z"
              permissions:
                description: User permissions for this project.
                type: dict
                sample: {"can-update": true, "can-destroy": true, "can-create-workspace": true}
          relationships:
            description: Related resources.
            type: dict
            contains:
              organization:
                description: The organization this project belongs to.
                type: dict
          links:
            description: URL links related to this project.
            type: dict
            sample: {"self": "/api/v2/projects/prj-jT92VLSFpv8FwKtc"}
      links:
        description: Pagination links (if applicable).
        type: dict
        sample: {"self": "/api/v2/organizations/my-organization/projects?page[number]=1&page[size]=20"}
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
        """Retrieve projects from HCP Terraform."""
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
        endpoint = f"organizations/{organization}/projects"
        
        display.vvv(f"Looking up projects for organization {organization}")
        
        try:
            # Build query parameters
            query_params = {}
            
            # Add server-side search query if provided
            if 'q' in params:
                query_params['q'] = params['q']
            
            # Retrieve client-side name filter if provided
            name_filter = params.get('name')
            
            # Use the pagination handler from the base class to retrieve results
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
            display.vvv("Successfully retrieved projects response")
            return [results]
        except Exception as e:
            display.error(f"Error retrieving projects: {str(e)}")
            raise AnsibleError(f"Error retrieving projects: {str(e)}")

if __name__ == '__main__':
    # For testing purposes, you can invoke the lookup module from the command line.
    lookup = LookupModule()
    result = lookup.run([], {})
    print(result)
