from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r"""
    name: hvs_secrets
    author: benemon
    version_added: "1.0.0"
    short_description: List secrets in an app from HashiCorp Vault Secrets (HVS)
    description:
        - This lookup returns a list of secrets from an app in HashiCorp Vault Secrets (HVS)
    options:
        organization_id:
            description: HCP Organization ID
            required: True
            type: str
        project_id:
            description: HCP Project ID
            required: True
            type: str
        app_name:
            description: Name of the app containing the secrets
            required: True
            type: str
        hcp_token:
            description: 
                - HCP API token
                - Can also be specified via HCP_TOKEN environment variable
            required: False
            type: str
        hcp_client_id:
            description:
                - HCP Client ID for OAuth authentication
                - Can also be specified via HCP_CLIENT_ID environment variable
            required: False
            type: str
        hcp_client_secret:
            description:
                - HCP Client Secret for OAuth authentication
                - Can also be specified via HCP_CLIENT_SECRET environment variable
            required: False
            type: str
        disable_pagination:
            description: If True, returns only the first page of results
            required: False
            type: bool
            default: False
        page_size:
            description: Number of results per page
            required: False
            type: int
        max_pages:
            description: Maximum number of pages to retrieve
            required: False
            type: int
        name_contains:
            description: Filter secrets by name
            required: False
            type: str
        types:
            description: Filter secrets by types (comma-separated)
            required: False
            type: str
    notes:
        - Authentication can be provided either via token (hcp_token/HCP_TOKEN) or client credentials
          (hcp_client_id + hcp_client_secret or HCP_CLIENT_ID + HCP_CLIENT_SECRET)
        - Environment variables take precedence over playbook variables
        - Returns all secrets by default; use filters to limit results
"""

EXAMPLES = r"""
# List all secrets in an app using token authentication
- ansible.builtin.debug:
    msg: "{{ lookup('benemon.hcp_community_collection.hvs_secrets', 
             organization_id=org_id,
             project_id=proj_id,
             app_name='my-app') }}"

# List secrets with name filter
- ansible.builtin.debug:
    msg: "{{ lookup('benemon.hcp_community_collection.hvs_secrets',
             organization_id=org_id,
             project_id=proj_id,
             app_name='my-app',
             name_contains='password') }}"

# List secrets by type
- ansible.builtin.debug:
    msg: "{{ lookup('benemon.hcp_community_collection.hvs_secrets',
             organization_id=org_id,
             project_id=proj_id,
             app_name='my-app',
             types='kv,rotating') }}"

# Paginate results
- ansible.builtin.debug:
    msg: "{{ lookup('benemon.hcp_community_collection.hvs_secrets',
             organization_id=org_id,
             project_id=proj_id,
             app_name='my-app',
             page_size=10,
             max_pages=2) }}"
"""

RETURN = r"""
  _list:
    description: List of secrets from an HVS app
    type: list
    elements: dict
    contains:
      name:
        description: Name of the secret
        type: str
        returned: always
      type:
        description: Type of secret
        type: str
        returned: always
      provider:
        description: Provider of the secret
        type: str
        returned: when applicable
      latest_version:
        description: Latest version number of the secret
        type: int
        returned: always
      created_at:
        description: Timestamp when the secret was created
        type: str
        returned: always
      created_by:
        description: Information about who created the secret
        type: dict
        returned: always
      sync_status:
        description: Sync status of the secret
        type: dict
        returned: when applicable
      static_version:
        description: Static version details of the secret
        type: dict
        returned: when applicable
      rotating_version:
        description: Rotating version details of the secret
        type: dict
        returned: when applicable
      version_count:
        description: Number of secret versions
        type: str
        returned: always
"""

from ansible_collections.benemon.hcp_community_collection.plugins.module_utils.base.hcp_base import HCPLookupBase
from ansible.errors import AnsibleError
from ansible.utils.display import Display
import json

display = Display()

class LookupModule(HCPLookupBase):
    def run(self, terms, variables=None, **kwargs):
        """List secrets in an HVS app."""
        variables = variables or {}

        # Parse terms into key-value pairs
        for term in terms:
            if isinstance(term, str) and '=' in term:
                key, value = term.split('=', 1)
                variables[key] = value

        display.vvv(f"Lookup parameters: {json.dumps(variables, indent=2, default=str)}")

        # Validate required parameters
        try:
            self._validate_params(terms, variables, [
                'organization_id',
                'project_id',
                'app_name'
            ])
        except AnsibleError as e:
            display.error(f"Parameter validation failed: {str(e)}")
            raise

        # Build endpoint
        endpoint = (f"secrets/{self.api_version}/organizations/{variables['organization_id']}"
                   f"/projects/{variables['project_id']}/apps/{variables['app_name']}/secrets")

        try:
            # The base class now handles all parameter processing
            display.vvv(f"Making request to endpoint: {endpoint}")
            result = self._handle_pagination(endpoint, variables)
            
            # Ensure we always return a list, even if empty
            secrets = result.get('results', [])
            display.vvv(f"Retrieved {len(secrets)} secrets")
            return [secrets]
            
        except Exception as e:
            display.error(f"Error listing secrets: {str(e)}")
            raise AnsibleError(f'Error listing secrets: {str(e)}')