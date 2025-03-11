#!/usr/bin/python
DOCUMENTATION = """
---
module: hcp_terraform_organization
short_description: Manages Terraform organizations in HCP Terraform
description:
  - Creates, updates, and manages Terraform organizations.
  - Supports configuration of organization settings such as email, session timeout, and auth policy.
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
  name:
    description: "Name of the organization."
    required: true
    type: str
  email:
    description: "Admin email address for the organization."
    required: true
    type: str
  description:
    description: "Description of the organization."
    required: false
    type: str
  session_timeout:
    description: "Session timeout after inactivity (minutes)."
    required: false
    type: int
  session_remember:
    description: "Session expiration (minutes)."
    required: false
    type: int
  collaborator_auth_policy:
    description: "Authentication policy for the organization."
    required: false
    choices: ["password", "two_factor_mandatory"]
    type: str
    default: "password"
  cost_estimation_enabled:
    description: "Whether to enable cost estimation for all workspaces in the organization."
    required: false
    type: bool
    default: false
  assessments_enforced:
    description: "Whether to enforce health assessments for all eligible workspaces."
    required: false
    type: bool
    default: false
  default_execution_mode:
    description: "Default execution mode for new workspaces created in the organization."
    required: false
    choices: ["remote", "local", "agent"]
    type: str
    default: "remote"
  allow_force_delete_workspaces:
    description: "Whether workspace administrators can delete workspaces with resources under management."
    required: false
    type: bool
    default: false
  state:
    description: "Whether the organization should exist or not."
    required: false
    choices: ["present", "absent"]
    default: "present"
    type: str
"""

EXAMPLES = """
- name: Create a basic organization
  benemon.hcp_community_collection.hcp_terraform_organization:
    token: "{{ lookup('env', 'TFE_TOKEN') }}"
    name: "my-organization"
    email: "admin@example.com"
    
- name: Create an organization with enhanced security settings
  benemon.hcp_community_collection.hcp_terraform_organization:
    token: "{{ lookup('env', 'TFE_TOKEN') }}"
    name: "secure-org"
    email: "security@example.com"
    collaborator_auth_policy: "two_factor_mandatory"
    session_timeout: 60
    session_remember: 20160
    
- name: Update an organization to enable cost estimation
  benemon.hcp_community_collection.hcp_terraform_organization:
    token: "{{ lookup('env', 'TFE_TOKEN') }}"
    name: "existing-organization"
    email: "admin@example.com"
    cost_estimation_enabled: true
    
- name: Configure an organization with agent-based execution as default
  benemon.hcp_community_collection.hcp_terraform_organization:
    token: "{{ lookup('env', 'TFE_TOKEN') }}"
    name: "agent-based-org"
    email: "agent@example.com"
    default_execution_mode: "agent"
    
- name: Delete an organization
  benemon.hcp_community_collection.hcp_terraform_organization:
    token: "{{ lookup('env', 'TFE_TOKEN') }}"
    name: "organization-to-remove"
    email: "admin@example.com"
    state: "absent"
"""

RETURN = """
organization:
  description: "Details of the organization."
  returned: when state=present
  type: dict
  contains:
    id:
      description: "The ID of the organization."
      type: str
      sample: "my-organization"
    name:
      description: "The name of the organization."
      type: str
      sample: "my-organization"
    email:
      description: "The admin email address of the organization."
      type: str
      sample: "admin@example.com"
    collaborator_auth_policy:
      description: "The authentication policy of the organization."
      type: str
      sample: "password"
    created_at:
      description: "When the organization was created."
      type: str
      sample: "2023-05-15T18:24:16.591Z"
    default_execution_mode:
      description: "The default execution mode for new workspaces."
      type: str
      sample: "remote"
    cost_estimation_enabled:
      description: "Whether cost estimation is enabled."
      type: bool
      sample: false
    assessments_enforced:
      description: "Whether health assessments are enforced."
      type: bool
      sample: false
result:
  description: "Raw API response from HCP Terraform."
  returned: always
  type: dict
  contains:
    data:
      description: "Information about the organization."
      type: dict
      contains:
        id:
          description: "The organization ID."
          type: str
        attributes:
          description: "Organization attributes."
          type: dict
        relationships:
          description: "Associated resources."
          type: dict
"""

