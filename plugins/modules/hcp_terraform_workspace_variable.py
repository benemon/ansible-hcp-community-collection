#!/usr/bin/python
DOCUMENTATION = """
---
module: hcp_terraform_workspace_variable
short_description: Manages Terraform variables in HCP Terraform or Terraform Enterprise
description:
  - Creates, updates, and manages Terraform variables.
  - Supports both Terraform variables and environment variables.
  - Can manage sensitive (secret) variables.
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
  workspace_id:
    description: "ID of the workspace where the variable will be managed."
    required: true
    type: str
  key:
    description: "Name of the variable."
    required: true
    type: str
  value:
    description: "Value of the variable. Required when state is present."
    required: false
    type: str
  description:
    description: "Description of the variable."
    required: false
    type: str
  category:
    description: "Whether this is a Terraform variable or environment variable."
    required: false
    choices: ["terraform", "env"]
    type: str
    default: "terraform"
  hcl:
    description: "Whether to evaluate the value of the variable as HCL."
    required: false
    type: bool
    default: false
  sensitive:
    description: "Whether the value of the variable is sensitive."
    required: false
    type: bool
    default: false
  state:
    description: "Whether the variable should exist or not."
    required: false
    choices: ["present", "absent"]
    default: "present"
    type: str
"""

EXAMPLES = """
- name: Create a Terraform variable
  benemon.hcp_community_collection.hcp_terraform_workspace_variable:
    token: "{{ lookup('env', 'TFE_TOKEN') }}"
    workspace_id: "ws-abcdefg123456"
    key: "instance_type"
    value: "t3.micro"
    description: "EC2 instance type"
    
- name: Create a sensitive environment variable
  benemon.hcp_community_collection.hcp_terraform_workspace_variable:
    token: "{{ lookup('env', 'TFE_TOKEN') }}"
    workspace_id: "ws-abcdefg123456"
    key: "AWS_SECRET_ACCESS_KEY"
    value: "{{ aws_secret_key }}"
    category: "env"
    sensitive: true
    
- name: Create a variable with HCL value
  benemon.hcp_community_collection.hcp_terraform_workspace_variable:
    token: "{{ lookup('env', 'TFE_TOKEN') }}"
    workspace_id: "ws-abcdefg123456"
    key: "allowed_cidrs"
    value: '["10.0.0.0/16", "192.168.1.0/24"]'
    hcl: true
    
- name: Update an existing variable
  benemon.hcp_community_collection.hcp_terraform_workspace_variable:
    token: "{{ lookup('env', 'TFE_TOKEN') }}"
    workspace_id: "ws-abcdefg123456"
    key: "instance_type"
    value: "t3.large"
    
- name: Delete a variable
  benemon.hcp_community_collection.hcp_terraform_workspace_variable:
    token: "{{ lookup('env', 'TFE_TOKEN') }}"
    workspace_id: "ws-abcdefg123456"
    key: "region"
    state: "absent"

- name: Create multiple variables in the same workspace
  benemon.hcp_community_collection.hcp_terraform_workspace_variable:
    token: "{{ lookup('env', 'TFE_TOKEN') }}"
    workspace_id: "ws-abcdefg123456"
    key: "{{ item.key }}"
    value: "{{ item.value }}"
    category: "{{ item.category | default('terraform') }}"
    description: "{{ item.description | default(omit) }}"
    sensitive: "{{ item.sensitive | default(false) }}"
  loop:
    - key: region
      value: us-east-1
      description: AWS region
    - key: AWS_ACCESS_KEY_ID
      value: "{{ aws_access_key }}"
      category: env
      sensitive: true
    - key: AWS_SECRET_ACCESS_KEY
      value: "{{ aws_secret_key }}"
      category: env
      sensitive: true
"""

