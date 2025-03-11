DOCUMENTATION = r"""
    name: hcp_terraform_oauth_clients
    author: benemon
    version_added: "0.0.7"
    short_description: List OAuth clients for HCP Terraform VCS connections
    description:
        - This lookup returns OAuth clients from HCP Terraform.
        - OAuth clients represent connections between an organization and a VCS provider.
        - Results can be filtered by name, service provider, or organization scope.
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
                - The name of the organization to list OAuth clients for.
                - Required for listing OAuth clients.
            required: true
            type: str
        name:
            description:
                - Filter results by client name.
                - Partial matches are supported.
            required: false
            type: str
        service_provider:
            description:
                - Filter results by service provider type.
                - Valid values include github, github_enterprise, gitlab_hosted, etc.
            required: false
            type: str
        organization_scoped:
            description:
                - Filter results by organization scope.
                - If true, return only organization-scoped clients.
                - If false, return only project-scoped clients.
            required: false
            type: bool
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
    notes:
        - Authentication requires a valid HCP Terraform API token.
        - OAuth clients connect an organization to VCS providers like GitHub, GitLab, etc.
        - This module only returns clients the user has access to.
        - Returns raw API response from HCP Terraform.
    seealso:
        - module: benemon.hcp_community_collection.hcp_terraform_workspace
        - module: benemon.hcp_community_collection.hcp_terraform_oauth_tokens
        - name: Terraform API Documentation
          link: https://developer.hashicorp.com/terraform/cloud-docs/api-docs/oauth-clients
"""

EXAMPLES = r"""
# List all OAuth clients for an organization
- name: Get all OAuth clients
  ansible.builtin.debug:
    msg: "{{ lookup('benemon.hcp_community_collection.hcp_terraform_oauth_clients', 
            organization='my-organization') }}"

# List OAuth clients with explicit token and hostname
- name: Get OAuth clients with specific credentials
  ansible.builtin.debug:
    msg: "{{ lookup('benemon.hcp_community_collection.hcp_terraform_oauth_clients',
            token='your_terraform_token',
            hostname='https://app.terraform.io',
            organization='my-organization') }}"

# Filter OAuth clients by name
- name: Get GitHub OAuth clients
  ansible.builtin.debug:
    msg: "{{ lookup('benemon.hcp_community_collection.hcp_terraform_oauth_clients',
            organization='my-organization',
            name='github') }}"

# Filter OAuth clients by service provider
- name: Get all GitHub clients
  ansible.builtin.debug:
    msg: "{{ lookup('benemon.hcp_community_collection.hcp_terraform_oauth_clients',
            organization='my-organization',
            service_provider='github') }}"

# Get organization-scoped OAuth clients
- name: Get organization-scoped clients
  ansible.builtin.debug:
    msg: "{{ lookup('benemon.hcp_community_collection.hcp_terraform_oauth_clients',
            organization='my-organization',
            organization_scoped=true) }}"

# Extract specific fields using a comprehension
- name: Get a list of client IDs for GitHub connections
  ansible.builtin.set_fact:
    github_client_ids: >-
      {{ lookup('benemon.hcp_community_collection.hcp_terraform_oauth_clients',
         organization='my-organization') 
         | json_query('data[?attributes.service-provider==`github`].id') }}

# Find OAuth client ID and use it to retrieve tokens
- name: Get GitHub OAuth client ID
  ansible.builtin.set_fact:
    github_oauth_client: >-
      {{ lookup('benemon.hcp_community_collection.hcp_terraform_oauth_clients',
         organization='my-organization',
         service_provider='github').data | first }}

- name: Get tokens for the GitHub OAuth client
  ansible.builtin.set_fact:
    github_tokens: "{{ lookup('benemon.hcp_community_collection.hcp_terraform_oauth_tokens',
                     oauth_client_id=github_oauth_client.id) }}"

# Complete workflow example
- name: Find GitHub OAuth client
  ansible.builtin.set_fact:
    github_client: >-
      {{ lookup('benemon.hcp_community_collection.hcp_terraform_oauth_clients',
         organization='my-organization',
         service_provider='github').data | first }}

- name: Get tokens for the GitHub OAuth client
  ansible.builtin.set_fact:
    github_token: "{{ lookup('benemon.hcp_community_collection.hcp_terraform_oauth_tokens',
                   oauth_client_id=github_client.id).data | first }}"

- name: Create Terraform workspace with VCS connection
  benemon.hcp_community_collection.hcp_terraform_workspace:
    token: "{{ lookup('env', 'TFE_TOKEN') }}"
    organization: "my-organization"
    name: "vcs-connected-workspace"
    vcs_repo:
      oauth_token_id: "{{ github_token.id }}"
      identifier: "my-org/my-repo"
      branch: "main"
"""

