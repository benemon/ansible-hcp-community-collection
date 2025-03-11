#!/usr/bin/python
DOCUMENTATION = """
---
module: hcp_terraform_project
short_description: Manages Terraform projects in HCP Terraform
description:
  - Creates, updates, and manages Terraform projects within an organization.
  - Projects help organize workspaces for easier management and permissions.
  - Supports configuration of project settings and attaching tags.
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
    description: "Name of the organization in which the project will be managed."
    required: true
    type: str
  name:
    description: "Name of the project."
    required: false
    type: str
  description:
    description: "Description of the project."
    required: false
    type: str
  auto_destroy_activity_duration:
    description: "Default for how long each workspace in the project should wait before automatically destroying its infrastructure."
    required: false
    type: str
  project_id:
    description: "ID of the project. Required when 'state=absent' and the project is specified by ID instead of name."
    required: false
    type: str
  tags:
    description: "List of tags to apply to the project. Each tag requires a 'key' and 'value'."
    required: false
    type: list
    elements: dict
    suboptions:
      key:
        description: "Tag key."
        required: true
        type: str
      value:
        description: "Tag value."
        required: true
        type: str
  state:
    description: "Whether the project should exist or not."
    required: false
    choices: ["present", "absent"]
    default: "present"
    type: str
"""

EXAMPLES = """
- name: Create a basic project
  benemon.hcp_community_collection.hcp_terraform_project:
    token: "{{ lookup('env', 'TFE_TOKEN') }}"
    organization: "my-organization"
    name: "My Project"
    description: "Created with Ansible"
    
- name: Create a project with tags
  benemon.hcp_community_collection.hcp_terraform_project:
    token: "{{ lookup('env', 'TFE_TOKEN') }}"
    organization: "my-organization"
    name: "Production Infrastructure"
    description: "Production environment resources"
    tags:
      - key: "environment"
        value: "production"
      - key: "department"
        value: "infrastructure"
    
- name: Create a project with auto-destroy settings
  benemon.hcp_community_collection.hcp_terraform_project:
    token: "{{ lookup('env', 'TFE_TOKEN') }}"
    organization: "my-organization"
    name: "Dev Project"
    description: "Development environment resources"
    auto_destroy_activity_duration: "14d"
    
- name: Update a project by name
  benemon.hcp_community_collection.hcp_terraform_project:
    token: "{{ lookup('env', 'TFE_TOKEN') }}"
    organization: "my-organization"
    name: "My Project"
    description: "Updated description"
    
- name: Remove a project
  benemon.hcp_community_collection.hcp_terraform_project:
    token: "{{ lookup('env', 'TFE_TOKEN') }}"
    organization: "my-organization"
    name: "Project to remove"
    state: "absent"
    
- name: Remove a project by ID
  benemon.hcp_community_collection.hcp_terraform_project:
    token: "{{ lookup('env', 'TFE_TOKEN') }}"
    organization: "my-organization"
    project_id: "prj-1234abcd"
    state: "absent"
"""

RETURN = """
project:
  description: "Details of the project."
  returned: when state=present
  type: dict
  contains:
    id:
      description: "The ID of the project."
      type: str
      sample: "prj-1234abcd"
    name:
      description: "The name of the project."
      type: str
      sample: "My Project"
    description:
      description: "The description of the project."
      type: str
      sample: "Created with Ansible"
    organization:
      description: "The name of the organization."
      type: str
      sample: "my-organization"
    auto_destroy_activity_duration:
      description: "Auto-destroy duration setting."
      type: str
      sample: "14d"
    created_at:
      description: "When the project was created."
      type: str
      sample: "2023-05-15T18:24:16.591Z"
    tags:
      description: "Tags associated with the project."
      type: list
      elements: dict
      contains:
        key:
          description: "Tag key."
          type: str
          sample: "environment"
        value:
          description: "Tag value."
          type: str
          sample: "production"
result:
  description: "Raw API response from HCP Terraform."
  returned: always
  type: dict
  contains:
    data:
      description: "Information about the project."
      type: dict
      contains:
        id:
          description: "The project ID."
          type: str
        attributes:
          description: "Project attributes."
          type: dict
        relationships:
          description: "Associated resources."
          type: dict
"""

from ansible_collections.benemon.hcp_community_collection.plugins.module_utils.hcp_terraform_module import HCPTerraformModule