RETURN = """
variable:
  description: "Details of the variable."
  returned: when state=present
  type: dict
  contains:
    id:
      description: "The ID of the variable."
      type: str
      sample: "var-EavQ1LztoRTQHSNT"
    key:
      description: "The name of the variable."
      type: str
      sample: "instance_type"
    value:
      description: "The value of the variable (omitted for sensitive variables)."
      type: str
      sample: "t3.micro"
    description:
      description: "The description of the variable."
      type: str
      sample: "EC2 instance type"
    category:
      description: "The category of the variable (terraform or env)."
      type: str
      sample: "terraform"
    hcl:
      description: "Whether the variable is evaluated as HCL."
      type: bool
      sample: false
    sensitive:
      description: "Whether the variable is sensitive."
      type: bool
      sample: false
    workspace_id:
      description: "The ID of the workspace."
      type: str
      sample: "ws-4j8p6jX1w33MiDC7"
result:
  description: "Raw API response from HCP Terraform."
  returned: always
  type: dict
  contains:
    data:
      description: "Information about the variable."
      type: dict
      contains:
        id:
          description: "The variable ID."
          type: str
          sample: "var-EavQ1LztoRTQHSNT"
        attributes:
          description: "Variable attributes."
          type: dict
          contains:
            key:
              description: "Variable name."
              type: str
              sample: "instance_type"
            value:
              description: "Variable value (omitted for sensitive variables)."
              type: str
              sample: "t3.micro"
            sensitive:
              description: "Whether the variable is sensitive."
              type: bool
              sample: false
            category:
              description: "Variable category (terraform or env)."
              type: str
              sample: "terraform"
            hcl:
              description: "Whether the variable is HCL formatted."
              type: bool
              sample: false
"""

from ansible_collections.benemon.hcp_community_collection.plugins.module_utils.hcp_terraform_module import HCPTerraformModule

