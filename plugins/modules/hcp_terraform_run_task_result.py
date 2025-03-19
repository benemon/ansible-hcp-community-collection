#!/usr/bin/python
DOCUMENTATION = """
---
module: hcp_terraform_run_task_result
short_description: Send run task results back to HCP Terraform
description:
  - This module enables sending run task results back to HCP Terraform.
  - Supports sending running, passed, or failed statuses with optional detailed outcomes.
  - Can provide detailed outcome information that appears in the HCP Terraform UI.
  - Designed to work as part of an HCP Terraform Run Task integration workflow.
author: "benemon"
options:
  callback_url:
    description: "The callback URL to send results to (from the task_result_callback_url field in the run task request)."
    required: true
    type: str
  access_token:
    description: "The access token provided in the original run task request payload (from the access_token field)."
    required: true
    type: str
    no_log: true
  status:
    description: "The status of the run task."
    required: false
    choices: ["running", "passed", "failed"]
    default: "running"
    type: str
  message:
    description: "A short message describing the status of the task."
    required: false
    type: str
  url:
    description: "A URL where users can obtain more information about the task."
    required: false
    type: str
  outcomes:
    description: "Detailed outcomes for the run task that provide additional context in the Terraform UI."
    required: false
    type: list
    elements: dict
    suboptions:
      outcome_id:
        description: "A unique identifier for this outcome."
        required: true
        type: str
      description:
        description: "A one-line description of the result."
        required: true
        type: str
      body:
        description: "A detailed message in Markdown format (recommended under 1MB, max 5MB)."
        required: false
        type: str
      url:
        description: "A URL with more information about this result."
        required: false
        type: str
      tags:
        description: "An object containing tag arrays (special handling for severity and status)."
        required: false
        type: dict
"""

EXAMPLES = """
# Send a progress update (running status)
- name: Send run task progress update
  benemon.hcp_community_collection.hcp_terraform_run_task_result:
    callback_url: "{{ tfc_request.task_result_callback_url }}"
    access_token: "{{ tfc_request.access_token }}"
    status: "running"
    message: "Analysis in progress (2/4 checks complete)"
    url: "https://my-analysis-tool.example.com/runs/12345"

# Send a successful final result
- name: Send successful run task result
  benemon.hcp_community_collection.hcp_terraform_run_task_result:
    callback_url: "{{ tfc_request.task_result_callback_url }}"
    access_token: "{{ tfc_request.access_token }}"
    status: "passed"
    message: "All security checks passed"
    url: "https://my-analysis-tool.example.com/runs/12345"
    outcomes:
      - outcome_id: "SECURITY-001"
        description: "Encryption check passed"
        body: "# Encryption Check\\nAll resources properly encrypted."
        tags:
          Status:
            - label: "Passed"
              level: "info"
          Severity:
            - label: "High"
              level: "info"

# Send a failed final result with multiple outcomes
- name: Send failed run task result
  benemon.hcp_community_collection.hcp_terraform_run_task_result:
    callback_url: "{{ tfc_request.task_result_callback_url }}"
    access_token: "{{ tfc_request.access_token }}"
    status: "failed"
    message: "Security checks failed"
    url: "https://my-analysis-tool.example.com/runs/12345"
    outcomes:
      - outcome_id: "SECURITY-002"
        description: "S3 bucket missing encryption"
        body: "# Missing Encryption\\nS3 bucket `my-bucket` is missing server-side encryption."
        url: "https://docs.example.com/security/encryption"
        tags:
          Status:
            - label: "Failed"
              level: "error"
          Severity:
            - label: "High"
              level: "error"
      - outcome_id: "SECURITY-003"
        description: "Public access not blocked on S3 bucket"
        body: "# Public Access\\nS3 bucket `my-bucket` does not have public access blocks enabled."
        url: "https://docs.example.com/security/s3-public-access"
        tags:
          Status:
            - label: "Failed"
              level: "error"
          Severity:
            - label: "Medium"
              level: "warning"
"""

