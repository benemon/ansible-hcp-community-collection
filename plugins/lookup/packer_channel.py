from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r"""
    name: packer_channel
    author: benemon
    version_added: "1.0.0"
    short_description: Get channel information from HCP Packer registry
    description:
        - This lookup retrieves information about a channel in an HCP Packer registry bucket
        - Returns details about the channel and its currently assigned version if any
    options:
        organization_id:
            description: HCP Organization ID
            required: True
            type: str
        project_id:
            description: HCP Project ID
            required: True
            type: str
        bucket_name:
            description: Name of the Packer bucket
            required: True
            type: str
        channel_name:
            description: Name of the channel to retrieve
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
        location_region_provider:
            description: Cloud provider for the region (e.g. "aws", "gcp", "azure")
            required: False
            type: str
        location_region_region:
            description: Cloud region (e.g. "us-west1", "us-east1")
            required: False
            type: str
    notes:
        - Authentication can be provided either via token (hcp_token/HCP_TOKEN) or client credentials
          (hcp_client_id + hcp_client_secret or HCP_CLIENT_ID + HCP_CLIENT_SECRET)
        - Environment variables take precedence over playbook variables
"""

EXAMPLES = r"""
# Get channel information using token authentication via environment variable
- environment:
    HCP_TOKEN: "hcp.thisisafaketoken..."
  ansible.builtin.debug:
    msg: "{{ lookup('benemon.hcp_community_collection.packer_channel', 
             organization_id=org_id,
             project_id=proj_id,
             bucket_name='my-images',
             channel_name='production') }}"

# Get channel information with token authentication via playbook variable
- ansible.builtin.debug:
    msg: "{{ lookup('benemon.hcp_community_collection.packer_channel',
             organization_id=org_id,
             project_id=proj_id,
             bucket_name='my-images',
             channel_name='production',
             hcp_token=my_token_var) }}"

# Get channel from specific region
- ansible.builtin.debug:
    msg: "{{ lookup('benemon.hcp_community_collection.packer_channel',
             organization_id=org_id,
             project_id=proj_id,
             bucket_name='my-images',
             channel_name='production',
             location_region_provider='aws',
             location_region_region='us-west-1') }}"

# Store channel information for later use
- name: Get channel details and store for later
  ansible.builtin.set_fact:
    channel_info: "{{ lookup('benemon.hcp_community_collection.packer_channel',
                     organization_id=org_id,
                     project_id=proj_id,
                     bucket_name='my-images',
                     channel_name='production') }}"
"""

RETURN = r"""
  _raw:
    description: Channel information from HCP Packer
    type: dict
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
      created_at:
        description: Creation timestamp
        type: str
        returned: always
      updated_at:
        description: Last update timestamp
        type: str
        returned: always
      version:
        description: Information about the currently assigned version
        type: dict
        returned: when version is assigned
        contains:
          id:
            description: Version ID
            type: str
          name:
            description: Version name
            type: str
          fingerprint:
            description: Version fingerprint
            type: str
      managed:
        description: Whether the channel is managed by HCP Packer
        type: bool
        returned: always
      restricted:
        description: Whether access to the channel is restricted
        type: bool
        returned: always
      author_id:
        description: ID of user who last updated the channel
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
        self.api_version = "2023-01-01"
    def run(self, terms, variables=None, **kwargs):
        """Get channel information from HCP Packer registry."""
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
                'bucket_name',
                'channel_name'
            ])
        except AnsibleError as e:
            display.error(f"Parameter validation failed: {str(e)}")
            raise

        # Build endpoint
        endpoint = (f"packer/2023-01-01/organizations/{variables['organization_id']}"
                   f"/projects/{variables['project_id']}/buckets/{variables['bucket_name']}"
                   f"/channels/{variables['channel_name']}")

        # Process optional region parameters
        params = {}
        if 'location_region_provider' in variables:
            params['location.region.provider'] = variables['location_region_provider']
        if 'location_region_region' in variables:
            params['location.region.region'] = variables['location_region_region']

        try:
            display.vvv(f"Making request to endpoint: {endpoint}")
            result = self._make_request('GET', endpoint, variables, params)
            
            # Extract channel information from response
            channel = result.get('channel', {})
            display.vvv(f"Retrieved channel information for: {variables['channel_name']}")
            
            # Return as a list containing a single item (required for lookup plugin)
            return [channel]
            
        except Exception as e:
            display.error(f"Error getting channel information: {str(e)}")
            raise AnsibleError(f'Error getting channel information: {str(e)}')