class TerraformWorkspaceVariableModule(HCPTerraformModule):
    def __init__(self):
        # Define the argument specification for this module.
        argument_spec = dict(
            token=dict(type='str', required=True, no_log=True),
            hostname=dict(type='str', required=False, default="https://app.terraform.io"),
            workspace_id=dict(type='str', required=True),
            key=dict(type='str', required=True),
            value=dict(type='str', required=False, no_log=False),
            description=dict(type='str', required=False),
            category=dict(type='str', required=False, choices=['terraform', 'env'], default='terraform'),
            hcl=dict(type='bool', required=False, default=False),
            sensitive=dict(type='bool', required=False, default=False),
            state=dict(type='str', required=False, choices=['present', 'absent'], default='present')
        )
        
        # Add no_log=True for value when sensitive=True
        # Note: We can't conditionally set no_log, so we handle this in run() method
        
        # Initialize the base class (which is also an AnsibleModule)
        super().__init__(
            argument_spec=argument_spec,
            supports_check_mode=True,
            required_if=[
                ['state', 'present', ['value']]
            ]
        )
        
        # Only extract params if we're not in a test environment
        if hasattr(self, 'params'):
            # Extract the parameters
            self.workspace_id = self.params.get('workspace_id')
            self.key = self.params.get('key')
            self.value = self.params.get('value')
            self.state = self.params.get('state')
            self.sensitive = self.params.get('sensitive')
            
            # If sensitive is true, remove the value from logs
            if self.sensitive and hasattr(self, 'no_log_values') and self.value:
                self.no_log_values.add(self.value)

    def _get_variable(self):
        """Find a variable by key in a workspace."""
        endpoint = f"/workspaces/{self.workspace_id}/vars"
        
        try:
            # Get all variables for the workspace
            response = self._request("GET", endpoint)
            
            # Find the variable with the matching key and category
            for var in response.get("data", []):
                if (var.get("attributes", {}).get("key") == self.key and 
                    var.get("attributes", {}).get("category") == self.params.get('category')):
                    return var
            
            # Variable not found
            return None
        except Exception as e:
            # If no variables exist, return None
            if "404" in str(e) or "not found" in str(e).lower():
                return None
            # Re-raise other exceptions
            raise

    def _create_variable(self):
        """Create a new variable in HCP Terraform."""
        endpoint = f"/workspaces/{self.workspace_id}/vars"
        
        # Prepare the attributes
        attributes = {
            "key": self.key,
            "value": self.value,
            "category": self.params.get('category'),
            "hcl": self.params.get('hcl'),
            "sensitive": self.sensitive
        }
        
        # Add description if provided
        if self.params.get('description'):
            attributes["description"] = self.params.get('description')
        
        # Build the payload
        payload = {
            "data": {
                "type": "vars",
                "attributes": attributes
            }
        }
        
        # Make the API request
        response = self._request("POST", endpoint, data=payload)
        return response

    def _update_variable(self, variable):
        """Update an existing variable in HCP Terraform."""
        variable_id = variable.get("id")
        if not variable_id:
            self.fail_json(msg="Failed to get variable ID from existing variable")
            
        endpoint = f"/workspaces/{self.workspace_id}/vars/{variable_id}"
        
        # Prepare the attributes
        attributes = {
            "key": self.key,
            "value": self.value,
            "category": self.params.get('category'),
            "hcl": self.params.get('hcl'),
            "sensitive": self.sensitive
        }
        
        # Add description if provided
        if self.params.get('description') is not None:
            attributes["description"] = self.params.get('description')
        
        # Build the payload
        payload = {
            "data": {
                "type": "vars",
                "id": variable_id,
                "attributes": attributes
            }
        }
        
        # Make the API request
        response = self._request("PATCH", endpoint, data=payload)
        return response

    def _delete_variable(self, variable):
        """Delete a variable from HCP Terraform."""
        variable_id = variable.get("id")
        if not variable_id:
            self.fail_json(msg="Failed to get variable ID from existing variable")
            
        endpoint = f"/workspaces/{self.workspace_id}/vars/{variable_id}"
        
        # Make the API request
        self._request("DELETE", endpoint)
        return {"changed": True, "msg": f"Variable '{self.key}' deleted successfully"}

    def _format_variable_output(self, variable):
        """Format the variable output for better readability."""
        attributes = variable.get("attributes", {})
        
        formatted = {
            "id": variable.get("id"),
            "key": attributes.get("key"),
            "category": attributes.get("category"),
            "hcl": attributes.get("hcl"),
            "sensitive": attributes.get("sensitive"),
            "description": attributes.get("description"),
            "workspace_id": self.workspace_id
        }
        
        # Only include the value if it's not sensitive
        if not attributes.get("sensitive") and "value" in attributes:
            formatted["value"] = attributes.get("value")
            
        return formatted

    def run(self):
        """Main module execution logic."""
        try:
            # Get the current variable state
            variable = self._get_variable()
            
            # Return early if check mode
            if self.check_mode:
                if self.state == 'present' and not variable:
                    self.exit_json(changed=True, msg=f"Would create variable '{self.key}'")
                elif self.state == 'present' and variable:
                    self.exit_json(changed=True, msg=f"Would update variable '{self.key}'")
                elif self.state == 'absent' and variable:
                    self.exit_json(changed=True, msg=f"Would delete variable '{self.key}'")
                else:
                    self.exit_json(changed=False, msg=f"No changes needed for variable '{self.key}'")
            
            # Apply the requested state
            if self.state == 'present':
                if not variable:
                    # Create a new variable
                    response = self._create_variable()
                    self.exit_json(
                        changed=True,
                        msg=f"Variable '{self.key}' created successfully",
                        variable=self._format_variable_output(response.get("data", {})),
                        result=response
                    )
                else:
                    # Check if update is needed
                    attributes = variable.get("attributes", {})
                    update_needed = (
                        attributes.get("value") != self.value or
                        attributes.get("description") != self.params.get('description') or
                        attributes.get("hcl") != self.params.get('hcl') or
                        attributes.get("sensitive") != self.sensitive
                    )
                    
                    if update_needed:
                        # Update the existing variable
                        response = self._update_variable(variable)
                        self.exit_json(
                            changed=True,
                            msg=f"Variable '{self.key}' updated successfully",
                            variable=self._format_variable_output(response.get("data", {})),
                            result=response
                        )
                    else:
                        # No update needed
                        self.exit_json(
                            changed=False,
                            msg=f"Variable '{self.key}' already up-to-date",
                            variable=self._format_variable_output(variable),
                            result={"data": variable}
                        )
            else:  # state == 'absent'
                if variable:
                    # Delete the variable
                    result = self._delete_variable(variable)
                    self.exit_json(**result, result={"deleted": True})
                else:
                    # Variable already doesn't exist
                    self.exit_json(
                        changed=False,
                        msg=f"Variable '{self.key}' already does not exist",
                        result={"deleted": False}
                    )
                    
        except Exception as e:
            error_msg = f"Error managing variable: {str(e)}"
            self.fail_json(msg=error_msg)

def main():
    module = TerraformWorkspaceVariableModule()
    module.run()

if __name__ == "__main__":
    main()