RETURN = """
changed:
  description: Always set to true when sending a run task result
  returned: always
  type: bool
message:
  description: Information about the action performed
  returned: always
  type: str
  sample: "Successfully sent run task result with status 'passed'"
status_code:
  description: HTTP status code from the API request
  returned: success
  type: int
  sample: 200
response:
  description: Full response from the API request (may be useful for debugging)
  returned: success
  type: dict
  sample: {"data": {"type": "task-results", "attributes": {"status": "passed"}}}
success:
  description: Whether the API call succeeded
  returned: always
  type: bool
  sample: true
"""

import json
import requests
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.benemon.hcp_community_collection.plugins.module_utils.hcp_terraform_module import HCPTerraformModule

class TerraformRunTaskResultModule(HCPTerraformModule):
    def __init__(self):
        # Define the argument specification for this module
        argument_spec = dict(
            callback_url=dict(type='str', required=True),
            access_token=dict(type='str', required=True, no_log=True),
            status=dict(type='str', required=False, choices=['running', 'passed', 'failed'], default='running'),
            message=dict(type='str', required=False),
            url=dict(type='str', required=False),
            outcomes=dict(
                type='list',
                elements='dict',
                required=False,
                options=dict(
                    outcome_id=dict(type='str', required=True),
                    description=dict(type='str', required=True),
                    body=dict(type='str', required=False),
                    url=dict(type='str', required=False),
                    tags=dict(type='dict', required=False)
                )
            )
        )

        # Initialize the base class (which is also an AnsibleModule)
        super().__init__(
            argument_spec=argument_spec,
            supports_check_mode=True
        )

        # Extract module parameters
        self.callback_url = self.params.get('callback_url')
        self.access_token = self.params.get('access_token')
        self.status = self.params.get('status')
        self.message = self.params.get('message')
        self.url = self.params.get('url')
        self.outcomes = self.params.get('outcomes')

    def send_result(self):
        """
        Send a run task result to HCP Terraform.
        """
        if self.status not in ['running', 'passed', 'failed']:
            self.fail_json(msg=f"Status must be 'running', 'passed', or 'failed', got '{self.status}'")
        
        # Build the request data
        data = {
            "data": {
                "type": "task-results",
                "attributes": {
                    "status": self.status
                }
            }
        }
        
        # Add optional fields if provided
        if self.message:
            data["data"]["attributes"]["message"] = self.message
        
        if self.url:
            data["data"]["attributes"]["url"] = self.url
        
        # Add outcomes if provided
        if self.outcomes:
            outcomes_data = []
            for outcome in self.outcomes:
                outcome_data = {
                    "type": "task-result-outcomes",
                    "attributes": {
                        "outcome-id": outcome['outcome_id'],
                        "description": outcome['description']
                    }
                }
                
                # Add optional outcome attributes
                if 'body' in outcome:
                    outcome_data["attributes"]["body"] = outcome['body']
                
                if 'url' in outcome:
                    outcome_data["attributes"]["url"] = outcome['url']
                
                if 'tags' in outcome:
                    outcome_data["attributes"]["tags"] = outcome['tags']
                
                outcomes_data.append(outcome_data)
            
            if outcomes_data:
                data["data"]["relationships"] = {
                    "outcomes": {
                        "data": outcomes_data
                    }
                }
        
        # Prepare the headers
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/vnd.api+json"
        }
        
        # Send the request
        try:
            response = requests.patch(
                self.callback_url,
                json=data,
                headers=headers
            )
            response.raise_for_status()
            
            # Return the results
            return {
                "changed": True,
                "status_code": response.status_code,
                "message": f"Successfully sent run task result with status '{self.status}'",
                "response": response.json() if response.text else None,
                "success": True
            }
            
        except requests.exceptions.RequestException as e:
            self.fail_json(
                msg=f"Error sending run task result: {str(e)}",
                status_code=getattr(e.response, 'status_code', None),
                response=getattr(e.response, 'text', None),
                success=False
            )

    def run(self):
        """
        Main module execution.
        """
        try:
            # Handle check mode
            if self.check_mode:
                self.exit_json(
                    changed=True,
                    message=f"Check mode: would send run task result with status '{self.status}'",
                    success=True
                )
            
            # Send the result
            result = self.send_result()
            self.exit_json(**result)
                
        except Exception as e:
            self.fail_json(
                msg=f"Error sending run task result: {str(e)}",
                success=False
            )

def main():
    module = TerraformRunTaskResultModule()
    module.run()

if __name__ == "__main__":
    main()