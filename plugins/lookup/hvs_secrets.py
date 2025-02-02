from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r"""
    name: hvs_secrets
    author: benemon
    version_added: "0.0.1"
    short_description: List secrets in an app from HashiCorp Vault Secrets (HVS)
    description:
        - This lookup returns a list of secrets from an app in HashiCorp Vault Secrets (HVS)
        - Returns metadata about secrets without their values
        - Can filter by secret name and type
        - Supports pagination of results
        - Does not return secret values - use specific secret lookup plugins for values
    options:
        organization_id:
            description: 
                - HCP Organization ID
                - Required for all operations
            required: true
            type: str
        project_id:
            description: 
                - HCP Project ID
                - Required for all operations
            required: true
            type: str
        app_name:
            description: 
                - Name of the app containing the secrets
                - Must exist in the project
            required: true
            type: str
        hcp_token:
            description:
                - HCP API token for authentication
                - Can be specified via HCP_TOKEN environment variable
                - Cannot be used together with client credentials (hcp_client_id/hcp_client_secret)
            required: false
            type: str
            env:
                - name: HCP_TOKEN
        hcp_client_id:
            description:
                - HCP Client ID for OAuth authentication
                - Can be specified via HCP_CLIENT_ID environment variable
                - Must be used together with hcp_client_secret
                - Cannot be used together with hcp_token
            required: false
            type: str
            env:
                - name: HCP_CLIENT_ID
        hcp_client_secret:
            description:
                - HCP Client Secret for OAuth authentication
                - Can be specified via HCP_CLIENT_SECRET environment variable
                - Must be used together with hcp_client_id
                - Cannot be used together with hcp_token
            required: false
            type: str
            env:
                - name: HCP_CLIENT_SECRET
        name_contains:
            description: 
                - Filter secrets by partial name match
                - Case-sensitive string comparison
                - Empty string matches all names
            required: false
            type: str
        types:
            description: 
                - Filter secrets by type
                - Comma-separated list of types
                - Valid types are kv, rotating, dynamic
                - Empty string matches all types
            required: false
            type: str
        page_size:
            description: 
                - Number of results to return per page
                - Defaults to service-defined value if not specified
                - Set to 0 to use service default
            required: false
            type: int
        max_pages:
            description:
                - Maximum number of pages to retrieve
                - Use with page_size to limit total results
                - If not set, retrieves all available pages
            required: false
            type: int
        disable_pagination:
            description: 
                - If True, returns only the first page of results
                - Overrides max_pages if set
            required: false
            type: bool
            default: false
    notes:
        - Authentication requires either an API token (hcp_token/HCP_TOKEN) or client credentials (hcp_client_id + hcp_client_secret)
        - Authentication methods cannot be mixed - use either token or client credentials
        - Environment variables take precedence over playbook parameters
        - All timestamps are returned in RFC3339 format
        - All responses are paginated by default with a default page size
        - Empty results return an empty list rather than failing
        - Multiple filter parameters are combined with AND logic
        - Does not return secret values, only metadata
        - For secret values, use the appropriate secret-type specific lookup plugin
    seealso:
        - module: benemon.hcp_community_collection.hvs_static_secret
        - module: benemon.hcp_community_collection.hvs_dynamic_secret
        - module: benemon.hcp_community_collection.hvs_rotating_secret
        - name: HVS API Documentation
          link: https://developer.hashicorp.com/hcp/api-docs/vault-secrets
"""

