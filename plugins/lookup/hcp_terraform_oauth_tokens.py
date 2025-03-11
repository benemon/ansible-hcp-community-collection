#!/usr/bin/python
DOCUMENTATION = r"""
    name: hcp_terraform_oauth_tokens
    author: benemon
    version_added: "0.0.7"
    short_description: Retrieve OAuth tokens from HCP Terraform
    description:
        - This lookup returns OAuth token information from HCP Terraform.
        - When a specific oauth_token_id is provided, the lookup uses the Show API endpoint.
        - Otherwise, it lists all tokens for a given OAuth client.
    options:
        token:
            description:
                - HCP Terraform API token.
                - Can be specified via the TFE_TOKEN environment variable.
            required: true
            type: str
            env:
                - name: TFE_TOKEN
        hostname:
            description:
                - HCP Terraform API hostname.
                - Can be specified via the TFE_HOSTNAME environment variable.
                - Defaults to https://app.terraform.io.
            required: false
            type: str
            default: "https://app.terraform.io"
            env:
                - name: TFE_HOSTNAME
        oauth_client_id:
            description:
                - The ID of the OAuth client to list tokens for.
                - Required when oauth_token_id is not provided.
            required: false
            type: str
        oauth_token_id:
            description:
                - The ID of a specific OAuth token to retrieve.
                - If provided, the Show API endpoint will be used.
            required: false
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
notes:
    - Authentication requires a valid HCP Terraform API token.
    - Returns raw API response from HCP Terraform.
seealso:
    - module: benemon.hcp_community_collection.hcp_terraform_oauth_clients
    - module: benemon.hcp_community_collection.hcp_terraform_state_versions
    - name: Terraform API Documentation
      link: https://developer.hashicorp.com/terraform/cloud-docs/api-docs/oauth-tokens
"""

EXAMPLES = r"""
# List all OAuth tokens for a given OAuth client
- name: List OAuth tokens
  ansible.builtin.debug:
    msg: "{{ lookup('benemon.hcp_community_collection.hcp_terraform_oauth_tokens', oauth_client_id='oc-EXAMPLE') }}"

# Retrieve a specific OAuth token by its ID
- name: Get specific OAuth token
  ansible.builtin.debug:
    msg: "{{ lookup('benemon.hcp_community_collection.hcp_terraform_oauth_tokens', oauth_token_id='ot-EXAMPLE') }}"
"""

RETURN = r"""
_raw:
    description: Raw API response from HCP Terraform containing OAuth token information.
    type: dict
    contains:
        data:
            description: OAuth token information.
            type: list
            elements: dict
            contains:
                id:
                    description: The ID of the OAuth token.
                    type: str
                type:
                    description: The type of resource (always 'oauth-tokens').
                    type: str
                attributes:
                    description: Attributes of the OAuth token.
                    type: dict
                relationships:
                    description: Related resources.
                    type: dict
        meta:
            description: Pagination metadata.
            type: dict
"""

from ansible.errors import AnsibleError
from ansible.utils.display import Display
from ansible_collections.benemon.hcp_community_collection.plugins.module_utils.hcp_terraform_lookup import HCPTerraformLookup

display = Display()

class LookupModule(HCPTerraformLookup):
    def run(self, terms, variables=None, **kwargs):
        """Retrieve OAuth token information from HCP Terraform."""
        variables = variables or {}

        # Process parameters
        params = self._parse_parameters(terms, variables)

        # Set hostname for base URL
        self.base_url = self._get_hostname(params)

        # Validate: if oauth_token_id is not provided, require oauth_client_id.
        if 'oauth_token_id' not in params and 'oauth_client_id' not in params:
            raise AnsibleError("Either oauth_token_id or oauth_client_id must be provided.")

        try:
            if 'oauth_token_id' in params:
                # Retrieve a specific OAuth token via the Show endpoint
                endpoint = f"/oauth-tokens/{params['oauth_token_id']}"
                result = self._make_request("GET", endpoint, params)
            else:
                # List OAuth tokens for the specified OAuth client
                oauth_client_id = params['oauth_client_id']
                endpoint = f"/oauth-clients/{oauth_client_id}/oauth-tokens"
                result = self._handle_pagination(endpoint, params, query_params={})
            display.vvv("Successfully retrieved OAuth token information")
            return [result]
        except Exception as e:
            display.error(f"Error retrieving OAuth tokens: {str(e)}")
            raise AnsibleError(f"Error retrieving OAuth tokens: {str(e)}")

if __name__ == '__main__':
    # For testing purposes only
    lookup = LookupModule()
    print(lookup.run([], {}))
