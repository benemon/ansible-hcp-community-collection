#!/usr/bin/python
DOCUMENTATION = r'''
---
module: hcp_terraform_variable_set
short_description: Manage Variable Sets in HCP Terraform
description:
    - Create, update, and manage variable sets in Terraform Cloud/Enterprise
    - Supports global, project-specific, and workspace-specific variable sets
    - Allows adding, updating, and removing variables within a set
author: 
    - Benjamin Holmes (@benemon)
options:
    token:
        description: HCP Terraform API token
        required: true
        type: str
        no_log: true
    organization:
        description: Name of the organization managing the variable set
        required: true
        type: str
    name:
        description: Name of the variable set
        required: true
        type: str
    description:
        description: Description of the variable set
        required: false
        type: str
    state:
        description: Whether the variable set should exist
        required: false
        type: str
        choices: ['present', 'absent']
        default: 'present'
    global:
        description: Apply the variable set to all workspaces in the organization
        required: false
        type: bool
        default: false
    priority:
        description: Variable set overrides other variable values
        required: false
        type: bool
        default: false
    project_ids:
        description: Projects to which the variable set should be assigned
        required: false
        type: list
        elements: str
        default: []
    workspace_ids:
        description: Workspaces to which the variable set should be assigned
        required: false
        type: list
        elements: str
        default: []
    variables:
        description: Variables to include in the variable set
        required: false
        type: list
        elements: dict
        suboptions:
            key:
                description: Name of the variable
                required: true
                type: str
            value:
                description: Value of the variable
                required: true
                type: str
            description:
                description: Description of the variable
                required: false
                type: str
            category:
                description: Category of the variable
                required: false
                type: str
                choices: ['terraform', 'env']
                default: 'terraform'
            hcl:
                description: Whether the variable is HCL-formatted
                required: false
                type: bool
                default: false
            sensitive:
                description: Mark the variable as sensitive
                required: false
                type: bool
                default: false
'''

EXAMPLES = r'''
- name: Create a global variable set
  benemon.hcp_community_collection.hcp_terraform_variable_set:
    token: "{{ lookup('env', 'TFE_TOKEN') }}"
    organization: my-org
    name: global-configs
    global: true
    variables:
      - key: default_region
        value: us-east-1

- name: Create a project-specific variable set
  benemon.hcp_community_collection.hcp_terraform_variable_set:
    token: "{{ lookup('env', 'TFE_TOKEN') }}"
    organization: my-org
    name: project-secrets
    project_ids: 
      - prj-abc123
    variables:
      - key: db_password
        value: "{{ vault_db_password }}"
        sensitive: true

- name: Remove a variable set
  benemon.hcp_community_collection.hcp_terraform_variable_set:
    token: "{{ lookup('env', 'TFE_TOKEN') }}"
    organization: my-org
    name: deprecated-vars
    state: absent
'''

RETURN = r'''
variable_set:
    description: Details of the variable set
    returned: always
    type: dict
    contains:
        id:
            description: Unique identifier of the variable set
            type: str
        name:
            description: Name of the variable set
            type: str
        description:
            description: Description of the variable set
            type: str
        global:
            description: Whether the set applies to all workspaces
            type: bool
        priority:
            description: Whether the set takes precedence
            type: bool
        variables:
            description: List of variables in the set
            type: list
        project_ids:
            description: Projects to which the set is assigned
            type: list
        workspace_ids:
            description: Workspaces to which the set is assigned
            type: list
result:
    description: Raw API response
    returned: always
    type: dict
'''

from ansible_collections.benemon.hcp_community_collection.plugins.module_utils.hcp_terraform_module import HCPTerraformModule

