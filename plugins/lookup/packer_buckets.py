from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r"""
    name: packer_buckets
    author: benemon
    version_added: "0.0.5"
    short_description: List buckets from HCP Packer registry
    description:
        - This lookup retrieves a list of buckets from HCP Packer registry
        - Returns bucket metadata including latest version information if available
        - Supports pagination and region-specific queries
        - Results can be sorted using order_by parameter
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
                - Cannot be used together with client credentials
            required: false
            type: str
            env:
                - name: HCP_TOKEN
        hcp_client_id:
            description:
                - HCP Client ID for OAuth authentication
                - Can be specified via HCP_CLIENT_ID environment variable
                - Must be used together with hcp_client_secret
            required: false
            type: str
            env:
                - name: HCP_CLIENT_ID
        hcp_client_secret:
            description:
                - HCP Client Secret for OAuth authentication
                - Can be specified via HCP_CLIENT_SECRET environment variable
                - Must be used together with hcp_client_id
            required: false
            type: str
            env:
                - name: HCP_CLIENT_SECRET
        page_size:
            description: 
                - Number of results to return per page
                - Defaults to service-defined value if not specified
            required: false
            type: int
        max_pages:
            description:
                - Maximum number of pages to retrieve
                - Use with page_size to limit total results
            required: false
            type: int
        disable_pagination:
            description: 
                - If True, returns only the first page of results
                - Overrides max_pages if set
            required: false
            type: bool
            default: false
        location_region_provider:
            description:
                - Cloud provider for the region
                - Examples - "aws", "gcp", "azure"
            required: false
            type: str
        location_region_region:
            description:
                - Cloud region identifier
                - Examples - "us-west1", "us-east1"
                - Must be valid region for specified provider
            required: false
            type: str
        order_by:
            description:
                - List of fields to sort results by
                - Format - field1,field2 desc,field3 asc
                - Default order is ascending
            required: false
            type: list
            elements: str
    notes:
        - Authentication requires either an API token or client credentials
        - Authentication methods cannot be mixed
        - Environment variables take precedence over parameters
        - All timestamps are returned in RFC3339 format
        - Sorting fields must be immutable, unique and orderable
        - Multiple sort fields can be used for tie-breaking
        - Returns empty list if no buckets exist
    seealso:
        - module: benemon.hcp_community_collection.packer_channel
        - module: benemon.hcp_community_collection.packer_version
        - name: HCP Packer Documentation
          link: https://developer.hashicorp.com/packer/docs/hcp
"""

EXAMPLES = r"""
# List all buckets using token auth
- name: Get all buckets
  ansible.builtin.debug:
    msg: "{{ lookup('benemon.hcp_community_collection.packer_buckets',
             'organization_id=my-org-id',
             'project_id=my-project-id') }}"

# List buckets with pagination
- name: Get paginated buckets
  ansible.builtin.debug:
    msg: "{{ lookup('benemon.hcp_community_collection.packer_buckets',
             'organization_id=my-org-id',
             'project_id=my-project-id',
             'page_size=10',
             'max_pages=2') }}"

# Sort buckets by name descending
- name: Get sorted buckets
  ansible.builtin.debug:
    msg: "{{ lookup('benemon.hcp_community_collection.packer_buckets',
             'organization_id=my-org-id',
             'project_id=my-project-id',
             'order_by=name desc') }}"

# Process buckets with error handling
- name: Get buckets safely
  block:
    - name: Retrieve buckets
      set_fact:
        bucket_list: "{{ lookup('benemon.hcp_community_collection.packer_buckets',
                       'organization_id=my-org-id',
                       'project_id=my-project-id') }}"
    - name: Use bucket info
      debug:
        msg: "Bucket {{ item.name }} has {{ item.version_count }} versions"
      loop: "{{ bucket_list }}"
      when: item.name is defined
  rescue:
    - name: Handle lookup failure
      debug:
        msg: "Failed to retrieve buckets"
"""

RETURN = r"""
  _list:
    description: List of buckets from HCP Packer registry
    type: list
    elements: dict
    contains:
      id:
        description: Unique identifier (ULID)
        type: str
        returned: always
      name:
        description: Human-readable name for the bucket
        type: str
        returned: always
      location:
        description: Location information
        type: dict
        returned: always
        contains:
          organization_id:
            description: Organization ID
            type: str
          project_id:
            description: Project ID
            type: str
          region:
            description: Region details if specified
            type: dict
            returned: when region filters used
      latest_version:
        description: Most recent valid version
        type: dict
        returned: when version exists
      created_at:
        description: Creation timestamp
        type: str
        format: date-time
        returned: always
      updated_at:
        description: Last update timestamp
        type: str
        format: date-time
        returned: always
      platforms:
        description: List of cloud providers included in latest version
        type: list
        elements: str
        returned: when platforms exist
      description:
        description: Short description of bucket purpose
        type: str
        returned: when set
      labels:
        description: User-defined metadata key-value pairs
        type: dict
        returned: when set
      version_count:
        description: Total number of versions
        type: str
        format: int64
        returned: always
      parents:
        description: Information about bucket's parents
        type: dict
        returned: always
      children:
        description: Information about bucket's children
        type: dict
        returned: always
      resource_name:
        description: Human-readable resource identifier
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
            self.api_version = get_api_version("packer")
        except ValueError as e:
            display.error(f"Failed to get API version: {str(e)}")
            raise AnsibleError(str(e))

    def run(self, terms, variables=None, **kwargs):
        """List buckets from HCP Packer registry."""
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
        endpoint = (f"packer/{self.api_version}/organizations/{variables['organization_id']}"
                  f"/projects/{variables['project_id']}/buckets")

        # Process optional parameters
        params = {}

        if 'order_by' in variables:
            # Pass the order_by string directly - it should already be in correct format
            params['sorting.order_by'] = variables['order_by']

        try:
            display.vvv(f"Making request to endpoint: {endpoint}")
            result = self._handle_pagination(endpoint, variables, params)
            
            buckets = result.get('results', [])
            display.vvv(f"Retrieved {len(buckets)} buckets")
            
            return [buckets]
            
        except Exception as e:
            display.error(f"Error listing buckets: {str(e)}")
            raise AnsibleError(f'Error listing buckets: {str(e)}')