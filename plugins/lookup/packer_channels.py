from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r"""
    name: packer_channels
    author: benemon
    version_added: "0.0.5"
    short_description: List channels from HCP Packer registry bucket
    description:
        - This lookup retrieves a list of channels from an HCP Packer registry bucket
        - Returns channel metadata and version assignments
        - Supports region-specific queries
        - Returns empty list if bucket has no channels
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
    notes:
        - Authentication requires either an API token or client credentials
        - Authentication methods cannot be mixed
        - Environment variables take precedence over parameters
        - All timestamps are returned in RFC3339 format
        - Bucket must exist in the project
        - Returns error if bucket does not exist
        - Returns empty list if bucket has no channels
        - Managed channels (like 'latest') have special behavior
    seealso:
        - module: benemon.hcp_community_collection.packer_buckets
        - module: benemon.hcp_community_collection.packer_versions
        - name: HCP Packer Documentation
          link: https://developer.hashicorp.com/packer/docs/hcp
"""

EXAMPLES = r"""
# List all channels in a bucket
- name: Get all channels
  ansible.builtin.debug:
    msg: "{{ lookup('benemon.hcp_community_collection.packer_channels',
             'organization_id=my-org-id',
             'project_id=my-project-id',
             'bucket_name=my-images') }}"

# Process channels with error handling
- name: Get channels safely
  block:
    - name: Retrieve channels
      set_fact:
        channel_list: "{{ lookup('benemon.hcp_community_collection.packer_channels',
                        'organization_id=my-org-id',
                        'project_id=my-project-id',
                        'bucket_name=my-images') }}"
    - name: Use channel info
      debug:
        msg: "Channel {{ item.name }} points to version {{ item.version.fingerprint }}"
      loop: "{{ channel_list }}"
      when: item.version is defined
  rescue:
    - name: Handle lookup failure
      debug:
        msg: "Failed to get channels from bucket"
"""

RETURN = r"""
  _list:
    description: List of channels from HCP Packer registry bucket
    type: list
    elements: dict
    contains:
      id:
        description: Unique identifier (ULID)
        type: str
        returned: always
      name:
        description: Name of the channel
        type: str
        returned: always
      bucket_name:
        description: Name of the bucket this channel belongs to
        type: str
        returned: always
      author_id:
        description: User who last updated the channel
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
      version:
        description: Currently assigned version information
        type: dict
        returned: when version is assigned
        contains:
          id:
            description: Version ULID
            type: str
            returned: always
          name:
            description: Version name
            type: str
            returned: always  
          fingerprint:
            description: Version build fingerprint
            type: str
            returned: always
      managed:
        description: Whether this is a managed channel (like 'latest')
        type: bool
        returned: always
      restricted:
        description: Whether channel access is restricted
        type: bool
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
            self.api_version = get_api_version("packer")
        except ValueError as e:
            display.error(f"Failed to get API version: {str(e)}")
            raise AnsibleError(str(e))

    def run(self, terms, variables=None, **kwargs):
        """List channels from HCP Packer registry bucket."""
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
                  f"/projects/{variables['project_id']}/buckets/{variables['bucket_name']}/channels")

        try:
            display.vvv(f"Making request to endpoint: {endpoint}")
            # Pass the query_params to _handle_pagination
            result = self._make_request("GET", endpoint, variables)
            
            channels = result.get('channels', [])
            display.vvv(f"Retrieved {len(channels)} channels")
            return [channels]
            
        except Exception as e:
            display.error(f"Error listing channels: {str(e)}")
            raise AnsibleError(f'Error listing channels: {str(e)}')