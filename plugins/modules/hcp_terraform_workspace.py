#!/usr/bin/python
DOCUMENTATION = """
---
module: hcp_terraform_workspace
short_description: Manages Terraform workspaces in HCP Terraform or Terraform Enterprise
description:
  - Creates, updates, and manages Terraform workspaces.
  - Supports configuration of VCS repositories, execution modes, and other workspace settings.
  - Can assign workspaces to projects within organizations.
author: "benemon"
options:
  token:
    description: "HCP Terraform API token. This can be set via the TFE_TOKEN environment variable."
    required: true
    type: str
  hostname:
    description: "Hostname for the Terraform API (Terraform Cloud or Terraform Enterprise). This can be set via the TFE_HOSTNAME environment variable."
    required: false
    type: str
    default: "https://app.terraform.io"
  organization:
    description: "Name of the organization in which the workspace will be managed."
    required: true
    type: str
  name:
    description: "Name of the workspace."
    required: true
    type: str
  description:
    description: "Description of the workspace."
    required: false
    type: str
  project_id:
    description: "ID of the project to which the workspace belongs. If not specified, the workspace will belong to the default project."
    required: false
    type: str
  execution_mode:
    description: "Execution mode of the workspace (remote, local, or agent)."
    required: false
    choices: ["remote", "local", "agent"]
    type: str
    default: "remote"
  agent_pool_id:
    description: "ID of the agent pool to use when execution_mode is 'agent'."
    required: false
    type: str
  auto_apply:
    description: "Whether to automatically apply changes when a plan succeeds."
    required: false
    type: bool
    default: false
  terraform_version:
    description: "Terraform version to use for this workspace."
    required: false
    type: str
  working_directory:
    description: "Relative path that Terraform will execute in."
    required: false
    type: str
  vcs_repo:
    description: "VCS repository configuration."
    required: false
    type: dict
    suboptions:
      oauth_token_id:
        description: "OAuth token ID to use for VCS integration."
        required: true
        type: str
      identifier:
        description: "Repository path (e.g., 'username/repo' for GitHub)."
        required: true
        type: str
      branch:
        description: "Repository branch to use."
        required: false
        type: str
      ingress_submodules:
        description: "Whether to clone submodules when fetching the repository."
        required: false
        type: bool
        default: false
      tags_regex:
        description: "Regular expression to filter which tags to clone."
        required: false
        type: str
  allow_destroy_plan:
    description: "Whether destroy plans can be queued on the workspace."
    required: false
    type: bool
  speculative_enabled:
    description: "Whether speculative plans can be queued on the workspace."
    required: false
    type: bool
    default: true
  global_remote_state:
    description: "Whether the workspace should be accessible from all other workspaces in the organization."
    required: false
    type: bool
  state:
    description: "Whether the workspace should exist or not."
    required: false
    choices: ["present", "absent"]
    default: "present"
    type: str
  wait_for_creation:
    description: "Whether to wait for the workspace to be fully created before returning."
    required: false
    type: bool
    default: true
  timeout:
    description: "Maximum time (in seconds) to wait for creation completion."
    required: false
    type: int
    default: 300
"""

EXAMPLES = """
- name: Create a basic workspace
  benemon.hcp_community_collection.hcp_terraform_workspace:
    token: "{{ lookup('env', 'TFE_TOKEN') }}"
    organization: "my-organization"
    name: "my-workspace"
    description: "Created with Ansible"
    
- name: Create a workspace with VCS integration
  benemon.hcp_community_collection.hcp_terraform_workspace:
    token: "{{ lookup('env', 'TFE_TOKEN') }}"
    organization: "my-organization"
    name: "vcs-workspace"
    description: "Workspace connected to GitHub"
    vcs_repo:
      oauth_token_id: "ot-abcdefg123456"
      identifier: "my-org/my-repo"
      branch: "main"
    terraform_version: "1.5.7"
    auto_apply: true
    
- name: Create a workspace in a specific project
  benemon.hcp_community_collection.hcp_terraform_workspace:
    token: "{{ lookup('env', 'TFE_TOKEN') }}"
    organization: "my-organization"
    name: "project-workspace"
    project_id: "prj-1234abcd"
    execution_mode: "remote"
    
- name: Update a workspace to use agent-based execution
  benemon.hcp_community_collection.hcp_terraform_workspace:
    token: "{{ lookup('env', 'TFE_TOKEN') }}"
    organization: "my-organization"
    name: "agent-workspace"
    execution_mode: "agent"
    agent_pool_id: "apool-abcdefg123456"
    
- name: Remove a workspace
  benemon.hcp_community_collection.hcp_terraform_workspace:
    token: "{{ lookup('env', 'TFE_TOKEN') }}"
    organization: "my-organization"
    name: "workspace-to-remove"
    state: "absent"
"""

