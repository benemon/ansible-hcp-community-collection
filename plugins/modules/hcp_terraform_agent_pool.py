#!/usr/bin/python
DOCUMENTATION = """
---
module: hcp_terraform_agent_pool
short_description: Manages HCP Terraform agent pools
description:
  - Creates, updates, and deletes agent pools in HCP Terraform.
  - Configures agent pool settings like name and scope.
  - Manages which workspaces are allowed to use the agent pool.
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
  organization:
    description: "Name of the organization in which the agent pool will be managed."
    required: true
    type: str
  name:
    description: "Name of the agent pool."
    required: true
    type: str
  organization_scoped:
    description: "Whether the agent pool is available to all workspaces in the organization."
    required: false
    type: bool
    default: true
  allowed_workspaces:
    description: "List of workspace IDs that are allowed to use this agent pool. Only used when organization_scoped is false."
    required: false
    type: list
    elements: str
  id:
    description: "ID of the agent pool to update or delete. Required when state=absent."
    required: false
    type: str  
  state:
    description: "Whether the agent pool should exist or not."
    required: false
    choices: ["present", "absent"]
    default: "present"
    type: str
notes:
  - "HCP Terraform Free Edition includes one self-hosted agent."
  - "When organization_scoped is false, at least one workspace must be specified in allowed_workspaces."
"""

EXAMPLES = """
- name: Create an organization-scoped agent pool
  benemon.hcp_community_collection.hcp_terraform_agent_pool:
    token: "{{ lookup('env', 'TFE_TOKEN') }}"
    organization: "my-organization"
    name: "my-agent-pool"
    organization_scoped: true
    
- name: Create a workspace-scoped agent pool
  benemon.hcp_community_collection.hcp_terraform_agent_pool:
    token: "{{ lookup('env', 'TFE_TOKEN') }}"
    organization: "my-organization"
    name: "workspace-specific-pool"
    organization_scoped: false
    allowed_workspaces:
      - "ws-abc123"
      - "ws-def456"
      
- name: Update an agent pool name and scope
  benemon.hcp_community_collection.hcp_terraform_agent_pool:
    token: "{{ lookup('env', 'TFE_TOKEN') }}"
    organization: "my-organization"
    name: "renamed-pool"
    id: "apool-yoGUFz5zcRMMz53i"
    organization_scoped: false
    allowed_workspaces:
      - "ws-abc123"
    
- name: Remove an agent pool
  benemon.hcp_community_collection.hcp_terraform_agent_pool:
    token: "{{ lookup('env', 'TFE_TOKEN') }}"
    organization: "my-organization"
    name: "pool-to-remove"
    id: "apool-yoGUFz5zcRMMz53i"
    state: "absent"
"""

RETURN = """
agent_pool:
  description: "Details of the agent pool."
  returned: when state=present
  type: dict
  contains:
    id:
      description: "The ID of the agent pool."
      type: str
      sample: "apool-yoGUFz5zcRMMz53i"
    name:
      description: "The name of the agent pool."
      type: str
      sample: "my-agent-pool"
    organization_scoped:
      description: "Whether the agent pool is available to all workspaces in the organization."
      type: bool
      sample: true
    created_at:
      description: "When the agent pool was created."
      type: str
      sample: "2021-05-15T18:24:16.591Z"
    organization:
      description: "The name of the organization."
      type: str
      sample: "my-organization"
    allowed_workspaces:
      description: "List of workspace IDs that are allowed to use this agent pool."
      type: list
      elements: str
      sample: ["ws-abc123", "ws-def456"]
result:
  description: "Raw API response from HCP Terraform."
  returned: always
  type: dict
  contains:
    data:
      description: "Information about the agent pool."
      type: dict
      contains:
        id:
          description: "The agent pool ID."
          type: str
        attributes:
          description: "Agent pool attributes."
          type: dict
        relationships:
          description: "Associated resources."
          type: dict
"""

