from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r"""
    name: hvs_apps
    author: benemon
    version_added: "0.0.1"
    short_description: List apps in HashiCorp Vault Secrets (HVS)
    description:
        - This lookup returns a list of apps from HashiCorp Vault Secrets (HVS)
        - Apps are organizational units within HVS that contain secrets
        - Results can be filtered and paginated
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
        name_contains:
            description: 
                - Filter apps by partial name match
                - Case-sensitive string comparison
                - Returns empty list if no matches found
            required: false
            type: str
    notes:
        - Authentication requires either an API token (hcp_token/HCP_TOKEN) or client credentials (hcp_client_id + hcp_client_secret)
        - Authentication methods cannot be mixed - use either token or client credentials
        - Environment variables take precedence over playbook parameters
        - All timestamps are returned in RFC3339 format
        - All responses are paginated by default with a default page size
        - Results are returned as a list of dictionaries
        - Empty results return an empty list rather than failing
        - Filter parameters can be combined to narrow results
    seealso:
        - module: benemon.hcp_community_collection.hvs_secrets
        - name: HVS API Documentation
          link: https://developer.hashicorp.com/hcp/api-docs/vault-secrets
"""

EXAMPLES = r"""
# List all apps using token authentication via environment variable
- environment:
    HCP_TOKEN: "hvs.thisisafaketoken..."
  ansible.builtin.debug:
    msg: "{{ lookup('benemon.hcp_community_collection.hvs_apps', 
             'organization_id=org_id',
             'project_id=proj_id') }}"

# List apps with OAuth client credentials
- ansible.builtin.debug:
    msg: "{{ lookup('benemon.hcp_community_collection.hvs_apps',
             'organization_id=org_id',
             'project_id=proj_id',
             'hcp_client_id=client_id',
             'hcp_client_secret=client_secret') }}"

# Filter apps by name pattern with pagination
- ansible.builtin.debug:
    msg: "{{ lookup('benemon.hcp_community_collection.hvs_apps',
             'organization_id=org_id',
             'project_id=proj_id',
             'name_contains=prod',
             'page_size=10',
             'max_pages=2') }}"

# Get all apps and handle empty results
- name: Get apps with error handling
  ansible.builtin.set_fact:
    hvs_apps: "{{ lookup('benemon.hcp_community_collection.hvs_apps',
                  'organization_id=org_id',
                  'project_id=proj_id') }}"
  failed_when: false

- name: Handle no apps found
  ansible.builtin.debug:
    msg: "No apps found"
  when: not hvs_apps

# Use with_items to process apps safely
- name: Process apps with error checking
  ansible.builtin.debug:
    msg: "Processing app: {{ item.name }} (created: {{ item.created_at }})"
  loop: "{{ lookup('benemon.hcp_community_collection.hvs_apps',
            'organization_id=org_id',
            'project_id=proj_id') }}"
  when: item.name is defined
  loop_control:
    label: "{{ item.name | default('unnamed app') }}"
"""

RETURN = r"""
  _list:
    description: List of apps from HVS
    type: list
    elements: dict
    contains:
      organization_id:
        description: Organization ID the app belongs to
        type: str
        returned: always
      project_id:
        description: Project ID the app belongs to  
        type: str
        returned: always
      name:
        description: Name of the app
        type: str
        returned: always
      description:
        description: Description of the app
        type: str
        returned: when set
      sync_names:
        description: List of sync names associated with the app
        type: list
        elements: str  
        returned: when set
      created_at:
        description: Timestamp when the app was created
        type: str
        format: date-time
        returned: always
      updated_at:
        description: Timestamp when the app was last updated
        type: str
        format: date-time
        returned: always  
      created_by:
        description: Principal who created the app
        type: dict
        returned: always
        contains:
          name:
            description: Name or identifier of the principal
            type: str
          type:
            description: Type of principal
            type: str
          email:
            description: Email of the principal if applicable
            type: str
      updated_by:
        description: Principal who last updated the app
        type: dict
        returned: always
        contains:
          name:
            description: Name or identifier of the principal
            type: str
          type:
            description: Type of principal
            type: str
          email:
            description: Email of the principal if applicable
            type: str
      secret_count:
        description: Total number of secrets in the app
        type: integer
        format: int32
        returned: always
      resource_name:
        description: Full resource name/path
        type: str
        returned: always
      resource_id:
        description: Unique identifier for the app
        type: str
        returned: always
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