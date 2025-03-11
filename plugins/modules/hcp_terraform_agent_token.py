#!/usr/bin/python
DOCUMENTATION = """
---
module: hcp_terraform_agent_token
short_description: Manages HCP Terraform agent tokens
description:
  - Creates and deletes agent tokens in HCP Terraform.
  - Agent tokens are used to authenticate self-hosted agents with HCP Terraform.
  - The token is only shown upon creation and cannot be retrieved later.
author: "benemon"
options:
  token:
    description: "HCP Terraform API token. This can be set via the TFE_TOKEN environment variable."
    required: true
    type: str
    no_log: true
  hostname:
    description: "Hostname for the Terraform API (Terraform Cloud or Terraform Enterprise). This can be set via the TFE_HOSTNAME environment variable."
    required: false
    type: str
    default: "https://app.terraform.io"
  agent_pool_id:
    description: "ID of the agent pool to manage tokens for."
    required: true
    type: str
  description:
    description: "Description of the agent token."
    required: false
    type: str
    default: "Created by Ansible"
  token_id:
    description: "ID of the agent token to delete. Required when state=absent."
    required: false
    type: str
  state:
    description: "Whether the agent token should exist or not."
    required: false
    choices: ["present", "absent"]
    default: "present"
    type: str
notes:
  - "The token is only returned once when created and cannot be retrieved later."
  - "You should store the created token securely for use with agent setup."
  - "HCP Terraform Free Edition includes one self-hosted agent."
"""

EXAMPLES = """
- name: Create an agent token
  benemon.hcp_community_collection.hcp_terraform_agent_token:
    token: "{{ lookup('env', 'TFE_TOKEN') }}"
    agent_pool_id: "apool-yoGUFz5zcRMMz53i"
    description: "Token for CI/CD pipeline agents"
  register: token_result
  
- name: Store the agent token securely
  ansible.builtin.set_fact:
    agent_token: "{{ token_result.agent_token.token }}"
    
- name: Use the agent token in agent configuration
  ansible.builtin.template:
    src: agent-config.j2
    dest: /etc/tfc-agent/config.hcl
  vars:
    agent_token: "{{ agent_token }}"
    
- name: Remove an agent token
  benemon.hcp_community_collection.hcp_terraform_agent_token:
    token: "{{ lookup('env', 'TFE_TOKEN') }}"
    agent_pool_id: "apool-yoGUFz5zcRMMz53i"
    token_id: "at-bonpPzYqv2bGD7vr"
    state: "absent"
"""

RETURN = """
agent_token:
  description: "Details of the agent token."
  returned: when state=present
  type: dict
  contains:
    id:
      description: "The ID of the agent token."
      type: str
      sample: "at-bonpPzYqv2bGD7vr"
    token:
      description: "The token string. Only available when created."
      type: str
      sample: "eHub7TsW7fz7LQ.atlasv1.cHGFcvf2VxVfUH4PZ7UNdaGB6SjyKWs5phdZ371z"
    description:
      description: "The description of the token."
      type: str
      sample: "Created by Ansible"
    created_at:
      description: "When the token was created."
      type: str
      sample: "2021-05-15T18:24:16.591Z"
result:
  description: "Raw API response from HCP Terraform."
  returned: always
  type: dict
  contains:
    data:
      description: "Information about the agent token."
      type: dict
      contains:
        id:
          description: "The agent token ID."
          type: str
        attributes:
          description: "Agent token attributes."
          type: dict
        relationships:
          description: "Associated resources."
          type: dict
"""

from ansible_collections.benemon.hcp_community_collection.plugins.module_utils.hcp_terraform_module import HCPTerraformModule

