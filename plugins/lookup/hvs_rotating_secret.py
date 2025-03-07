from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r"""
    name: hvs_rotating_secret
    author: benemon
    version_added: "0.0.1"
    short_description: Retrieve a rotating secret value from HashiCorp Vault Secrets (HVS)
    description:
        - This lookup retrieves a rotating secret value from HashiCorp Vault Secrets (HVS)
        - Returns the decrypted secret value and metadata
        - Rotating secrets automatically rotate on a schedule and maintain previous versions
        - For static or dynamic secrets, use their dedicated lookup plugins
        - Returns latest valid version by default
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
                - Must be a rotating secret
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
    notes:
        - Authentication requires either an API token (hcp_token/HCP_TOKEN) or client credentials (hcp_client_id + hcp_client_secret)
        - Authentication methods cannot be mixed - use either token or client credentials
        - Environment variables take precedence over playbook parameters
        - All timestamps are returned in RFC3339 format
        - Returns latest non-revoked version by default
        - Secret must already exist and be of type 'rotating'
        - Returns error if secret type does not match
        - Multiple values may be returned in the values dictionary
        - Expiration and revocation times are included in response
    seealso:
        - module: benemon.hcp_community_collection.hvs_static_secret
        - module: benemon.hcp_community_collection.hvs_dynamic_secret
        - name: HVS API Documentation
          link: https://developer.hashicorp.com/hcp/api-docs/vault-secrets
"""

EXAMPLES = r"""
# Get latest version of rotating secret using token auth
- name: Get database credentials
  ansible.builtin.debug:
    msg: "{{ lookup('benemon.hcp_community_collection.hvs_rotating_secret',
             'organization_id=my-org-id',
             'project_id=my-project-id',
             'app_name=db-app',
             'secret_name=database-password') }}"

# Use rotating secret with error handling
- name: Get rotating secret with validation
  block:
    - name: Retrieve secret
      set_fact:
        api_key: "{{ lookup('benemon.hcp_community_collection.hvs_rotating_secret',
                     'organization_id=my-org-id',
                     'project_id=my-project-id',
                     'app_name=api-app',
                     'secret_name=api-key') }}"
    - name: Verify secret values exist
      assert:
        that:
          - api_key.rotating_version.values is defined
          - api_key.rotating_version.values | length > 0
        fail_msg: "Retrieved secret has no values"
  rescue:
    - name: Handle lookup failure
      debug:
        msg: "Failed to retrieve rotating secret or invalid data received"

# Check expiration of rotating secret
- name: Get and check rotating credentials
  block:
    - name: Get credentials
      set_fact:
        creds: "{{ lookup('benemon.hcp_community_collection.hvs_rotating_secret',
                   'organization_id=my-org-id',
                   'project_id=my-project-id',
                   'app_name=service-app',
                   'secret_name=service-creds') }}"
    - name: Check expiration
      debug:
        msg: "Warning: Credentials expire at {{ creds.rotating_version.expires_at }}"
      when: creds.rotating_version.expires_at is defined

# Use rotating secret in configuration with value checking
- name: Configure application with rotating credentials
  ansible.builtin.template:
    src: config.j2
    dest: /etc/myapp/config.yml
    mode: '0600'
  vars:
    secret: "{{ lookup('benemon.hcp_community_collection.hvs_rotating_secret',
                'organization_id=my-org-id',
                'project_id=my-project-id',
                'app_name=my-app',
                'secret_name=app-secret') }}"
  when: 
    - secret.rotating_version is defined 
    - secret.rotating_version.values is defined
    - secret.rotating_version.revoked_at is not defined
"""

RETURN = r"""
  _list:
    description: Complete secret data as returned by the HVS API
    type: list
    elements: dict
    contains:
      name:
        description: Name of the secret
        type: str
        returned: always
      type:
        description: Type of secret (will be 'rotating')
        type: str
        returned: always
      provider:
        description: Provider for this rotating secret
        type: str
        returned: always
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
      rotating_version:
        description: The current rotating secret version
        type: dict
        returned: always
        contains:
          version:
            description: Version number
            type: int
            format: int64
          values:
            description: Map of secret values for this version
            type: dict
          created_by_id:
            description: ID of the principal who created this version
            type: str
          created_at:
            description: When this version was created
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
          keys:
            description: List of available secret value keys
            type: list
            elements: str
"""

from ansible_collections.benemon.hcp_community_collection.plugins.module_utils.hcp_base import HCPLookupBase
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
        """Retrieve a rotating secret value from HVS."""
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

        # First get metadata to confirm type
        metadata_endpoint = (f"secrets/{self.api_version}/organizations/{variables['organization_id']}"
                           f"/projects/{variables['project_id']}/apps/{variables['app_name']}"
                           f"/secrets/{variables['secret_name']}")

        try:
            metadata = self._make_request('GET', metadata_endpoint, variables)
            if not metadata or 'secret' not in metadata:
                raise AnsibleError("Invalid metadata response from API")
            
            secret_type = metadata.get('secret', {}).get('type')
            if secret_type != 'rotating':
                raise AnsibleError(f"Secret '{variables['secret_name']}' is not a rotating secret (type: {secret_type})")
        except Exception as e:
            display.error(f"Error retrieving secret metadata: {str(e)}")
            raise AnsibleError(f'Error retrieving secret metadata: {str(e)}')

        # Build base endpoint
        base_endpoint = (f"secrets/{self.api_version}/organizations/{variables['organization_id']}"
                        f"/projects/{variables['project_id']}/apps/{variables['app_name']}"
                        f"/secrets/{variables['secret_name']}")

        # Use the :open endpoint to get latest version
        endpoint = f"{base_endpoint}:open"

        try:
            # Make request to get secret
            display.vvv(f"Making request to endpoint: {endpoint}")
            response = self._make_request('GET', endpoint, variables)
            
            # Validate response
            if not response or 'secret' not in response:
                display.error("Received invalid response from API")
                raise AnsibleError("Invalid or empty response from API")

            secret_data = response['secret']
            
            # Verify this is a rotating secret
            if 'rotating_version' not in secret_data:
                if 'static_version' in secret_data:
                    raise AnsibleError(
                        'Retrieved static secret - please use hvs_static_secret plugin instead'
                    )
                elif 'dynamic_instance' in secret_data:
                    raise AnsibleError(
                        'Retrieved dynamic secret - please use hvs_dynamic_secret plugin instead'
                    )
                else:
                    raise AnsibleError("Unknown secret type in response")

            display.vvv("Successfully retrieved rotating secret")
            return [secret_data]
            
        except Exception as e:
            display.error(f"Error retrieving rotating secret: {str(e)}")
            raise AnsibleError(f'Error retrieving rotating secret: {str(e)}')