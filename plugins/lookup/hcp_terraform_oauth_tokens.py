DOCUMENTATION = r"""
    name: hcp_terraform_oauth_tokens
    author: benemon
    version_added: "0.0.6"
    short_description: List OAuth tokens for HCP Terraform VCS connections
    description:
        - This lookup returns OAuth tokens from HCP Terraform
        - OAuth tokens are used to authenticate connections to VCS providers
        - Results can be filtered by OAuth client ID
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
        oauth_client_id:
            description:
                - ID of the OAuth client to filter tokens for
                - Required to list tokens for a specific OAuth client
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
    notes:
        - Authentication requires a valid HCP Terraform API token
        - OAuth tokens are tied to specific OAuth clients and VCS providers
        - OAuth clients must exist before retrieving tokens
        - This module only returns tokens the user has access to
        - Returns raw API response from HCP Terraform
    seealso:
        - module: benemon.hcp_community_collection.hcp_terraform_workspace
        - name: Terraform API Documentation
          link: https://developer.hashicorp.com/terraform/cloud-docs/api-docs/oauth-tokens
"""

EXAMPLES = r"""
# List all OAuth tokens for a specific OAuth client
- name: Get OAuth tokens
  ansible.builtin.debug:
    msg: "{{ lookup('benemon.hcp_community_collection.hcp_terraform_oauth_tokens', 
            oauth_client_id='oc-XKFwG6ggfA9n7t1K') }}"

# List OAuth tokens with explicit token and hostname
- name: Get OAuth tokens with specific credentials
  ansible.builtin.debug:
    msg: "{{ lookup('benemon.hcp_community_collection.hcp_terraform_oauth_tokens',
            token='your_terraform_token',
            hostname='https://app.terraform.io',
            oauth_client_id='oc-XKFwG6ggfA9n7t1K') }}"

# Get token ID for a specific OAuth client and use it in workspace creation
- name: Get OAuth token ID
  ansible.builtin.set_fact:
    oauth_token_id: "{{ lookup('benemon.hcp_community_collection.hcp_terraform_oauth_tokens',
                       oauth_client_id='oc-XKFwG6ggfA9n7t1K').data[0].id }}"

- name: Create workspace with VCS connection
  benemon.hcp_community_collection.hcp_terraform_workspace:
    name: "new-workspace"
    organization: "my-organization"
    vcs_repo:
      oauth_token_id: "{{ oauth_token_id }}"
      identifier: "my-org/my-repo"
      branch: "main"

# Extract specific fields using a comprehension
- name: Get a list of token IDs
  ansible.builtin.set_fact:
    token_ids: "{{ lookup('benemon.hcp_community_collection.hcp_terraform_oauth_tokens',
                  oauth_client_id='oc-XKFwG6ggfA9n7t1K').data | map(attribute='id') | list }}"
"""

RETURN = r"""
  _raw:
    description: Raw API response from HCP Terraform containing OAuth token information
    type: dict
    contains:
      data:
        description: List of OAuth token objects
        type: list
        elements: dict
        contains:
          id:
            description: The ID of the OAuth token
            type: str
          type:
            description: The type of resource (always 'oauth-tokens')
            type: str
          attributes:
            description: OAuth token attributes
            type: dict
            contains:
              created-at:
                description: When the token was created
                type: str
              service-provider-user:
                description: The username of the VCS provider user
                type: str
              has-ssh-key:
                description: Whether the token has an associated SSH key
                type: bool
          relationships:
            description: Related resources
            type: dict
            contains:
              oauth-client:
                description: The OAuth client this token belongs to
                type: dict
          links:
            description: URL links related to this token
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
        """Retrieve OAuth tokens from HCP Terraform."""
        variables = variables or {}
        
        # Process parameters
        params = self._parse_parameters(terms, variables)
        
        # Set hostname for base URL
        self.base_url = self._get_hostname(params)
        
        # Validate required parameters
        required_params = ['oauth_client_id']
        self._validate_params(params, required_params)
        
        # Build endpoint
        oauth_client_id = params['oauth_client_id']
        endpoint = f"oauth-clients/{oauth_client_id}/oauth-tokens"
        
        display.vvv(f"Looking up OAuth tokens for client {oauth_client_id}")
        
        try:
            # Use the pagination handler from the base class
            results = self._handle_pagination(endpoint, params)
            
            # Return the raw results, preserving the original structure
            display.vvv(f"Successfully retrieved OAuth tokens response")
            return [results]
        except Exception as e:
            display.error(f"Error retrieving OAuth tokens: {str(e)}")
            raise AnsibleError(f"Error retrieving OAuth tokens: {str(e)}")