class TerraformVariableSetModule(HCPTerraformModule):
    def __init__(self):
        # Define argument specification
        argument_spec = dict(
            token=dict(type='str', required=True, no_log=True),
            organization=dict(type='str', required=True),
            name=dict(type='str', required=True),
            description=dict(type='str', required=False),
            state=dict(type='str', choices=['present', 'absent'], default='present'),
            global_set=dict(type='bool', default=False, aliases=['global']),
            priority=dict(type='bool', default=False),
            project_ids=dict(type='list', elements='str', default=[]),
            workspace_ids=dict(type='list', elements='str', default=[]),
            variables=dict(
                type='list', 
                elements='dict', 
                default=[],
                options=dict(
                    key=dict(type='str', required=True),
                    value=dict(type='str', required=True, no_log=False),
                    description=dict(type='str', required=False),
                    category=dict(type='str', choices=['terraform', 'env'], default='terraform'),
                    hcl=dict(type='bool', default=False),
                    sensitive=dict(type='bool', default=False)
                )
            )
        )
        
        # Initialize base class
        super().__init__(
            argument_spec=argument_spec,
            supports_check_mode=True
        )
        
        # Extract key parameters
        self.organization = self.params.get('organization')
        self.name = self.params.get('name')
        self.state = self.params.get('state')

    def _get_variable_set(self):
        """Find a variable set by name in the organization."""
        try:
            # List variable sets to find matching name
            endpoint = f"/organizations/{self.organization}/varsets"
            response = self._request("GET", endpoint)
            
            # Find the variable set with the matching name
            for varset in response.get("data", []):
                if varset.get("attributes", {}).get("name") == self.name:
                    # Fetch full details of the specific variable set
                    varset_id = varset.get("id")
                    return self._request("GET", f"/varsets/{varset_id}")
            
            return None
        except Exception as e:
            # If the variable set doesn't exist or there's an error, return None
            if "404" in str(e) or "not found" in str(e).lower():
                return None
            raise

    def _prepare_payload(self):
        """Prepare the payload for creating or updating a variable set."""
        payload = {
            "data": {
                "type": "varsets",
                "attributes": {
                    "name": self.name,
                    "global": self.params.get('global_set', False),
                    "priority": self.params.get('priority', False)
                }
            }
        }
        
        # Add optional description
        if self.params.get('description'):
            payload["data"]["attributes"]["description"] = self.params.get('description')
        
        # Add relationships
        relationships = {}
        
        # Add variables
        if self.params.get('variables'):
            relationships["vars"] = {
                "data": [
                    {
                        "type": "vars",
                        "attributes": {
                            "key": var['key'],
                            "value": var['value'],
                            "category": var.get('category', 'terraform'),
                            "description": var.get('description', ''),
                            "hcl": var.get('hcl', False),
                            "sensitive": var.get('sensitive', False)
                        }
                    }
                    for var in self.params.get('variables', [])
                ]
            }
        
        # Add project assignments
        project_ids = self.params.get('project_ids', [])
        if project_ids:
            relationships["projects"] = {
                "data": [{"id": pid, "type": "projects"} for pid in project_ids]
            }
        
        # Add workspace assignments
        workspace_ids = self.params.get('workspace_ids', [])
        if workspace_ids:
            relationships["workspaces"] = {
                "data": [{"id": wid, "type": "workspaces"} for wid in workspace_ids]
            }
        
        # Add relationships to payload if any exist
        if relationships:
            payload["data"]["relationships"] = relationships
        
        return payload

    def _create_variable_set(self):
        """Create a new variable set in HCP Terraform."""
        endpoint = f"/organizations/{self.organization}/varsets"
        payload = self._prepare_payload()
        return self._request("POST", endpoint, data=payload)

    def _update_variable_set(self, existing_varset):
        """Update an existing variable set in HCP Terraform."""
        varset_id = existing_varset.get("data", {}).get("id")
        if not varset_id:
            self.fail_json(msg="Failed to get variable set ID")
        
        endpoint = f"/varsets/{varset_id}"
        payload = self._prepare_payload()
        payload['data']['id'] = varset_id
        
        return self._request("PATCH", endpoint, data=payload)

    def _delete_variable_set(self, varset):
        """Delete a variable set from HCP Terraform."""
        varset_id = varset.get("data", {}).get("id")
        if not varset_id:
            self.fail_json(msg="Failed to get variable set ID")
        
        endpoint = f"/varsets/{varset_id}"
        self._request("DELETE", endpoint)
        return {"changed": True, "msg": f"Variable set '{self.name}' deleted successfully"}

    def _format_variable_set_output(self, varset):
        """Format the variable set output for better readability."""
        data = varset.get("data", {})
        attributes = data.get("attributes", {})
        
        output = {
            "id": data.get("id"),
            "name": attributes.get("name"),
            "description": attributes.get("description"),
            "global": attributes.get("global", False),
            "priority": attributes.get("priority", False),
            "variables": [],
            "project_ids": [],
            "workspace_ids": []
        }
        
        # Add variables from included resources
        for included in varset.get("included", []):
            if included.get("type") == "vars":
                output["variables"].append({
                    "key": included.get("attributes", {}).get("key"),
                    "category": included.get("attributes", {}).get("category"),
                    "sensitive": included.get("attributes", {}).get("sensitive", False)
                })
        
        # Add project ids
        if data.get("relationships", {}).get("projects", {}).get("data"):
            output["project_ids"] = [
                proj.get("id") for proj in data["relationships"]["projects"]["data"]
            ]
        
        # Add workspace ids
        if data.get("relationships", {}).get("workspaces", {}).get("data"):
            output["workspace_ids"] = [
                ws.get("id") for ws in data["relationships"]["workspaces"]["data"]
            ]
        
        return output

    def run(self):
        """Main module execution logic."""
        try:
            # Get the current variable set state
            existing_varset = self._get_variable_set()
            
            # Handle check mode
            if self.check_mode:
                if self.state == 'present' and not existing_varset:
                    self.exit_json(changed=True, msg=f"Would create variable set '{self.name}'")
                elif self.state == 'present' and existing_varset:
                    self.exit_json(changed=True, msg=f"Would update variable set '{self.name}'")
                elif self.state == 'absent' and existing_varset:
                    self.exit_json(changed=True, msg=f"Would delete variable set '{self.name}'")
                else:
                    self.exit_json(changed=False, msg=f"No changes needed for variable set '{self.name}'")
            
            # Apply the requested state
            if self.state == 'present':
                if not existing_varset:
                    # Create a new variable set
                    response = self._create_variable_set()
                    self.exit_json(
                        changed=True,
                        msg=f"Variable set '{self.name}' created successfully",
                        variable_set=self._format_variable_set_output(response),
                        result=response
                    )
                else:
                    # Check if an update is needed
                    data = existing_varset.get("data", {})
                    attributes = data.get("attributes", {})
                    relationships = data.get("relationships", {})

                    update_needed = (
                        attributes.get("name") != self.name or
                        attributes.get("description") != self.params.get('description') or
                        attributes.get("global") != self.params.get('global_set') or
                        attributes.get("priority") != self.params.get('priority')
                    )

                    # Check if project assignments need updating
                    if not update_needed and self.params.get('project_ids'):
                        current_project_ids = []
                        if relationships.get("projects", {}).get("data"):
                            current_project_ids = [
                                proj.get("id") for proj in relationships["projects"]["data"]
                            ]
                        update_needed = set(current_project_ids) != set(self.params.get('project_ids'))

                    # Check if workspace assignments need updating
                    if not update_needed and self.params.get('workspace_ids'):
                        current_workspace_ids = []
                        if relationships.get("workspaces", {}).get("data"):
                            current_workspace_ids = [
                                ws.get("id") for ws in relationships["workspaces"]["data"]
                            ]
                        update_needed = set(current_workspace_ids) != set(self.params.get('workspace_ids'))

                    # Check if variables need updating
                    # This is a simplified check - a more thorough implementation would compare each variable
                    if not update_needed and self.params.get('variables'):
                        current_var_count = len(relationships.get("vars", {}).get("data", []))
                        update_needed = current_var_count != len(self.params.get('variables'))

                    if update_needed:
                        # Update the existing variable set
                        response = self._update_variable_set(existing_varset)
                        self.exit_json(
                            changed=True,
                            msg=f"Variable set '{self.name}' updated successfully",
                            variable_set=self._format_variable_set_output(response),
                            result=response
                        )
                    else:
                        # No update needed
                        self.exit_json(
                            changed=False,
                            msg=f"Variable set '{self.name}' already up-to-date",
                            variable_set=self._format_variable_set_output(existing_varset),
                            result=existing_varset
                        )
            else:  # state == 'absent'
                if existing_varset:
                    # Delete the variable set
                    result = self._delete_variable_set(existing_varset)
                    self.exit_json(**result, result={"deleted": True})
                else:
                    # Variable set already doesn't exist
                    self.exit_json(
                        changed=False,
                        msg=f"Variable set '{self.name}' already does not exist",
                        result={"deleted": False}
                    )
                    
        except Exception as e:
            error_msg = f"Error managing variable set: {str(e)}"
            self.fail_json(msg=error_msg)
def main():
    module = TerraformVariableSetModule()
    module.run()

if __name__ == "__main__":
    main()