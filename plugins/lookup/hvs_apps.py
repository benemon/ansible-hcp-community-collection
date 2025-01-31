from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r"""
    name: hvs_apps
    author: benemon
    version_added: "1.0.0"
    short_description: List apps in HashiCorp Vault Secrets (HVS)
    description:
        - This lookup returns a list of apps from HashiCorp Vault Secrets (HVS)
        - Apps are organizational units within HVS that contain secrets
    options:
        organization_id:
            description: HCP Organization ID
            required: True
            type: str
        project_id:
            description: HCP Project ID
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
            description: Filter apps by name pattern
            required: False
            type: str
    notes:
        - Authentication can be provided either via token (hcp_token/HCP_TOKEN) or client credentials
          (hcp_client_id + hcp_client_secret or HCP_CLIENT_ID + HCP_CLIENT_SECRET)
        - Environment variables take precedence over playbook variables
        - Returns all apps by default; use filters to limit results
"""

EXAMPLES = r"""
# List all apps using token authentication via environment variable
- environment:
    HCP_TOKEN: "hvs.thisisafaketoken..."
  ansible.builtin.debug:
    msg: "{{ lookup('benemon.hcp_community_collection.hvs_apps', 
             organization_id=org_id,
             project_id=proj_id) }}"

# List apps with token authentication via playbook variable
- ansible.builtin.debug:
    msg: "{{ lookup('benemon.hcp_community_collection.hvs_apps',
             organization_id=org_id,
             project_id=proj_id,
             hcp_token=my_token_var) }}"

# List apps using OAuth client credentials
- ansible.builtin.debug:
    msg: "{{ lookup('benemon.hcp_community_collection.hvs_apps',
             organization_id=org_id,
             project_id=proj_id,
             hcp_client_id=client_id,
             hcp_client_secret=client_secret) }}"

# Filter apps by name pattern
- ansible.builtin.debug:
    msg: "{{ lookup('benemon.hcp_community_collection.hvs_apps',
             organization_id=org_id,
             project_id=proj_id,
             name_contains='prod') }}"

# Limit results with pagination
- ansible.builtin.debug:
    msg: "{{ lookup('benemon.hcp_community_collection.hvs_apps',
             organization_id=org_id,
             project_id=proj_id,
             page_size=10,
             max_pages=2) }}"

# Store app information for later use
- name: Get list of apps and store for later
  ansible.builtin.set_fact:
    hvs_apps: "{{ lookup('benemon.hcp_community_collection.hvs_apps',
                  organization_id=org_id,
                  project_id=proj_id) }}"

# Use with_items to iterate over apps
- name: Print app names
  ansible.builtin.debug:
    msg: "Found app: {{ item.name }}"
  with_items: "{{ lookup('benemon.hcp_community_collection.hvs_apps',
                  organization_id=org_id,
                  project_id=proj_id) }}"
"""

RETURN = r"""
  _list:
    description: List of apps from HVS
    type: list
    elements: dict
    contains:
      name:
        description: Name of the app
        type: str
        returned: always
      description:
        description: Description of the app
        type: str
        returned: when set
      organization_id:
        description: Organization ID the app belongs to
        type: str
        returned: always
      project_id:
        description: Project ID the app belongs to
        type: str
        returned: always
      created_at:
        description: Timestamp when the app was created
        type: str
        returned: always
      updated_at:
        description: Timestamp when the app was last updated
        type: str
        returned: always
      created_by:
        description: Information about who created the app
        type: dict
        returned: always
        contains:
          name:
            description: Name of the creator
            type: str
          type:
            description: Type of principal who created the app
            type: str
          email:
            description: Email of the creator
            type: str
      updated_by:
        description: Information about who last updated the app
        type: dict
        returned: always
        contains:
          name:
            description: Name of the updater
            type: str
          type:
            description: Type of principal who updated the app
            type: str
          email:
            description: Email of the updater
            type: str
      sync_names:
        description: List of sync configurations associated with the app
        type: list
        elements: str
        returned: when configured
      secret_count:
        description: Number of secrets in the app
        type: int
        returned: always
      resource_name:
        description: Full resource name of the app
        type: str
        returned: always
      resource_id:
        description: Unique identifier for the app
        type: str
        returned: always
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
        """List apps in HashiCorp Vault Secrets."""
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
                'project_id'
            ])
        except AnsibleError as e:
            display.error(f"Parameter validation failed: {str(e)}")
            raise

        # Build endpoint
        endpoint = (f"secrets/{self.api_version}/organizations/{variables['organization_id']}"
                   f"/projects/{variables['project_id']}/apps")

        try:
            # The base class now handles all parameter processing
            display.vvv(f"Making request to endpoint: {endpoint}")
            result = self._handle_pagination(endpoint, variables)
            
            # Ensure we always return a list, even if empty
            apps = result.get('results', [])
            display.vvv(f"Retrieved {len(apps)} apps")
            return [apps]
            
        except Exception as e:
            display.error(f"Error listing apps: {str(e)}")
            raise AnsibleError(f'Error listing apps: {str(e)}')