EXAMPLES = r"""
# List all secrets in an app using token auth
- name: Get all secrets
  ansible.builtin.debug:
    msg: "{{ lookup('benemon.hcp_community_collection.hvs_secrets',
             'organization_id=my-org-id',
             'project_id=my-project-id',
             'app_name=my-app') }}"

# List secrets with name filter and pagination
- name: Get filtered secrets
  ansible.builtin.debug:
    msg: "{{ lookup('benemon.hcp_community_collection.hvs_secrets',
             'organization_id=my-org-id',
             'project_id=my-project-id',
             'app_name=my-app',
             'name_contains=password',
             'page_size=10',
             'max_pages=2') }}"

# List specific types of secrets
- name: Get rotating and dynamic secrets
  ansible.builtin.debug:
    msg: "{{ lookup('benemon.hcp_community_collection.hvs_secrets',
             'organization_id=my-org-id',
             'project_id=my-project-id',
             'app_name=my-app',
             'types=rotating,dynamic') }}"

# List secrets with error handling and validation
- name: Get secrets with validation
  block:
    - name: Retrieve secrets
      set_fact:
        app_secrets: "{{ lookup('benemon.hcp_community_collection.hvs_secrets',
                        'organization_id=my-org-id',
                        'project_id=my-project-id',
                        'app_name=my-app') }}"
    - name: Count secret types
      set_fact:
        secret_counts: "{{ app_secrets | groupby('type') }}"
    - name: Display summary
      debug:
        msg: "Found {{ item.0 }} secrets of type {{ item.1 }}"
      loop: "{{ secret_counts }}"
  rescue:
    - name: Handle lookup failure
      debug:
        msg: "Failed to retrieve secrets"

# Find rotating secrets nearing expiration
- name: Check rotating secrets
  ansible.builtin.debug:
    msg: "Secret {{ item.name }} expires at {{ item.rotating_version.expires_at }}"
  loop: "{{ lookup('benemon.hcp_community_collection.hvs_secrets',
            'organization_id=my-org-id',
            'project_id=my-project-id',
            'app_name=my-app',
            'types=rotating') }}"
  when: 
    - item.rotating_version is defined
    - item.rotating_version.expires_at is defined
  loop_control:
    label: "{{ item.name }}"
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
        description: Type of secret (kv, rotating, or dynamic)
        type: str
        returned: always
      provider:
        description: Provider for the secret
        type: str
        returned: when applicable
      latest_version:
        description: Latest version number
        type: int
        format: int64
        returned: always
      created_at:
        description: Creation timestamp
        type: str
        format: date-time
        returned: always
      created_by:
        description: Information about who created the secret
        type: dict
        returned: always
        contains:
          name:
            description: Name of the principal
            type: str
          type:
            description: Type of principal
            type: str
          email:
            description: Email of the principal if applicable
            type: str
      sync_status:
        description: Status of syncs for this secret
        type: dict
        returned: when syncs configured
        contains:
          status:
            description: Current sync status
            type: str
          updated_at:
            description: Last sync update timestamp
            type: str
            format: date-time
          last_error_code:
            description: Error code from last sync attempt if any
            type: str
      static_version:
        description: Static version details if this is a static secret
        type: dict
        returned: when type is 'kv'
        contains:
          version:
            description: Version number
            type: int
            format: int64
          created_at:
            description: Version creation timestamp
            type: str
            format: date-time
          created_by:
            description: Principal who created this version
            type: dict
            contains:
              name:
                description: Name of the principal
                type: str
              type:
                description: Type of principal
                type: str
              email:
                description: Email of the principal if applicable
                type: str
      rotating_version:
        description: Rotating version details if this is a rotating secret
        type: dict
        returned: when type is 'rotating'
        contains:
          version:
            description: Version number
            type: int
            format: int64
          keys:
            description: List of available secret keys
            type: list
            elements: str
          created_by:
            description: Principal who created this version
            type: dict
            contains:
              name:
                description: Name of the principal
                type: str
              type:
                description: Type of principal
                type: str
              email:
                description: Email of the principal if applicable
                type: str
          created_at:
            description: Version creation timestamp
            type: str
            format: date-time
          expires_at:
            description: When this version expires
            type: str
            format: date-time
          revoked_at:
            description: When this version was revoked (if applicable)
            type: str
            format: date-time
      dynamic_config:
        description: Configuration for dynamic secrets
        type: dict
        returned: when type is 'dynamic'
        contains:
          ttl:
            description: Default TTL for this dynamic secret
            type: str
      version_count:
        description: Total number of versions
        type: str
        format: int64
        returned: always
"""

from ansible_collections.benemon.hcp_community_collection.plugins.module_utils.base.hcp_base import HCPLookupBase
from ansible_collections.benemon.hcp_community_collection.plugins.module_utils.api_versions import get_api_version
from ansible.errors import AnsibleError
from ansible.utils.display import Display
import json

display = Display()

class LookupModule(HCPLookupBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            self.api_version = get_api_version("hvs")  # Fetch API version dynamically
        except ValueError as e:
            display.error(f"Failed to get API version: {str(e)}")
            raise AnsibleError(str(e))  # Convert to AnsibleError for better error reporting
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