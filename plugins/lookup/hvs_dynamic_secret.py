from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r"""
    name: hvs_dynamic_secret
    author: benemon
    version_added: "0.0.1"
    short_description: Retrieve a dynamic secret value from HashiCorp Vault Secrets (HVS)
    description:
        - This lookup retrieves a dynamic secret value from HashiCorp Vault Secrets (HVS)
        - Uses the API to get the secret value and metadata
        - Dynamic secrets are generated on-demand and have a defined TTL
        - For static or rotating secrets, use their dedicated lookup plugins
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
                - Name of the app containing the secret
                - Must exist in the project
            required: true
            type: str
        secret_name:
            description: 
                - Name of the secret to retrieve
                - Must be a dynamic secret
            required: true
            type: str
        ttl:
            description: 
                - Override the default TTL for this request
                - Format: duration string (e.g. "1h", "30m", "24h")
                - If not specified, uses the secret's default TTL
            required: false
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
    notes:
        - Authentication requires either an API token (hcp_token/HCP_TOKEN) or client credentials (hcp_client_id + hcp_client_secret)
        - Authentication methods cannot be mixed - use either token or client credentials
        - Environment variables take precedence over playbook parameters
        - All timestamps are returned in RFC3339 format
        - Dynamic secrets are generated for each request
        - TTL values must be valid duration strings
        - Secret must already exist and be of type 'dynamic'
        - Returns error if secret type does not match
        - Values expire after TTL period
    seealso:
        - module: benemon.hcp_community_collection.hvs_static_secret
        - module: benemon.hcp_community_collection.hvs_rotating_secret
        - name: HVS API Documentation
          link: https://developer.hashicorp.com/hcp/api-docs/vault-secrets
"""

EXAMPLES = r"""
# Get a dynamic secret with default TTL using token auth
- name: Get AWS credentials
  ansible.builtin.debug:
    msg: "{{ lookup('benemon.hcp_community_collection.hvs_dynamic_secret',
             'organization_id=my-org-id',
             'project_id=my-project-id',
             'app_name=aws-app',
             'secret_name=temporary-creds') }}"

# Get a dynamic secret with custom TTL
- name: Get database credentials with 2 hour TTL
  ansible.builtin.debug:
    msg: "{{ lookup('benemon.hcp_community_collection.hvs_dynamic_secret',
             'organization_id=my-org-id',
             'project_id=my-project-id',
             'app_name=db-app',
             'secret_name=temp-db-user',
             'ttl=2h') }}"

# Get dynamic secret with OAuth credentials and handle errors
- name: Get dynamic secret with error handling
  block:
    - name: Retrieve secret
      set_fact:
        db_creds: "{{ lookup('benemon.hcp_community_collection.hvs_dynamic_secret',
                      'organization_id=my-org-id',
                      'project_id=my-project-id',
                      'app_name=db-app',
                      'secret_name=temp-access',
                      'hcp_client_id=client_id',
                      'hcp_client_secret=client_secret') }}"
  rescue:
    - name: Handle lookup failure
      debug:
        msg: "Failed to retrieve dynamic secret"

# Use dynamic secret in configuration
- name: Configure application with temporary credentials
  ansible.builtin.template:
    src: config.j2
    dest: /etc/myapp/config.yml
    mode: '0600'
  vars:
    credentials: "{{ lookup('benemon.hcp_community_collection.hvs_dynamic_secret',
                    'organization_id=my-org-id',
                    'project_id=my-project-id',
                    'app_name=service-app',
                    'secret_name=api-creds') }}"
"""

RETURN = r"""
  _list:
    description: Complete dynamic secret data as returned by the HVS API
    type: list
    elements: dict
    contains:
      name:
        description: Name of the secret
        type: str
        returned: always
      type:
        description: Type of secret (will be 'dynamic')
        type: str
        returned: always
      provider:
        description: Provider for this dynamic secret
        type: str
        returned: always
      created_at:
        description: Creation timestamp
        type: str
        format: date-time
        returned: always
      created_by_id:
        description: ID of the principal who created the secret
        type: str
        returned: always
      sync_status:
        description: Status of any syncs for this secret
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
      dynamic_instance:
        description: The dynamic secret instance data
        type: dict
        returned: always
        contains:
          values:
            description: Map of secret values
            type: dict
            returned: always
          created_at:
            description: When this instance was created
            type: str
            format: date-time
            returned: always
          expires_at:
            description: When this instance expires
            type: str
            format: date-time
            returned: always
          ttl:
            description: Time-to-live duration for this instance
            type: str
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
        """Retrieve a dynamic secret value from HVS."""
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
                'app_name',
                'secret_name'
            ])
        except AnsibleError as e:
            display.error(f"Parameter validation failed: {str(e)}")
            raise

        # First get metadata
        metadata_endpoint = (f"secrets/{self.api_version}/organizations/{variables['organization_id']}"
                        f"/projects/{variables['project_id']}/apps/{variables['app_name']}"
                        f"/secrets/{variables['secret_name']}")

        # Get secret metadata first to confirm type
        try:
            metadata = self._make_request('GET', metadata_endpoint, variables)
            if not metadata or 'secret' not in metadata:
                raise AnsibleError("Invalid metadata response from API")
            
            secret_type = metadata.get('secret', {}).get('type')
            if secret_type != 'dynamic':
                raise AnsibleError(f"Secret '{variables['secret_name']}' is not a dynamic secret (type: {secret_type})")
        except Exception as e:
            display.error(f"Error retrieving secret metadata: {str(e)}")
            raise AnsibleError(f'Error retrieving secret metadata: {str(e)}')

        # Build endpoint for secret retrieval
        endpoint = (f"secrets/{self.api_version}/organizations/{variables['organization_id']}"
                f"/projects/{variables['project_id']}/apps/{variables['app_name']}"
                f"/secrets/{variables['secret_name']}:open")

        # Add TTL parameter if specified
        params = {}
        if 'ttl' in variables:
            params['ttl'] = variables['ttl']

        try:
            # Make single request to get secret
            display.vvv(f"Making request to endpoint: {endpoint}")
            response = self._make_request('GET', endpoint, variables, params)
            
            # Validate response
            if not response or 'secret' not in response:
                display.error("Received invalid response from API")
                raise AnsibleError("Invalid or empty response from API")

            secret_data = response['secret']
            
            # Verify this is a dynamic secret
            if 'dynamic_instance' not in secret_data:
                if 'static_version' in secret_data:
                    raise AnsibleError(
                        'Retrieved static secret - please use hvs_static_secret plugin instead'
                    )
                elif 'rotating_version' in secret_data:
                    raise AnsibleError(
                        'Retrieved rotating secret - please use hvs_rotating_secret plugin instead'
                    )
                else:
                    raise AnsibleError("Unknown secret type in response")

            display.vvv("Successfully retrieved dynamic secret")
            return [secret_data]
            
        except Exception as e:
            display.error(f"Error retrieving dynamic secret: {str(e)}")
            raise AnsibleError(f'Error retrieving dynamic secret: {str(e)}')