RETURN = """
workspace:
  description: "Details of the workspace."
  returned: when state=present
  type: dict
  contains:
    id:
      description: "The ID of the workspace."
      type: str
    name:
      description: "The name of the workspace."
      type: str
    description:
      description: "The description of the workspace."
      type: str
    organization:
      description: "The name of the organization."
      type: str
    execution_mode:
      description: "The execution mode of the workspace."
      type: str
    terraform_version:
      description: "The Terraform version of the workspace."
      type: str
    working_directory:
      description: "The working directory of the workspace."
      type: str
    auto_apply:
      description: "Whether auto apply is enabled."
      type: bool
    vcs_repo:
      description: "The VCS repository configuration."
      type: dict
result:
  description: "Raw API response from HCP Terraform."
  returned: always
  type: dict
"""

from ansible_collections.benemon.hcp_community_collection.plugins.module_utils.hcp_terraform_module import HCPTerraformModule
import time

class TerraformWorkspaceModule(HCPTerraformModule):
    def __init__(self):
        # Define the argument specification for this module.
        argument_spec = dict(
            token=dict(type='str', required=True, no_log=True),
            hostname=dict(type='str', required=False, default="https://app.terraform.io"),
            organization=dict(type='str', required=True),
            name=dict(type='str', required=True),
            description=dict(type='str', required=False),
            project_id=dict(type='str', required=False),
            execution_mode=dict(type='str', required=False, choices=['remote', 'local', 'agent'], default='remote'),
            agent_pool_id=dict(type='str', required=False),
            auto_apply=dict(type='bool', required=False, default=False),
            terraform_version=dict(type='str', required=False),
            working_directory=dict(type='str', required=False),
            vcs_repo=dict(type='dict', required=False, options=dict(
                oauth_token_id=dict(type='str', required=True),
                identifier=dict(type='str', required=True),
                branch=dict(type='str', required=False),
                ingress_submodules=dict(type='bool', required=False, default=False),
                tags_regex=dict(type='str', required=False)
            )),
            allow_destroy_plan=dict(type='bool', required=False),
            speculative_enabled=dict(type='bool', required=False, default=True),
            global_remote_state=dict(type='bool', required=False),
            state=dict(type='str', required=False, choices=['present', 'absent'], default='present'),
            wait_for_creation=dict(type='bool', required=False, default=True),
            timeout=dict(type='int', required=False, default=300)
        )
        
        # Initialize the base class (which is also an AnsibleModule)
        super().__init__(
            argument_spec=argument_spec,
            supports_check_mode=True,
            required_if=[
                ['execution_mode', 'agent', ['agent_pool_id']]
            ]
        )
        
        # Only extract params if we're not in a test environment
        if hasattr(self, 'params'):
            # Extract the parameters
            self.organization = self.params.get('organization')
            self.name = self.params.get('name')
            self.state = self.params.get('state')
            self.wait_for_creation = self.params.get('wait_for_creation')
            self.timeout = self.params.get('timeout')

    def _get_workspace(self):
        """Retrieve the workspace from HCP Terraform if it exists."""
        try:
            endpoint = f"/organizations/{self.organization}/workspaces/{self.name}"
            response = self._request("GET", endpoint)
            return response
        except Exception as e:
            # If the workspace doesn't exist, return None
            if "404" in str(e) or "not found" in str(e).lower():
                return None
            # Re-raise other exceptions
            raise

    def _prepare_vcs_payload(self, vcs_repo):
        """Prepare the VCS repository payload."""
        if not vcs_repo:
            return None
            
        vcs_payload = {
            "oauth-token-id": vcs_repo.get('oauth_token_id'),
            "identifier": vcs_repo.get('identifier')
        }
        
        # Add optional fields if present
        if 'branch' in vcs_repo and vcs_repo['branch']:
            vcs_payload["branch"] = vcs_repo['branch']
        
        if 'ingress_submodules' in vcs_repo:
            vcs_payload["ingress-submodules"] = vcs_repo['ingress_submodules']
            
        if 'tags_regex' in vcs_repo and vcs_repo['tags_regex']:
            vcs_payload["tags-regex"] = vcs_repo['tags_regex']
            
        return vcs_payload

    def _create_workspace(self):
        """Create a new workspace in HCP Terraform."""
        endpoint = f"/organizations/{self.organization}/workspaces"
        
        # Prepare the attributes
        attributes = {
            "name": self.name,
            "execution-mode": self.params.get('execution_mode'),
            "auto-apply": self.params.get('auto_apply'),
            "speculative-enabled": self.params.get('speculative_enabled')
        }
        
        # Add optional attributes if they are set
        if self.params.get('description'):
            attributes["description"] = self.params.get('description')
            
        if self.params.get('terraform_version'):
            attributes["terraform-version"] = self.params.get('terraform_version')
            
        if self.params.get('working_directory'):
            attributes["working-directory"] = self.params.get('working_directory')
            
        if self.params.get('agent_pool_id') and self.params.get('execution_mode') == 'agent':
            attributes["agent-pool-id"] = self.params.get('agent_pool_id')
            
        if self.params.get('allow_destroy_plan') is not None:
            attributes["allow-destroy-plan"] = self.params.get('allow_destroy_plan')
            
        if self.params.get('global_remote_state') is not None:
            attributes["global-remote-state"] = self.params.get('global_remote_state')
        
        # Build the payload
        payload = {
            "data": {
                "type": "workspaces",
                "attributes": attributes
            }
        }
        
        # Add project relationship if project_id is provided
        if self.params.get('project_id'):
            payload["data"]["relationships"] = {
                "project": {
                    "data": {
                        "id": self.params.get('project_id'),
                        "type": "projects"
                    }
                }
            }
        
        # Add VCS repository configuration if provided
        vcs_repo = self.params.get('vcs_repo')
        if vcs_repo:
            vcs_payload = self._prepare_vcs_payload(vcs_repo)
            if vcs_payload:
                attributes["vcs-repo"] = vcs_payload
        
        # Make the API request
        response = self._request("POST", endpoint, data=payload)
        
        # Wait for workspace to be fully created if requested
        if self.wait_for_creation:
            workspace_id = response.get("data", {}).get("id")
            if workspace_id:
                self._wait_for_workspace(workspace_id)
                
        return response

    def _update_workspace(self, workspace):
        """Update an existing workspace in HCP Terraform."""
        workspace_id = workspace.get("data", {}).get("id")
        if not workspace_id:
            self.fail_json(msg="Failed to get workspace ID from existing workspace")
            
        endpoint = f"/workspaces/{workspace_id}"
        
        # Prepare the attributes
        attributes = {}
        
        # Add attributes that are being updated
        if self.params.get('description') is not None:
            attributes["description"] = self.params.get('description')
            
        if self.params.get('execution_mode'):
            attributes["execution-mode"] = self.params.get('execution_mode')
            
        if self.params.get('terraform_version'):
            attributes["terraform-version"] = self.params.get('terraform_version')
            
        if self.params.get('working_directory') is not None:
            attributes["working-directory"] = self.params.get('working_directory')
            
        if self.params.get('auto_apply') is not None:
            attributes["auto-apply"] = self.params.get('auto_apply')
            
        if self.params.get('speculative_enabled') is not None:
            attributes["speculative-enabled"] = self.params.get('speculative_enabled')
            
        if self.params.get('agent_pool_id') and self.params.get('execution_mode') == 'agent':
            attributes["agent-pool-id"] = self.params.get('agent_pool_id')
            
        if self.params.get('allow_destroy_plan') is not None:
            attributes["allow-destroy-plan"] = self.params.get('allow_destroy_plan')
            
        if self.params.get('global_remote_state') is not None:
            attributes["global-remote-state"] = self.params.get('global_remote_state')
        
        # Add VCS repository configuration if provided
        vcs_repo = self.params.get('vcs_repo')
        if vcs_repo:
            vcs_payload = self._prepare_vcs_payload(vcs_repo)
            if vcs_payload:
                attributes["vcs-repo"] = vcs_payload
        
        # Build the payload
        payload = {
            "data": {
                "type": "workspaces",
                "id": workspace_id,
                "attributes": attributes
            }
        }
        
        # Add project relationship if project_id is provided
        if self.params.get('project_id'):
            payload["data"]["relationships"] = {
                "project": {
                    "data": {
                        "id": self.params.get('project_id'),
                        "type": "projects"
                    }
                }
            }
        
        # Make the API request
        response = self._request("PATCH", endpoint, data=payload)
        return response

    def _delete_workspace(self):
        """Delete a workspace from HCP Terraform."""
        workspace = self._get_workspace()
        if not workspace:
            return {"changed": False, "msg": f"Workspace '{self.name}' does not exist"}
            
        workspace_id = workspace.get("data", {}).get("id")
        if not workspace_id:
            self.fail_json(msg="Failed to get workspace ID from existing workspace")
            
        endpoint = f"/workspaces/{workspace_id}"
        
        # Make the API request
        response = self._request("DELETE", endpoint)
        return {"changed": True, "msg": f"Workspace '{self.name}' deleted successfully"}

    def _wait_for_workspace(self, workspace_id):
        """Wait for a workspace to be fully created and ready."""
        endpoint = f"/workspaces/{workspace_id}"
        start_time = time.time()
        
        while True:
            # Check if the timeout has been reached
            if time.time() - start_time > self.timeout:
                self.fail_json(msg=f"Timeout waiting for workspace {workspace_id} to be ready")
                
            # Make the request
            response = self._request("GET", endpoint)
            
            # Check if the workspace is ready (no specific marker in API, assume it's ready if we get a 200)
            if response and response.get("data", {}).get("id") == workspace_id:
                return response
                
            # Wait for a bit before checking again
            time.sleep(5)

    def _format_workspace_output(self, workspace):
        """Format the workspace output for better readability."""
        data = workspace.get("data", {})
        attributes = data.get("attributes", {})
        
        formatted = {
            "id": data.get("id"),
            "name": attributes.get("name"),
            "description": attributes.get("description"),
            "organization": self.organization,
            "execution_mode": attributes.get("execution-mode"),
            "terraform_version": attributes.get("terraform-version"),
            "working_directory": attributes.get("working-directory"),
            "auto_apply": attributes.get("auto-apply"),
            "created_at": attributes.get("created-at"),
            "updated_at": attributes.get("updated-at"),
        }
        
        # Add VCS repository information if available
        vcs_repo = attributes.get("vcs-repo")
        if vcs_repo:
            formatted["vcs_repo"] = {
                "identifier": vcs_repo.get("identifier"),
                "branch": vcs_repo.get("branch"),
                "ingress_submodules": vcs_repo.get("ingress-submodules"),
                "oauth_token_id": vcs_repo.get("oauth-token-id")
            }
            
        # Add project information if available
        if data.get("relationships", {}).get("project", {}).get("data", {}).get("id"):
            formatted["project_id"] = data["relationships"]["project"]["data"]["id"]
            
        return formatted

    def run(self):
        """Main module execution logic."""
        try:
            # Get the current workspace state
            workspace = self._get_workspace()
            
            # Return early if check mode
            if self.check_mode:
                if self.state == 'present' and not workspace:
                    self.exit_json(changed=True, msg=f"Would create workspace '{self.name}'")
                elif self.state == 'present' and workspace:
                    self.exit_json(changed=True, msg=f"Would update workspace '{self.name}'")
                elif self.state == 'absent' and workspace:
                    self.exit_json(changed=True, msg=f"Would delete workspace '{self.name}'")
                else:
                    self.exit_json(changed=False, msg=f"No changes needed for workspace '{self.name}'")
            
            # Apply the requested state
            if self.state == 'present':
                if not workspace:
                    # Create a new workspace
                    response = self._create_workspace()
                    self.exit_json(
                        changed=True,
                        msg=f"Workspace '{self.name}' created successfully",
                        workspace=self._format_workspace_output(response),
                        result=response
                    )
                else:
                    # Update an existing workspace
                    response = self._update_workspace(workspace)
                    self.exit_json(
                        changed=True,
                        msg=f"Workspace '{self.name}' updated successfully",
                        workspace=self._format_workspace_output(response),
                        result=response
                    )
            else:  # state == 'absent'
                if workspace:
                    # Delete the workspace
                    result = self._delete_workspace()
                    self.exit_json(**result, result={"deleted": True})
                else:
                    # Workspace already doesn't exist
                    self.exit_json(
                        changed=False,
                        msg=f"Workspace '{self.name}' already does not exist",
                        result={"deleted": False}
                    )
                    
        except Exception as e:
            self.fail_json(msg=f"Error managing workspace: {str(e)}")

def main():
    module = TerraformWorkspaceModule()
    module.run()

if __name__ == "__main__":
    main()