#!/usr/bin/python
DOCUMENTATION = r"""
    name: hcp_terraform_organizations
    author: benemon
    version_added: "0.0.7"
    short_description: List organizations for HCP Terraform with server-side filtering
    description:
        - This lookup returns organizations from HCP Terraform.
        - Organizations are the top-level resource that contain projects and workspaces.
        - Results can be filtered using the 'q' parameter for server-side filtering.
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
        q:
            description:
                - Server-side search query to filter organizations.
                - This query is passed directly to the API endpoint for filtering.
            required: false
            type: str
        q_name:
            description:
                - Filter organizations by name. Shorthand for q[name].
                - Provides server-side filtering based on the name attribute.
            required: false
            type: str
        q_email:
            description:
                - Filter organizations by email. Shorthand for q[email].
                - Provides server-side filtering based on the email attribute.
            required: false
            type: str
        name:
            description:
                - Client-side filter to return only organizations with an exact matching name (case-sensitive).
            required: false
            type: str
    notes:
        - Authentication requires a valid HCP Terraform API token.
        - Returns raw API response from HCP Terraform.
    seealso:
        - module: benemon.hcp_community_collection.hcp_terraform_organization
        - name: Terraform API Documentation
          link: https://developer.hashicorp.com/terraform/cloud-docs/api-docs/organizations
"""

EXAMPLES = r"""
# List all organizations
- name: Get all organizations
  ansible.builtin.debug:
    msg: "{{ lookup('benemon.hcp_community_collection.hcp_terraform_organizations') }}"

# List organizations using server-side filtering with a search query
- name: Get organizations using server-side filtering
  ansible.builtin.debug:
    msg: "{{ lookup('benemon.hcp_community_collection.hcp_terraform_organizations', 
            token='your_terraform_token',
            hostname='https://app.terraform.io',
            q='terraform') }}"

# Get organization by filtering with a client-side name filter
- name: Get organization with an exact name
  ansible.builtin.set_fact:
    organization_id: "{{ lookup('benemon.hcp_community_collection.hcp_terraform_organizations',
                    name='My Organization')._raw.data | 
                    selectattr('attributes.name', 'equalto', 'My Organization') | 
                    map(attribute='id') | first }}"

# Filter organizations by email domain using server-side filtering
- name: Get organizations with a specific email domain
  ansible.builtin.debug:
    msg: "{{ lookup('benemon.hcp_community_collection.hcp_terraform_organizations',
            q_email='@example.com') }}"

# Extract specific fields using a comprehension
- name: Get a list of organization names and IDs
  ansible.builtin.set_fact:
    organizations: "{{ lookup('benemon.hcp_community_collection.hcp_terraform_organizations')._raw.data | 
                map('combine', {'name': item.attributes.name, 'id': item.id}) | list }}"
  vars:
    item: "{{ item }}"

# Limit number of results using pagination controls
- name: Get first page with 5 organizations per page
  ansible.builtin.debug:
    msg: "{{ lookup('benemon.hcp_community_collection.hcp_terraform_organizations',
            page_size=5,
            disable_pagination=true) }}"
"""

RETURN = r"""
  _raw:
    description: Raw API response from HCP Terraform containing organization information.
    type: dict
    contains:
      data:
        description: List of organization objects.
        type: list
        elements: dict
        contains:
          id:
            description: The ID of the organization.
            type: str
            sample: "my-organization"
          type:
            description: The type of resource (always 'organizations').
            type: str
            sample: "organizations"
          attributes:
            description: Organization attributes.
            type: dict
            contains:
              name:
                description: The name of the organization.
                type: str
                sample: "My Organization"
              email:
                description: The email address of the organization.
                type: str
                sample: "admin@example.com"
              created-at:
                description: When the organization was created.
                type: str
                sample: "2023-05-15T18:24:16.591Z"
              permissions:
                description: User permissions for this organization.
                type: dict
              collaborator-auth-policy:
                description: The auth policy (password or two_factor_mandatory).
                type: str
                sample: "password"
          relationships:
            description: Related resources.
            type: dict
          links:
            description: URL links related to this organization.
            type: dict
            sample: {"self": "/api/v2/organizations/my-organization"}
      links:
        description: Pagination links (if applicable).
        type: dict
        sample: {"self": "/api/v2/organizations?page[number]=1&page[size]=20"}
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
        """Retrieve organizations from HCP Terraform."""
        variables = variables or {}
        
        # Process parameters
        params = self._parse_parameters(terms, variables)
        
        # Set hostname for base URL
        self.base_url = self._get_hostname(params)
        
        display.vvv(f"Looking up organizations")
        
        try:
            # Build endpoint for organizations
            endpoint = "organizations"
            
            # Build query parameters
            query_params = {}
            
            # Add server-side search query if provided
            if 'q' in params:
                query_params['q'] = params['q']
            
            # Add specific filters if provided
            if 'q_name' in params:
                query_params['q[name]'] = params['q_name']
                
            if 'q_email' in params:
                query_params['q[email]'] = params['q_email']
            
            # Retrieve client-side name filter if provided
            name_filter = params.get('name')
            
            # Use the pagination handler from the base class to retrieve results
            results = self._handle_pagination(endpoint, params, query_params)
            
            # Apply client-side name filtering if specified
            if name_filter and 'data' in results:
                filtered_data = [
                    org for org in results['data']
                    if 'attributes' in org and 
                    'name' in org['attributes'] and 
                    org['attributes']['name'] == name_filter
                ]
                results['data'] = filtered_data
            
            # Return the raw results, preserving the original structure
            display.vvv("Successfully retrieved organizations response")
            return [results]
        except Exception as e:
            display.error(f"Error retrieving organizations: {str(e)}")
            raise AnsibleError(f"Error retrieving organizations: {str(e)}")

if __name__ == '__main__':
    # For testing purposes, you can invoke the lookup module from the command line.
    lookup = LookupModule()
    result = lookup.run([], {})
    print(result)