from ansible_collections.benemon.hcp_community_collection.plugins.module_utils.hcp_terraform_module import HCPTerraformModule

class TerraformOrganizationModule(HCPTerraformModule):
    def __init__(self):
        # Define the argument specification for this module.
        argument_spec = dict(
            token=dict(type='str', required=True, no_log=True),
            hostname=dict(type='str', required=False, default="https://app.terraform.io"),
            name=dict(type='str', required=True),
            email=dict(type='str', required=True),
            description=dict(type='str', required=False),
            session_timeout=dict(type='int', required=False),
            session_remember=dict(type='int', required=False),
            collaborator_auth_policy=dict(
                type='str', 
                required=False, 
                choices=['password', 'two_factor_mandatory'], 
                default='password'
            ),
            cost_estimation_enabled=dict(type='bool', required=False, default=False),
            assessments_enforced=dict(type='bool', required=False, default=False),
            default_execution_mode=dict(
                type='str', 
                required=False, 
                choices=['remote', 'local', 'agent'], 
                default='remote'
            ),
            allow_force_delete_workspaces=dict(type='bool', required=False, default=False),
            state=dict(type='str', required=False, choices=['present', 'absent'], default='present')
        )
        
        # Initialize the base class (which is also an AnsibleModule)
        super().__init__(
            argument_spec=argument_spec,
            supports_check_mode=True
        )
        
        # Extract the parameters
        self.name = self.params.get('name')
        self.email = self.params.get('email')
        self.state = self.params.get('state')

    def _get_organization(self):
        """Retrieve the organization from HCP Terraform if it exists."""
        try:
            endpoint = f"/organizations/{self.name}"
            response = self._request("GET", endpoint)
            return response
        except Exception as e:
            # If the organization doesn't exist, return None
            if "404" in str(e) or "not found" in str(e).lower():
                return None
            # Re-raise other exceptions
            raise

    def _create_organization(self):
        """Create a new organization in HCP Terraform."""
        endpoint = "/organizations"
        
        # Prepare the attributes
        attributes = {
            "name": self.name,
            "email": self.email,
            "collaborator-auth-policy": self.params.get('collaborator_auth_policy')
        }
        
        # Add optional attributes if they are set
        if self.params.get('description'):
            attributes["description"] = self.params.get('description')
            
        if self.params.get('session_timeout') is not None:
            attributes["session-timeout"] = self.params.get('session_timeout')
            
        if self.params.get('session_remember') is not None:
            attributes["session-remember"] = self.params.get('session_remember')
            
        if self.params.get('cost_estimation_enabled') is not None:
            attributes["cost-estimation-enabled"] = self.params.get('cost_estimation_enabled')
            
        if self.params.get('assessments_enforced') is not None:
            attributes["assessments-enforced"] = self.params.get('assessments_enforced')
            
        if self.params.get('default_execution_mode'):
            attributes["default-execution-mode"] = self.params.get('default_execution_mode')
            
        if self.params.get('allow_force_delete_workspaces') is not None:
            attributes["allow-force-delete-workspaces"] = self.params.get('allow_force_delete_workspaces')
        
        # Build the payload
        payload = {
            "data": {
                "type": "organizations",
                "attributes": attributes
            }
        }
        
        # Make the API request
        response = self._request("POST", endpoint, data=payload)
        return response

    def _update_organization(self):
        """Update an existing organization in HCP Terraform."""
        endpoint = f"/organizations/{self.name}"
        
        # Prepare the attributes
        attributes = {}
        
        # Add attributes that are being updated
        if self.params.get('email'):
            attributes["email"] = self.params.get('email')
            
        if self.params.get('description'):
            attributes["description"] = self.params.get('description')
            
        if self.params.get('session_timeout') is not None:
            attributes["session-timeout"] = self.params.get('session_timeout')
            
        if self.params.get('session_remember') is not None:
            attributes["session-remember"] = self.params.get('session_remember')
            
        if self.params.get('collaborator_auth_policy'):
            attributes["collaborator-auth-policy"] = self.params.get('collaborator_auth_policy')
            
        if self.params.get('cost_estimation_enabled') is not None:
            attributes["cost-estimation-enabled"] = self.params.get('cost_estimation_enabled')
            
        if self.params.get('assessments_enforced') is not None:
            attributes["assessments-enforced"] = self.params.get('assessments_enforced')
            
        if self.params.get('default_execution_mode'):
            attributes["default-execution-mode"] = self.params.get('default_execution_mode')
            
        if self.params.get('allow_force_delete_workspaces') is not None:
            attributes["allow-force-delete-workspaces"] = self.params.get('allow_force_delete_workspaces')
        
        # Build the payload
        payload = {
            "data": {
                "type": "organizations",
                "attributes": attributes
            }
        }
        
        # Make the API request
        response = self._request("PATCH", endpoint, data=payload)
        return response

    def _delete_organization(self):
        """Delete an organization from HCP Terraform."""
        endpoint = f"/organizations/{self.name}"
        
        # Make the API request
        response = self._request("DELETE", endpoint)
        return {"changed": True, "msg": f"Organization '{self.name}' deleted successfully"}

    def _format_organization_output(self, organization):
        """Format the organization output for better readability."""
        data = organization.get("data", {})
        attributes = data.get("attributes", {})
        
        formatted = {
            "id": data.get("id"),
            "name": attributes.get("name"),
            "email": attributes.get("email"),
            "description": attributes.get("description"),
            "collaborator_auth_policy": attributes.get("collaborator-auth-policy"),
            "created_at": attributes.get("created-at"),
            "cost_estimation_enabled": attributes.get("cost-estimation-enabled"),
            "assessments_enforced": attributes.get("assessments-enforced"),
            "default_execution_mode": attributes.get("default-execution-mode"),
            "allow_force_delete_workspaces": attributes.get("allow-force-delete-workspaces")
        }
        
        return formatted

    def run(self):
        """Main module execution logic."""
        try:
            # Get the current organization state
            organization = self._get_organization()
            
            # Return early if check mode
            if self.check_mode:
                if self.state == 'present' and not organization:
                    self.exit_json(changed=True, msg=f"Would create organization '{self.name}'")
                elif self.state == 'present' and organization:
                    self.exit_json(changed=True, msg=f"Would update organization '{self.name}'")
                elif self.state == 'absent' and organization:
                    self.exit_json(changed=True, msg=f"Would delete organization '{self.name}'")
                else:
                    self.exit_json(changed=False, msg=f"No changes needed for organization '{self.name}'")
            
            # Apply the requested state
            if self.state == 'present':
                if not organization:
                    # Create a new organization
                    response = self._create_organization()
                    self.exit_json(
                        changed=True,
                        msg=f"Organization '{self.name}' created successfully",
                        organization=self._format_organization_output(response),
                        result=response
                    )
                else:
                    # Update an existing organization
                    response = self._update_organization()
                    self.exit_json(
                        changed=True,
                        msg=f"Organization '{self.name}' updated successfully",
                        organization=self._format_organization_output(response),
                        result=response
                    )
            else:  # state == 'absent'
                if organization:
                    # Delete the organization
                    result = self._delete_organization()
                    self.exit_json(**result, result={"deleted": True})
                else:
                    # Organization already doesn't exist
                    self.exit_json(
                        changed=False,
                        msg=f"Organization '{self.name}' already does not exist",
                        result={"deleted": False}
                    )
                    
        except Exception as e:
            self.fail_json(msg=f"Error managing organization: {str(e)}")

def main():
    module = TerraformOrganizationModule()
    module.run()

if __name__ == "__main__":
    main()