from ansible_collections.benemon.hcp_community_collection.plugins.module_utils.hcp_terraform_module import HCPTerraformModule

class TerraformAgentPoolModule(HCPTerraformModule):
    def __init__(self):
        # Define the argument specification for this module.
        argument_spec = dict(
            token=dict(type='str', required=True, no_log=True),
            hostname=dict(type='str', required=False, default="https://app.terraform.io"),
            organization=dict(type='str', required=True),
            name=dict(type='str', required=True),
            organization_scoped=dict(type='bool', required=False, default=True),
            allowed_workspaces=dict(type='list', elements='str', required=False),
            id=dict(type='str', required=False),
            state=dict(type='str', required=False, choices=['present', 'absent'], default='present')
        )
        
        # Initialize the base class (which is also an AnsibleModule)
        super().__init__(
            argument_spec=argument_spec,
            supports_check_mode=True,
            required_if=[
                ['organization_scoped', False, ['allowed_workspaces']],
                ['state', 'absent', ['id']]
            ]
        )
        
        # Only extract params if we're not in a test environment
        if hasattr(self, 'params'):
            # Extract the parameters
            self.organization = self.params.get('organization')
            self.name = self.params.get('name')
            self.id = self.params.get('id')
            self.state = self.params.get('state')
            self.organization_scoped = self.params.get('organization_scoped')
            self.allowed_workspaces = self.params.get('allowed_workspaces')

    def _get_agent_pool_by_id(self):
        """Retrieve the agent pool from HCP Terraform using ID."""
        try:
            endpoint = f"/agent-pools/{self.id}"
            response = self._request("GET", endpoint)
            return response
        except Exception as e:
            # If the agent pool doesn't exist, return None
            if "404" in str(e) or "not found" in str(e).lower():
                return None
            # Re-raise other exceptions
            raise

    def _get_agent_pool_by_name(self):
        """Retrieve the agent pool from HCP Terraform by name if it exists."""
        try:
            endpoint = f"/organizations/{self.organization}/agent-pools"
            response = self._request("GET", endpoint)
            
            if 'data' in response:
                # Find the agent pool by name
                for pool in response['data']:
                    if pool.get('attributes', {}).get('name') == self.name:
                        return {'data': pool}
            # If no matching agent pool found
            return None
        except Exception as e:
            # If the organization doesn't exist, return None
            if "404" in str(e) or "not found" in str(e).lower():
                return None
            # Re-raise other exceptions
            raise

    def _get_agent_pool(self):
        """Get the agent pool by ID if provided, otherwise by name."""
        if self.id:
            return self._get_agent_pool_by_id()
        else:
            return self._get_agent_pool_by_name()

    def _create_agent_pool(self):
        """Create a new agent pool in HCP Terraform."""
        endpoint = f"/organizations/{self.organization}/agent-pools"
        
        # Prepare the attributes
        attributes = {
            "name": self.name,
            "organization-scoped": self.organization_scoped
        }
        
        # Build the payload
        payload = {
            "data": {
                "type": "agent-pools",
                "attributes": attributes
            }
        }
        
        # Add allowed workspaces if organization scoped is False
        if not self.organization_scoped and self.allowed_workspaces:
            allowed_workspaces_data = []
            for workspace_id in self.allowed_workspaces:
                allowed_workspaces_data.append({
                    "id": workspace_id,
                    "type": "workspaces"
                })
            
            payload["data"]["relationships"] = {
                "allowed-workspaces": {
                    "data": allowed_workspaces_data
                }
            }
            
        # Make the API request
        response = self._request("POST", endpoint, data=payload)
        return response

    def _update_agent_pool(self, agent_pool):
        """Update an existing agent pool in HCP Terraform."""
        agent_pool_id = agent_pool.get("data", {}).get("id")
        if not agent_pool_id:
            self.fail_json(msg="Failed to get agent pool ID from existing agent pool")
            
        endpoint = f"/agent-pools/{agent_pool_id}"
        
        # Prepare the attributes
        attributes = {
            "name": self.name,
            "organization-scoped": self.organization_scoped
        }
        
        # Build the payload
        payload = {
            "data": {
                "type": "agent-pools",
                "id": agent_pool_id,
                "attributes": attributes
            }
        }
        
        # Add allowed workspaces if organization scoped is False
        if not self.organization_scoped and self.allowed_workspaces:
            allowed_workspaces_data = []
            for workspace_id in self.allowed_workspaces:
                allowed_workspaces_data.append({
                    "id": workspace_id,
                    "type": "workspaces"
                })
            
            payload["data"]["relationships"] = {
                "allowed-workspaces": {
                    "data": allowed_workspaces_data
                }
            }
        
        # Make the API request
        response = self._request("PATCH", endpoint, data=payload)
        return response

    def _delete_agent_pool(self, agent_pool):
        """Delete an agent pool from HCP Terraform."""
        agent_pool_id = agent_pool.get("data", {}).get("id")
        if not agent_pool_id:
            self.fail_json(msg="Failed to get agent pool ID from existing agent pool")
            
        endpoint = f"/agent-pools/{agent_pool_id}"
        
        # Make the API request
        self._request("DELETE", endpoint)
        return {"changed": True, "msg": f"Agent pool '{self.name}' deleted successfully"}

    def _format_agent_pool_output(self, agent_pool):
        """Format the agent pool output for better readability."""
        data = agent_pool.get("data", {})
        attributes = data.get("attributes", {})
        
        formatted = {
            "id": data.get("id"),
            "name": attributes.get("name"),
            "organization_scoped": attributes.get("organization-scoped"),
            "created_at": attributes.get("created-at"),
            "organization": self.organization
        }
        
        # Add allowed workspaces if present
        if data.get("relationships", {}).get("allowed-workspaces", {}).get("data"):
            formatted["allowed_workspaces"] = [
                workspace.get("id")
                for workspace in data["relationships"]["allowed-workspaces"]["data"]
            ]
            
        return formatted

    def run(self):
        """Main module execution logic."""
        try:
            # Get the current agent pool state
            agent_pool = self._get_agent_pool()
            
            # Return early if check mode
            if self.check_mode:
                if self.state == 'present' and not agent_pool:
                    self.exit_json(changed=True, msg=f"Would create agent pool '{self.name}'")
                elif self.state == 'present' and agent_pool:
                    self.exit_json(changed=True, msg=f"Would update agent pool '{self.name}'")
                elif self.state == 'absent' and agent_pool:
                    self.exit_json(changed=True, msg=f"Would delete agent pool '{self.name}'")
                else:
                    self.exit_json(changed=False, msg=f"No changes needed for agent pool '{self.name}'")
            
            # Apply the requested state
            if self.state == 'present':
                if not agent_pool:
                    # Create a new agent pool
                    response = self._create_agent_pool()
                    self.exit_json(
                        changed=True,
                        msg=f"Agent pool '{self.name}' created successfully",
                        agent_pool=self._format_agent_pool_output(response),
                        result=response
                    )
                else:
                    # Update an existing agent pool
                    response = self._update_agent_pool(agent_pool)
                    self.exit_json(
                        changed=True,
                        msg=f"Agent pool '{self.name}' updated successfully",
                        agent_pool=self._format_agent_pool_output(response),
                        result=response
                    )
            else:  # state == 'absent'
                if agent_pool:
                    # Delete the agent pool
                    result = self._delete_agent_pool(agent_pool)
                    self.exit_json(**result, result={"deleted": True})
                else:
                    # Agent pool already doesn't exist
                    self.exit_json(
                        changed=False,
                        msg=f"Agent pool '{self.name}' already does not exist",
                        result={"deleted": False}
                    )
                    
        except Exception as e:
            self.fail_json(msg=f"Error managing agent pool: {str(e)}")

def main():
    module = TerraformAgentPoolModule()
    module.run()

if __name__ == "__main__":
    main()