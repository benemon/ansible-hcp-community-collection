from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r"""
    name: packer_version
    author: benemon
    version_added: "0.0.3"
    short_description: Get version information from HCP Packer registry
    description:
        - This lookup retrieves version information from an HCP Packer registry bucket
        - Returns version metadata, build information, and artifact details
        - Provides status information about the version
        - Includes revocation status if applicable
        - Supports region-specific queries
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
        fingerprint:
            description:
                - Fingerprint of the version to retrieve
                - Unique identifier set during packer build
                - Must be a valid fingerprint in the specified bucket
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
        - Version must exist in the specified bucket
        - Returns error if bucket or version does not exist
        - Build information includes all artifacts and their metadata
        - Revocation status and scheduling is included when applicable
        - Template type (HCL2 or JSON) is included in response
        - Metadata includes packer, cicd, and vcs information when available
    seealso:
        - module: benemon.hcp_community_collection.packer_channel
        - name: HCP Packer Documentation
          link: https://developer.hashicorp.com/packer/docs/hcp
"""

EXAMPLES = r"""
# Get version information using token auth
- name: Get version details
  ansible.builtin.debug:
    msg: "{{ lookup('benemon.hcp_community_collection.packer_version',
             'organization_id=my-org-id',
             'project_id=my-project-id',
             'bucket_name=my-images',
             'fingerprint=abcd1234') }}"

# Process build artifacts
- name: Get AWS AMI IDs
  ansible.builtin.debug:
    msg: "AMI {{ item.external_identifier }} in region {{ item.region }}"
  vars:
    version: "{{ lookup('benemon.hcp_community_collection.packer_version',
                 'organization_id=my-org-id',
                 'project_id=my-project-id',
                 'bucket_name=my-images',
                 'fingerprint=abcd1234') }}"
  loop: "{{ version.builds | 
            selectattr('platform', 'equalto', 'aws') | 
            map(attribute='artifacts') | 
            flatten }}"
  when: version.builds is defined
  loop_control:
    label: "{{ item.region }}"

# Check build metadata
- name: Display build information
  ansible.builtin.debug:
    msg: 
      - "Built with Packer: {{ item.metadata.packer | default('unknown') }}"
      - "CI/CD: {{ item.metadata.cicd | default('unknown') }}"
      - "VCS: {{ item.metadata.vcs | default('unknown') }}"
  loop: "{{ lookup('benemon.hcp_community_collection.packer_version',
            'organization_id=my-org-id',
            'project_id=my-project-id',
            'bucket_name=my-images',
            'fingerprint=abcd1234').builds }}"
  when: item.metadata is defined
  loop_control:
    label: "Build {{ item.id }}"
"""

RETURN = r"""
  _list:
    description: Version information from HCP Packer
    type: list
    elements: dict
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
        description: Current state of the version (VERSION_UNSET, VERSION_RUNNING, VERSION_CANCELLED, VERSION_FAILED, VERSION_REVOKED, VERSION_REVOCATION_SCHEDULED, VERSION_ACTIVE, VERSION_INCOMPLETE)
        type: str
        returned: always
      author_id:
        description: Author's ID who created this version
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
        description: Fingerprint of the version set by Packer
        type: str
        returned: always
      builds:
        description: List of builds associated with this version
        type: list
        elements: dict
        returned: always
        contains:
          id:
            description: Unique identifier (ULID)
            type: str
          version_id:
            description: ID of the version this build belongs to
            type: str
          component_type:
            description: Internal Packer name for the builder or post-processor component
            type: str
          packer_run_uuid:
            description: UUID specific to this Packer build run
            type: str
          artifacts:
            description: List of artifacts created by this build
            type: list
            elements: dict
            contains:
              id:
                description: Unique identifier (ULID)
                type: str
              external_identifier:
                description: ID or URL of the remote artifact
                type: str
              region:
                description: External region as provided by Packer build
                type: str
              created_at:
                description: Creation timestamp
                type: str
                format: date-time
          platform:
            description: Platform that this build produced artifacts for
            type: str
          status:
            description: Current state of the build
            type: str
          created_at:
            description: Creation timestamp
            type: str
            format: date-time
          updated_at:
            description: Last update timestamp
            type: str
            format: date-time
          source_external_identifier:
            description: ID or URL of the remote cloud source artifact
            type: str
          labels:
            description: Key:value map for custom metadata about the build
            type: dict
          metadata:
            description: Build process information set by Packer
            type: dict
            contains:
              packer:
                description: Information about Packer version, plugins, and OS
                type: dict
              cicd:
                description: Information about the CICD pipeline
                type: dict
              vcs:
                description: Information about the version control system
                type: dict
      has_descendants:
        description: Whether this version has child versions
        type: bool
        returned: always
      template_type:
        description: Type of Packer configuration template used (TEMPLATE_TYPE_UNSET, HCL2, JSON)
        type: str
        returned: always
      revoke_at:
        description: When this version is scheduled to be revoked
        type: str
        format: date-time
        returned: when set
      revocation_message:
        description: Reason for revocation
        type: str
        returned: when revoked
      revocation_author:
        description: Who revoked this version
        type: str
        returned: when revoked
      revocation_type:
        description: Type of revocation (MANUAL or INHERITED)
        type: str
        returned: when revoked
      revocation_inherited_from:
        description: Ancestor version from whom this version inherited the revocation
        type: dict
        returned: when revocation inherited
        contains:
          href:
            description: URL to get the revoked ancestor
            type: str
          bucket_name:
            description: The revoked ancestor bucket name
            type: str
          version_name:
            description: The revoked ancestor version name
            type: str
          version_id:
            description: The revoked ancestor version ULID
            type: str
          version_fingerprint:
            description: The revoked ancestor version fingerprint
            type: str
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
            self.api_version = get_api_version("packer")  # Fetch API version dynamically
        except ValueError as e:
            display.error(f"Failed to get API version: {str(e)}")
            raise AnsibleError(str(e))  # Convert to AnsibleError for better error reporting
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


        try:
            display.vvv(f"Making request to endpoint: {endpoint}")
            result = self._make_request('GET', endpoint, variables)
            
            # Extract version information from response
            version = result.get('version', {})
            display.vvv(f"Retrieved version information for fingerprint: {variables['fingerprint']}")
            
            # Return as a list containing a single item (required for lookup plugin)
            return [version]
            
        except Exception as e:
            display.error(f"Error getting version information: {str(e)}")
            raise AnsibleError(f'Error getting version information: {str(e)}')