class TerraformProjectModule(HCPTerraformModule):
    def __init__(self):
        # Define the argument specification for this module.
        argument_spec = dict(
            token=dict(type='str', required=True, no_log=True),
            hostname=dict(type='str', required=False, default="https://app.terraform.io"),
            organization=dict(type='str', required=True),
            name=dict(type='str', required=False),
            description=dict(type='str', required=False),
            auto_destroy_activity_duration=dict(type='str', required=False),
            project_id=dict(type='str', required=False),
            tags=dict(
                type='list',
                elements='dict',
                required=False,
                options=dict(
                    key=dict(type='str', required=True),
                    value=dict(type='str', required=True)
                )
            ),
            state=dict(type='str', required=False, choices=['present', 'absent'], default='present')
        )
        
        # Initialize the base class (which is also an AnsibleModule)
        super().__init__(
            argument_spec=argument_spec,
            supports_check_mode=True,
            required_one_of=[['name', 'project_id']],
            required_if=[['state', 'present', ['name']]]
        )
        
        # Extract the parameters
        self.organization = self.params.get('organization')
        self.name = self.params.get('name')
        self.project_id = self.params.get('project_id')
        self.state = self.params.get('state')

    def _get_project_by_name(self):
        """Retrieve the project from HCP Terraform using its name."""
        try:
            # List organization projects and filter by name
            endpoint = f"/organizations/{self.organization}/projects"
            # Add the name filter if provided
            params = {}
            if self.name:
                params = {'filter[names]': self.name}
                
            response = self._request("GET", endpoint, params=params)
            
            # Check if any project matches the name
            if response.get('data'):
                for project in response['data']:
                    if project['attributes']['name'] == self.name:
                        return project
            
            return None
        except Exception as e:
            # Re-raise exceptions
            raise

    def _get_project_by_id(self):
        """Retrieve the project from HCP Terraform using its ID."""
        try:
            endpoint = f"/projects/{self.project_id}"
            response = self._request("GET", endpoint)
            return response.get('data')
        except Exception as e:
            # If the project doesn't exist, return None
            if "404" in str(e) or "not found" in str(e).lower():
                return None
            # Re-raise other exceptions
            raise

    def _get_project(self):
        """Get a project by ID or name."""
        if self.project_id:
            return self._get_project_by_id()
        elif self.name:
            return self._get_project_by_name()
        return None
    
    def _create_tag_bindings_payload(self, tags):
        """Prepare tag bindings payload for a project."""
        if not tags:
            return None
        
        tag_bindings = []
        for tag in tags:
            tag_bindings.append({
                "type": "tag-bindings",
                "attributes": {
                    "key": tag.get('key'),
                    "value": tag.get('value')
                }
            })
        
        return tag_bindings

    def _create_project(self):
        """Create a new project in HCP Terraform."""
        endpoint = f"/organizations/{self.organization}/projects"
        
        # Prepare the attributes
        attributes = {
            "name": self.name
        }
        
        # Add optional attributes if they are set
        if self.params.get('description'):
            attributes["description"] = self.params.get('description')
            
        if self.params.get('auto_destroy_activity_duration'):
            attributes["auto-destroy-activity-duration"] = self.params.get('auto_destroy_activity_duration')
        
        # Build the payload
        payload = {
            "data": {
                "type": "projects",
                "attributes": attributes
            }
        }
        
        # Add tag bindings if provided
        tags = self.params.get('tags')
        if tags:
            tag_bindings = self._create_tag_bindings_payload(tags)
            if tag_bindings:
                payload["data"]["relationships"] = {
                    "tag-bindings": {
                        "data": tag_bindings
                    }
                }
        
        # Make the API request
        response = self._request("POST", endpoint, data=payload)
        
        # If there are tags, we need to get the project details to confirm they were added
        if tags:
            project_id = response.get("data", {}).get("id")
            if project_id:
                self.project_id = project_id
                return self._get_project_by_id()
                
        return response

    def _update_project(self, project):
        """Update an existing project in HCP Terraform."""
        project_id = project.get("id")
        if not project_id:
            self.fail_json(msg="Failed to get project ID from existing project")
            
        endpoint = f"/projects/{project_id}"
        
        # Prepare the attributes
        attributes = {}
        
        # Add attributes that are being updated
        if self.params.get('name'):
            attributes["name"] = self.params.get('name')
            
        if self.params.get('description') is not None:
            attributes["description"] = self.params.get('description')
            
        if self.params.get('auto_destroy_activity_duration') is not None:
            attributes["auto-destroy-activity-duration"] = self.params.get('auto_destroy_activity_duration')
        
        # Build the payload
        payload = {
            "data": {
                "type": "projects",
                "attributes": attributes
            }
        }
        
        # Add tag bindings if provided
        tags = self.params.get('tags')
        if tags:
            tag_bindings = self._create_tag_bindings_payload(tags)
            if tag_bindings:
                payload["data"]["relationships"] = {
                    "tag-bindings": {
                        "data": tag_bindings
                    }
                }
        
        # Make the API request
        response = self._request("PATCH", endpoint, data=payload)
        
        # If there are tags, we need to get the project details to confirm they were added
        if tags:
            return self._get_project_by_id()
                
        return response

    def _delete_project(self, project):
        """Delete a project from HCP Terraform."""
        project_id = project.get("id")
        if not project_id:
            self.fail_json(msg="Failed to get project ID from existing project")
            
        endpoint = f"/projects/{project_id}"
        
        # Make the API request
        self._request("DELETE", endpoint)
        return {"changed": True, "msg": f"Project '{self.name or project_id}' deleted successfully"}

    def _get_project_tags(self, project_id):
        """Get the tags associated with a project."""
        endpoint = f"/projects/{project_id}/tag-bindings"
        
        try:
            response = self._request("GET", endpoint)
            return response.get('data', [])
        except Exception as e:
            # If there's an error, return an empty list
            return []

    def _format_project_output(self, project, include_tags=True):
        """Format the project output for better readability."""
        if isinstance(project, dict) and 'data' in project:
            project = project.get('data', {})
            
        attributes = project.get("attributes", {})
        
        formatted = {
            "id": project.get("id"),
            "name": attributes.get("name"),
            "description": attributes.get("description"),
            "organization": self.organization,
            "auto_destroy_activity_duration": attributes.get("auto-destroy-activity-duration"),
            "created_at": attributes.get("created-at")
        }
        
        # Add tags if requested
        if include_tags and project.get("id"):
            tags_data = self._get_project_tags(project["id"])
            formatted["tags"] = []
            
            for tag in tags_data:
                tag_attrs = tag.get("attributes", {})
                formatted["tags"].append({
                    "key": tag_attrs.get("key"),
                    "value": tag_attrs.get("value")
                })
            
        return formatted

    def run(self):
        """Main module execution logic."""
        try:
            # Get the current project state
            project = self._get_project()
            
            # Return early if check mode
            if self.check_mode:
                if self.state == 'present' and not project:
                    self.exit_json(changed=True, msg=f"Would create project '{self.name}'")
                elif self.state == 'present' and project:
                    self.exit_json(changed=True, msg=f"Would update project '{self.name or project.get('id')}'")
                elif self.state == 'absent' and project:
                    self.exit_json(changed=True, msg=f"Would delete project '{self.name or project.get('id')}'")
                else:
                    self.exit_json(changed=False, msg=f"No changes needed for project '{self.name or self.project_id}'")
            
            # Apply the requested state
            if self.state == 'present':
                if not project:
                    # Create a new project
                    response = self._create_project()
                    self.exit_json(
                        changed=True,
                        msg=f"Project '{self.name}' created successfully",
                        project=self._format_project_output(response),
                        result=response
                    )
                else:
                    # Update an existing project
                    response = self._update_project(project)
                    self.exit_json(
                        changed=True,
                        msg=f"Project '{self.name or project.get('id')}' updated successfully",
                        project=self._format_project_output(response),
                        result=response
                    )
            else:  # state == 'absent'
                if project:
                    # Delete the project
                    result = self._delete_project(project)
                    self.exit_json(**result, result={"deleted": True})
                else:
                    # Project already doesn't exist
                    self.exit_json(
                        changed=False,
                        msg=f"Project '{self.name or self.project_id}' already does not exist",
                        result={"deleted": False}
                    )
                    
        except Exception as e:
            self.fail_json(msg=f"Error managing project: {str(e)}")

def main():
    module = TerraformProjectModule()
    module.run()

if __name__ == "__main__":
    main()