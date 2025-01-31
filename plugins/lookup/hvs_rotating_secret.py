from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r"""
    name: hvs_rotating_secret
    author: benemon
    version_added: "1.0.0"
    short_description: Retrieve a rotating secret value from HashiCorp Vault Secrets (HVS)
    description:
        - This lookup retrieves a rotating secret value from HashiCorp Vault Secrets (HVS)
        - Uses the :open endpoint to get the decrypted secret value
        - Rotating secrets are automatically rotated on a schedule and maintain previous versions
        - For static or dynamic secrets, use their dedicated lookup plugins
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
            description: Name of the app containing the secret
            required: True
            type: str
        secret_name:
            description: Name of the secret to retrieve
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

    notes:
        - Authentication can be provided either via token (hcp_token/HCP_TOKEN) or client credentials
          (hcp_client_id + hcp_client_secret or HCP_CLIENT_ID + HCP_CLIENT_SECRET)
        - Environment variables take precedence over playbook variables
        - For non-rotating secrets, use hvs_static_secret or hvs_dynamic_secret plugins
"""

EXAMPLES = r"""
# Retrieve latest version of a rotating secret
- ansible.builtin.debug:
    msg: "{{ lookup('benemon.hcp_community_collection.hvs_rotating_secret', 
             organization_id=org_id,
             project_id=proj_id,
             app_name='my-app',
             secret_name='database_credentials') }}"



# Use rotating credentials in a configuration
- name: Configure application with rotating credentials
  ansible.builtin.template:
    src: app-config.j2
    dest: /etc/myapp/config.yml
  vars:
    credentials: "{{ lookup('benemon.hcp_community_collection.hvs_rotating_secret',
                    organization_id=org_id,
                    project_id=proj_id,
                    app_name='my-app',
                    secret_name='service_account') }}"
"""

RETURN = r"""
  _list:
    description: Complete secret data as returned by the HVS API
    type: list
    elements: dict
    contains:
      rotating_version:
        description: Rotating secret data
        type: dict
        returned: always
        contains:
          values:
            description: Dictionary of secret values
            type: dict
          version:
            description: Version number
            type: int
          created_at:
            description: Creation timestamp
            type: str
          expires_at:
            description: When this version expires
            type: str
          revoked_at:
            description: When this version was revoked (if applicable)
            type: str
          keys:
            description: List of available secret keys
            type: list
            elements: str
"""

from ansible_collections.benemon.hcp_community_collection.plugins.module_utils.base.hcp_base import HCPLookupBase
from ansible.errors import AnsibleError
from ansible.utils.display import Display
import json

display = Display()

class LookupModule(HCPLookupBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.api_version = "2023-11-28"
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