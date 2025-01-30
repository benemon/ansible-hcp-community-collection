from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r"""
    name: hvs_dynamic_secret
    author: benemon
    version_added: "1.0.0"
    short_description: Retrieve a dynamic secret value from HashiCorp Vault Secrets (HVS)
    description:
        - This lookup retrieves a dynamic secret value from HashiCorp Vault Secrets (HVS)
        - Uses the API to get the secret value and metadata
        - Dynamic secrets are generated on-demand and have a defined TTL
        - For static or rotating secrets, use their dedicated lookup plugins
    options:
        organization_id:
            description: HCP Organization ID
            required: true
            type: str
        project_id:
            description: HCP Project ID
            required: true
            type: str
        app_name:
            description: Name of the app containing the secret
            required: true
            type: str
        secret_name:
            description: Name of the secret to retrieve
            required: true
            type: str
        ttl:
            description: Override the default TTL for this request
            required: false
            type: str
        hcp_token:
            description: HCP API token
            required: false
            type: str
            env:
                - name: HCP_TOKEN
        hcp_client_id:
            description: HCP Client ID for OAuth authentication
            required: false
            type: str
            env:
                - name: HCP_CLIENT_ID
        hcp_client_secret:
            description: HCP Client Secret for OAuth authentication
            required: false
            type: str
            env:
                - name: HCP_CLIENT_SECRET
"""

EXAMPLES = r"""
# Get a dynamic secret with default TTL
- name: Get dynamic AWS credentials
  debug:
    msg: "{{ lookup('benemon.hcp_community_collection.hvs_dynamic_secret',
             'organization_id=my-org-id',
             'project_id=my-project-id',
             'app_name=my-app',
             'secret_name=aws-creds') }}"

# Get a dynamic secret with custom TTL
- name: Get dynamic database credentials
  debug:
    msg: "{{ lookup('benemon.hcp_community_collection.hvs_dynamic_secret',
             'organization_id=my-org-id',
             'project_id=my-project-id',
             'app_name=my-app',
             'secret_name=db-creds',
             'ttl=2h') }}"
"""

RETURN = r"""
_raw:
    description: dictionary containing the dynamic secret data
    type: dict
    contains:
        dynamic_instance:
            description: Dynamic secret instance data
            type: dict
            contains:
                values:
                    description: The secret values
                    type: dict
                created_at:
                    description: Creation timestamp
                    type: str
                expires_at:
                    description: Expiration timestamp
                    type: str
                ttl:
                    description: Time-to-live duration
                    type: str
"""

from ansible_collections.benemon.hcp_community_collection.plugins.module_utils.base.hcp_base import HCPLookupBase
from ansible.errors import AnsibleError
from ansible.utils.display import Display
import json

display = Display()

class LookupModule(HCPLookupBase):
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