class TerraformAgentTokenModule(HCPTerraformModule):
    def __init__(self):
        # Define the argument specification for this module.
        argument_spec = dict(
            token=dict(type='str', required=True, no_log=True),
            hostname=dict(type='str', required=False, default="https://app.terraform.io"),
            agent_pool_id=dict(type='str', required=True),
            description=dict(type='str', required=False, default="Created by Ansible"),
            token_id=dict(type='str', required=False),
            state=dict(type='str', required=False, choices=['present', 'absent'], default='present')
        )
        
        # Initialize the base class (which is also an AnsibleModule)
        super().__init__(
            argument_spec=argument_spec,
            supports_check_mode=True,
            required_if=[
                ['state', 'absent', ['token_id']],
            ]
        )
        
        # Only extract params if we're not in a test environment
        if hasattr(self, 'params'):
            # Extract the parameters
            self.agent_pool_id = self.params.get('agent_pool_id')
            self.description = self.params.get('description')
            self.token_id = self.params.get('token_id')
            self.state = self.params.get('state')

    def _get_agent_token(self, token_id):
        """Retrieve the agent token from HCP Terraform if it exists."""
        try:
            endpoint = f"/authentication-tokens/{token_id}"
            response = self._request("GET", endpoint)
            return response
        except Exception as e:
            # If the token doesn't exist, return None
            if "404" in str(e) or "not found" in str(e).lower():
                return None
            # Re-raise other exceptions
            raise

    def _list_agent_tokens(self):
        """List all agent tokens for the agent pool."""
        try:
            endpoint = f"/agent-pools/{self.agent_pool_id}/authentication-tokens"
            response = self._request("GET", endpoint)
            return response
        except Exception as e:
            # If the agent pool doesn't exist, re-raise the exception
            raise

    def _create_agent_token(self):
        """Create a new agent token for the agent pool."""
        endpoint = f"/agent-pools/{self.agent_pool_id}/authentication-tokens"
        
        # Build the payload
        payload = {
            "data": {
                "type": "authentication-tokens",
                "attributes": {
                    "description": self.description
                }
            }
        }
        
        # Make the API request
        response = self._request("POST", endpoint, data=payload)
        return response

    def _delete_agent_token(self, token_id):
        """Delete an agent token."""
        endpoint = f"/authentication-tokens/{token_id}"
        
        # Make the API request
        self._request("DELETE", endpoint)
        return {"changed": True, "msg": f"Agent token '{token_id}' deleted successfully"}

    def _format_agent_token_output(self, response):
        """Format the agent token output for better readability."""
        data = response.get("data", {})
        attributes = data.get("attributes", {})
        
        formatted = {
            "id": data.get("id"),
            "description": attributes.get("description"),
            "created_at": attributes.get("created-at"),
        }
        
        # Add token value if available (only on creation)
        if attributes.get("token"):
            formatted["token"] = attributes.get("token")
            
        return formatted

    def run(self):
        """Main module execution logic."""
        try:
            # Return early if check mode
            if self.check_mode:
                if self.state == 'present':
                    self.exit_json(changed=True, msg=f"Would create agent token for agent pool '{self.agent_pool_id}'")
                elif self.state == 'absent' and self.token_id:
                    # Check if the token exists
                    token = self._get_agent_token(self.token_id)
                    if token:
                        self.exit_json(changed=True, msg=f"Would delete agent token '{self.token_id}'")
                    else:
                        self.exit_json(changed=False, msg=f"Agent token '{self.token_id}' already does not exist")
                else:
                    self.exit_json(changed=False, msg="No changes needed for agent tokens")
            
            # Apply the requested state
            if self.state == 'present':
                # Create a new agent token
                response = self._create_agent_token()
                self.exit_json(
                    changed=True,
                    msg=f"Agent token created successfully for agent pool '{self.agent_pool_id}'",
                    agent_token=self._format_agent_token_output(response),
                    result=response
                )
            else:  # state == 'absent'
                # Check if the token exists
                token = self._get_agent_token(self.token_id)
                if token:
                    # Delete the token
                    result = self._delete_agent_token(self.token_id)
                    self.exit_json(**result, result={"deleted": True})
                else:
                    # Token already doesn't exist
                    self.exit_json(
                        changed=False,
                        msg=f"Agent token '{self.token_id}' already does not exist",
                        result={"deleted": False}
                    )
                    
        except Exception as e:
            self.fail_json(msg=f"Error managing agent token: {str(e)}")

def main():
    module = TerraformAgentTokenModule()
    module.run()

if __name__ == "__main__":
    main()