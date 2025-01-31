from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r"""
    name: packer_version
    author: benemon
    version_added: "1.0.0"
    short_description: Get version information from HCP Packer registry
    description:
        - This lookup retrieves version information for a specific version in an HCP Packer registry bucket
        - Returns details about the version including its status, builds, and metadata
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
        fingerprint:
            description: Fingerprint of the version to retrieve
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
# Get version information using token authentication via environment variable
- environment:
    HCP_TOKEN: "hcp.thisisafaketoken..."
  ansible.builtin.debug:
    msg: "{{ lookup('benemon.hcp_community_collection.packer_version', 
             organization_id=org_id,
             project_id=proj_id,
             bucket_name='my-images',
             fingerprint='abcd1234') }}"

# Get version information with token authentication via playbook variable
- ansible.builtin.debug:
    msg: "{{ lookup('benemon.hcp_community_collection.packer_version',
             organization_id=org_id,
             project_id=proj_id,
             bucket_name='my-images',
             fingerprint='abcd1234',
             hcp_token=my_token_var) }}"

# Get version from specific region
- ansible.builtin.debug:
    msg: "{{ lookup('benemon.hcp_community_collection.packer_version',
             organization_id=org_id,
             project_id=proj_id,
             bucket_name='my-images',
             fingerprint='abcd1234',
             location_region_provider='aws',
             location_region_region='us-west-1') }}"

# Store version information for later use
- name: Get version details and store for later
  ansible.builtin.set_fact:
    version_info: "{{ lookup('benemon.hcp_community_collection.packer_version',
                     organization_id=org_id,
                     project_id=proj_id,
                     bucket_name='my-images',
                     fingerprint='abcd1234') }}"
"""

RETURN = r"""
  _raw:
    description: Version information from HCP Packer
    type: dict
    contains:
      id:
        description: Unique identifier (ULID)
        type: str
        returned: always
      bucket_name:
        description: Name of the bucket containing this version
        type: str
        returned: always
      name:
        description: Human-readable name of the version
        type: str
        returned: always
      status:
        description: Current state of the version (e.g., VERSION_ACTIVE)
        type: str
        returned: always
      fingerprint:
        description: Fingerprint of the version set by Packer
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
      builds:
        description: List of builds associated with this version
        type: list
        returned: always
        contains:
          id:
            description: Build identifier
            type: str
          version_id:
            description: Version identifier
            type: str
          component_type:
            description: Type of builder or post-processor
            type: str
          status:
            description: Build status
            type: str
          artifacts:
            description: List of artifacts created by this build
            type: list
            contains:
              id:
                description: Artifact identifier
                type: str
              external_identifier:
                description: External resource identifier (e.g. AMI ID)
                type: str
              region:
                description: Region where artifact exists
                type: str
      has_descendants:
        description: Whether this version has child versions
        type: bool
        returned: always
      template_type:
        description: Type of Packer template used (HCL2 or JSON)
        type: str
        returned: when set
      revoke_at:
        description: Scheduled revocation timestamp
        type: str
        returned: when set
      revocation_message:
        description: Explanation for revocation
        type: str
        returned: when set
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
        """Get version information from HCP Packer registry."""
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
                'fingerprint'
            ])
        except AnsibleError as e:
            display.error(f"Parameter validation failed: {str(e)}")
            raise

        # Build endpoint
        endpoint = (f"packer/{self.api_version}/organizations/{variables['organization_id']}"
                   f"/projects/{variables['project_id']}/buckets/{variables['bucket_name']}"
                   f"/versions/{variables['fingerprint']}")

        # Process optional region parameters
        params = {}
        if 'location_region_provider' in variables:
            params['location.region.provider'] = variables['location_region_provider']
        if 'location_region_region' in variables:
            params['location.region.region'] = variables['location_region_region']

        try:
            display.vvv(f"Making request to endpoint: {endpoint}")
            result = self._make_request('GET', endpoint, variables, params)
            
            # Extract version information from response
            version = result.get('version', {})
            display.vvv(f"Retrieved version information for fingerprint: {variables['fingerprint']}")
            
            # Return as a list containing a single item (required for lookup plugin)
            return [version]
            
        except Exception as e:
            display.error(f"Error getting version information: {str(e)}")
            raise AnsibleError(f'Error getting version information: {str(e)}')