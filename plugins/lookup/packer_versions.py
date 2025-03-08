from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r"""
    name: packer_versions
    author: benemon
    version_added: "0.0.5"
    short_description: List versions from HCP Packer registry bucket
    description:
        - This lookup retrieves a list of versions from an HCP Packer registry bucket
        - Returns version metadata including build information
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
        bucket_name:
            description:
                - Name of the Packer registry bucket
                - Must exist in the project
                - Case-sensitive
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
        - Bucket must exist in the project
        - Returns error if bucket does not exist
        - Returns empty list if bucket has no versions
        - Sorting fields must be immutable, unique and orderable
        - Multiple sort fields can be used for tie-breaking
    seealso:
        - module: benemon.hcp_community_collection.packer_buckets
        - module: benemon.hcp_community_collection.packer_channels
        - name: HCP Packer Documentation
          link: https://developer.hashicorp.com/packer/docs/hcp
"""

EXAMPLES = r"""
# List all versions in a bucket
- name: Get all versions
  ansible.builtin.debug:
    msg: "{{ lookup('benemon.hcp_community_collection.packer_versions',
             'organization_id=my-org-id',
             'project_id=my-project-id',
             'bucket_name=my-images') }}"

# List versions with pagination
- name: Get paginated versions
  ansible.builtin.debug:
    msg: "{{ lookup('benemon.hcp_community_collection.packer_versions',
             'organization_id=my-org-id',
             'project_id=my-project-id',
             'bucket_name=my-images',
             'page_size=10',
             'max_pages=2') }}"

# List versions with sorting
- name: Get sorted versions
  ansible.builtin.debug:
    msg: "{{ lookup('benemon.hcp_community_collection.packer_versions',
             'organization_id=my-org-id',
             'project_id=my-project-id',
             'bucket_name=my-images',
             'order_by=name desc') }}"

# Process versions with error handling
- name: Get versions safely
  block:
    - name: Retrieve versions
      set_fact:
        version_list: "{{ lookup('benemon.hcp_community_collection.packer_versions',
                        'organization_id=my-org-id',
                        'project_id=my-project-id',
                        'bucket_name=my-images') }}"
    - name: Use version info
      debug:
        msg: "Version {{ item.fingerprint }} has {{ item.builds | length }} builds"
      loop: "{{ version_list }}"
      when: item.builds is defined
  rescue:
    - name: Handle lookup failure
      debug:
        msg: "Failed to get versions from bucket"
"""

RETURN = r"""
  _list:
    description: List of versions from HCP Packer registry bucket
    type: list
    elements: dict
    contains:
      id:
        description: Unique identifier (ULID)
        type: str
        returned: always
      bucket_name:
        description: Name of the bucket this version belongs to
        type: str
        returned: always
      name:
        description: Name of the version
        type: str
        returned: always
      status:
        description: Current state of the version
        type: str
        returned: always
      author_id:
        description: Name of the author who created this version
        type: str
        returned: always
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
      fingerprint:
        description: Version fingerprint from Packer build
        type: str
        returned: always
      builds:
        description: List of builds associated with this version
        type: list
        elements: dict
        returned: when builds exist
      revoke_at:
        description: Timestamp when version will be revoked
        type: str
        format: date-time
        returned: when revocation scheduled
      revocation_message:
        description: Explanation for revocation
        type: str
        returned: when revoked
      revocation_author:
        description: Who revoked the version
        type: str
        returned: when revoked
      revocation_type:
        description: Type of revocation (manual/inherited)
        type: str
        returned: when revoked
      revocation_inherited_from:
        description: Parent version that caused revocation
        type: dict
        returned: when revocation inherited
      has_descendants:
        description: If version has child versions
        type: bool
        returned: always
      template_type:
        description: Type of Packer template used
        type: str
        returned: always
      parents:
        description: Information about version's parents
        type: dict
        returned: always
"""

from ansible_collections.benemon.hcp_community_collection.plugins.module_utils.hcp_lookup import HCPLookup
from ansible_collections.benemon.hcp_community_collection.plugins.module_utils.api_versions import get_api_version
from ansible.errors import AnsibleError
from ansible.utils.display import Display
import json

display = Display()

class LookupModule(HCPLookup):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            self.api_version = get_api_version("packer")
        except ValueError as e:
            display.error(f"Failed to get API version: {str(e)}")
            raise AnsibleError(str(e))

    def run(self, terms, variables=None, **kwargs):
        """List versions from HCP Packer registry bucket."""
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
                'bucket_name'
            ])
        except AnsibleError as e:
            display.error(f"Parameter validation failed: {str(e)}")
            raise

        # Build endpoint
        endpoint = (f"packer/{self.api_version}/organizations/{variables['organization_id']}"
                  f"/projects/{variables['project_id']}/buckets/{variables['bucket_name']}/versions")

        try:
            # Process optional filter and sort parameters
            params = {}
                
            # Add sorting if specified
            if 'order_by' in variables:
                params['sorting.order_by'] = variables['order_by']

            display.vvv(f"Making request to endpoint: {endpoint}")
            result = self._handle_pagination(endpoint, variables, params)
            
            # Extract versions and wrap in list to match other lookup patterns
            versions = result.get('results', [])
            display.vvv(f"Retrieved {len(versions)} versions")
            return [versions]
            
        except Exception as e:
            display.error(f"Error listing versions: {str(e)}")
            raise AnsibleError(f'Error listing versions: {str(e)}')