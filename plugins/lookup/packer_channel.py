from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r"""
    name: packer_channel
    author: benemon
    version_added: "0.0.3"
    short_description: Get channel information from HCP Packer registry
    description:
        - This lookup retrieves information about a channel in an HCP Packer registry bucket
        - Returns channel metadata and current version assignment if any
        - Channels provide a way to track specific versions of Packer builds
        - Supports region-specific queries
        - Returns error if channel or bucket does not exist
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
        channel_name:
            description:
                - Name of the channel to retrieve
                - Must exist in the specified bucket
                - Case-sensitive
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
        - Channel must exist in the specified bucket
        - Region filters are optional but must be valid if specified
        - Returns error if bucket or channel does not exist
        - Managed channels (like 'latest') have special behavior
        - Restricted channels may have limited access
    seealso:
        - module: benemon.hcp_community_collection.packer_version
        - name: HCP Packer Documentation
          link: https://developer.hashicorp.com/packer/docs/hcp
"""

EXAMPLES = r"""
# Get channel information using token auth
- name: Get production channel info
  ansible.builtin.debug:
    msg: "{{ lookup('benemon.hcp_community_collection.packer_channel',
             'organization_id=my-org-id',
             'project_id=my-project-id',
             'bucket_name=my-images',
             'channel_name=production') }}"

# Get channel info with error handling
- name: Get channel with validation
  block:
    - name: Retrieve channel
      set_fact:
        channel_info: "{{ lookup('benemon.hcp_community_collection.packer_channel',
                         'organization_id=my-org-id',
                         'project_id=my-project-id',
                         'bucket_name=my-images',
                         'channel_name=staging') }}"
    - name: Check if version is assigned
      debug:
        msg: "Channel has version {{ channel_info.version.fingerprint }} assigned"
      when: channel_info.version is defined
  rescue:
    - name: Handle lookup failure
      debug:
        msg: "Failed to retrieve channel information"

# Use channel info for configuration
- name: Configure with channel version
  ansible.builtin.template:
    src: config.j2
    dest: /etc/myapp/image-config.yml
    mode: '0644'
  vars:
    channel: "{{ lookup('benemon.hcp_community_collection.packer_channel',
                 'organization_id=my-org-id',
                 'project_id=my-project-id',
                 'bucket_name=my-images',
                 'channel_name=production') }}"
  when: 
    - channel.version is defined
    - channel.version.fingerprint is defined
"""

RETURN = r"""
  _list:
    description: Channel information from HCP Packer
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
        description: Whether this channel is managed by HCP Packer (such as the latest channel)
        type: bool
        returned: always
      restricted:
        description: Whether this channel's access is restricted to users with write permission
        type: bool
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
            self.api_version = get_api_version("packer")  # Fetch API version dynamically
        except ValueError as e:
            display.error(f"Failed to get API version: {str(e)}")
            raise AnsibleError(str(e))  # Convert to AnsibleError for better error reporting
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

        try:
            display.vvv(f"Making request to endpoint: {endpoint}")
            result = self._make_request('GET', endpoint, variables)
            
            # Extract channel information from response
            channel = result.get('channel', {})
            display.vvv(f"Retrieved channel information for: {variables['channel_name']}")
            
            # Return as a list containing a single item (required for lookup plugin)
            return [channel]
            
        except Exception as e:
            display.error(f"Error getting channel information: {str(e)}")
            raise AnsibleError(f'Error getting channel information: {str(e)}')