RETURN = r"""
  _raw:
    description: Raw API response from HCP Terraform containing OAuth client information.
    type: dict
    contains:
      data:
        description: List of OAuth client objects.
        type: list
        elements: dict
        contains:
          id:
            description: The ID of the OAuth client.
            type: str
            sample: "oc-XKFwG6ggfA9n7t1K"
          type:
            description: The type of resource (always 'oauth-clients').
            type: str
            sample: "oauth-clients"
          attributes:
            description: OAuth client attributes.
            type: dict
            contains:
              created-at:
                description: When the client was created.
                type: str
                sample: "2021-08-16T21:22:49.566Z"
              service-provider:
                description: The type of VCS provider.
                type: str
                sample: "github"
              service-provider-display-name:
                description: Display name of the VCS provider.
                type: str
                sample: "GitHub"
              name:
                description: Display name for the OAuth client.
                type: str
                sample: "GitHub Provider"
              http-url:
                description: URL of the VCS provider.
                type: str
                sample: "https://github.com"
              api-url:
                description: API URL of the VCS provider.
                type: str
                sample: "https://api.github.com"
              organization-scoped:
                description: Whether the client is available to all projects in the organization.
                type: bool
                sample: true
              callback-url:
                description: OAuth callback URL.
                type: str
                sample: "https://app.terraform.io/auth/35936d44-842c-4ddd-b4d4-7c741383dc3a"
              connect-path:
                description: OAuth connection path.
                type: str
                sample: "/auth/35936d44-842c-4ddd-b4d4-7c741383dc3a?organization_id=1"
          relationships:
            description: Related resources.
            type: dict
            contains:
              organization:
                description: The organization this client belongs to.
                type: dict
              projects:
                description: The projects this client is available to (if not organization-scoped).
                type: dict
              oauth-tokens:
                description: The OAuth tokens associated with this client.
                type: dict
              agent-pool:
                description: The agent pool associated with this client for VCS operations.
                type: dict
          links:
            description: URL links related to this client.
            type: dict
            sample: {"self": "/api/v2/oauth-clients/oc-XKFwG6ggfA9n7t1K"}
      links:
        description: Pagination links (if applicable).
        type: dict
      meta:
        description: Metadata about the response (if applicable).
        type: dict
"""

from ansible.errors import AnsibleError
from ansible.utils.display import Display
from ansible_collections.benemon.hcp_community_collection.plugins.module_utils.hcp_terraform_lookup import HCPTerraformLookup
from ansible_collections.benemon.hcp_community_collection.plugins.module_utils.collection_utils import str_to_bool

display = Display()

class LookupModule(HCPTerraformLookup):
    def run(self, terms, variables=None, **kwargs):
        """Retrieve OAuth clients from HCP Terraform."""
        variables = variables or {}
        
        # Process parameters
        params = self._parse_parameters(terms, variables)

        # Convert organization_scoped to a boolean if provided
        if 'organization_scoped' in params:
            try:
                params['organization_scoped'] = str_to_bool(params['organization_scoped'])
            except ValueError as e:
                raise AnsibleError(f"Invalid value for organization_scoped: {params['organization_scoped']}")
        
        # Set hostname for base URL
        self.base_url = self._get_hostname(params)
        
        # Validate required parameters
        required_params = ['organization']
        self._validate_params(params, required_params)
        
        # Build endpoint
        organization = params['organization']
        endpoint = f"organizations/{organization}/oauth-clients"
        
        # Build query parameters
        query_params = {}
        
        # Apply filters to the API request where possible
        # Note: The HCP Terraform API doesn't support filtering OAuth clients via query params
        # We'll perform client-side filtering after getting the response
        
        display.vvv(f"Looking up OAuth clients for organization {organization}")
        
        try:
            # Use the pagination handler from the base class
            results = self._handle_pagination(endpoint, params, query_params)
            
            # Apply client-side filtering
            if 'data' in results and isinstance(results['data'], list):
                filtered_data = results['data']
                
                # Filter by name
                if 'name' in params and params['name']:
                    name_filter = params['name'].lower()
                    filtered_data = [
                        client for client in filtered_data
                        if client.get('attributes', {}).get('name') and 
                        name_filter in client['attributes']['name'].lower()
                    ]
                
                # Filter by service provider
                if 'service_provider' in params and params['service_provider']:
                    service_provider = params['service_provider']
                    filtered_data = [
                        client for client in filtered_data
                        if client.get('attributes', {}).get('service-provider') == service_provider
                    ]
                
                # Filter by organization scope
                if 'organization_scoped' in params and params['organization_scoped'] is not None:
                    org_scoped = params['organization_scoped']
                    filtered_data = [
                        client for client in filtered_data
                        if client.get('attributes', {}).get('organization-scoped') == org_scoped
                    ]
                
                # Update the results with the filtered data
                results['data'] = filtered_data
            
            # Return the raw results, preserving the original structure
            display.vvv(f"Successfully retrieved {len(results.get('data', []))} OAuth clients")
            return [results]
        except Exception as e:
            display.error(f"Error retrieving OAuth clients: {str(e)}")
            raise AnsibleError(f"Error retrieving OAuth clients: {str(e)}")