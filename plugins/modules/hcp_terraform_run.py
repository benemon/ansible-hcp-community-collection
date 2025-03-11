#!/usr/bin/python
DOCUMENTATION = """
---
module: hcp_terraform_run
short_description: Triggers a Terraform run in HCP Terraform or Terraform Enterprise.
description:
  - Starts a Terraform run in a specified workspace.
  - Supports plan-only, destroy, and auto-apply options.
  - Can wait for the run to complete before exiting.
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
    description: "ID of the Terraform workspace to execute the run in."
    required: true
    type: str
  message:
    description: "A description of the run."
    required: false
    type: str
    default: "Triggered by Ansible"
  is_destroy:
    description: "If true, the run will create a destroy plan instead of an apply plan."
    required: false
    type: bool
    default: false
  auto_apply:
    description: "If true, the changes will be automatically applied."
    required: false
    type: bool
    default: false
  plan_only:
    description: "If true, the run will generate a plan but not apply it."
    required: false
    type: bool
    default: false
  variables:
    description: "Key-value pairs of input variables for the run. Each item will be converted to a terraform variable."
    required: false
    type: dict
    default: {}
  targets:
    description: "A list of resource addresses to target in the run."
    required: false
    type: list
    elements: str
    default: []
  wait:
    description: "If true, the module will wait for the run to complete before exiting."
    required: false
    type: bool
    default: true
  timeout:
    description: "Maximum time (in seconds) to wait for execution completion."
    required: false
    type: int
    default: 600
"""

EXAMPLES = """
- name: Trigger a Terraform run and wait for completion
  benemon.hcp_community_collection.hcp_terraform_run:
    token: "{{ lookup('env', 'TFE_TOKEN') }}"
    workspace_id: "ws-abc123"
    message: "Run triggered from Ansible"
    auto_apply: true
    wait: true

- name: Plan-only run
  benemon.hcp_community_collection.hcp_terraform_run:
    token: "{{ lookup('env', 'TFE_TOKEN') }}"
    workspace_id: "ws-abc123"
    plan_only: true
    wait: false
    
- name: Run with variables
  benemon.hcp_community_collection.hcp_terraform_run:
    token: "{{ lookup('env', 'TFE_TOKEN') }}"
    workspace_id: "ws-abc123"
    variables:
      region: "us-west-2"
      instance_type: "t3.micro"

- name: Destroy run with auto-apply
  benemon.hcp_community_collection.hcp_terraform_run:
    token: "{{ lookup('env', 'TFE_TOKEN') }}"
    workspace_id: "ws-abc123"
    message: "Destroying infrastructure"
    is_destroy: true
    auto_apply: true

- name: Run targeting specific resources
  benemon.hcp_community_collection.hcp_terraform_run:
    token: "{{ lookup('env', 'TFE_TOKEN') }}"
    workspace_id: "ws-abc123"
    targets:
      - "aws_instance.web"
      - "aws_security_group.allow_http"
"""

RETURN = """
run_id:
  description: "The ID of the triggered run."
  returned: always
  type: str
  sample: "run-CZcmD7eagjhyX111"
status:
  description: "The final status of the run (only if wait=True)."
  returned: when wait=True
  type: str
  sample: "applied"
result:
  description: "Raw API response from Terraform."
  returned: always
  type: dict
  contains:
    data:
      description: "Information about the run."
      type: dict
      contains:
        id:
          description: "The run ID."
          type: str
          sample: "run-CZcmD7eagjhyX111"
        attributes:
          description: "Run attributes."
          type: dict
          contains:
            status:
              description: "Current status of the run."
              type: str
              sample: "planned_and_finished"
            message:
              description: "Run message."
              type: str
              sample: "Triggered by Ansible"
            is-destroy:
              description: "Whether this is a destroy run."
              type: bool
              sample: false
            auto-apply:
              description: "Whether auto-apply is enabled."
              type: bool
              sample: true
            plan-only: 
              description: "Whether this is a plan-only run."
              type: bool
              sample: false
            created-at:
              description: "When the run was created."
              type: str
              sample: "2023-05-15T18:24:16.591Z"
"""

from ansible_collections.benemon.hcp_community_collection.plugins.module_utils.hcp_terraform_module import HCPTerraformModule
import time

class TerraformRunModule(HCPTerraformModule):
    def __init__(self):
        # Define the argument specification for this module.
        argument_spec = dict(
            token=dict(type='str', required=True, no_log=True),
            hostname=dict(type='str', required=False, default="https://app.terraform.io"),
            workspace_id=dict(type='str', required=True),
            message=dict(type='str', required=False, default="Triggered by Ansible"),
            is_destroy=dict(type='bool', required=False, default=False),
            auto_apply=dict(type='bool', required=False, default=False),
            plan_only=dict(type='bool', required=False, default=False),
            variables=dict(type='dict', required=False, default={}),
            targets=dict(type='list', elements='str', required=False, default=[]),
            wait=dict(type='bool', required=False, default=True),
            timeout=dict(type='int', required=False, default=600),
        )
        
        # Initialize the base class (which is also an AnsibleModule)
        super().__init__(argument_spec=argument_spec, supports_check_mode=True)
        
        # Only extract params if we're not in a test environment
        if hasattr(self, 'params'):
            # Extract module-specific parameters.
            self.workspace_id = self.params.get('workspace_id')
            self.message = self.params.get('message')
            self.is_destroy = self.params.get('is_destroy')
            self.auto_apply = self.params.get('auto_apply')
            self.plan_only = self.params.get('plan_only')
            self.variables = self.params.get('variables')
            self.targets = self.params.get('targets')
            self.wait = self.params.get('wait')
            self.timeout = self.params.get('timeout')

    def trigger_run(self):
        """Triggers a Terraform run in the specified workspace."""
        endpoint = "/runs"
        payload = {
            "data": {
                "attributes": {
                    "message": self.message,
                    "is-destroy": self.is_destroy,
                    "auto-apply": self.auto_apply,
                    "plan-only": self.plan_only
                },
                "type": "runs",
                "relationships": {
                    "workspace": {
                        "data": {"type": "workspaces", "id": self.workspace_id}
                    }
                }
            }
        }

        if self.variables:
            payload["data"]["attributes"]["variables"] = [
                {"key": k, "value": v, "category": "terraform"} for k, v in self.variables.items()
            ]
        if self.targets:
            payload["data"]["attributes"]["target-addrs"] = self.targets

        response = self._request("POST", endpoint, data=payload)
        run_id = response["data"]["id"]
        return run_id, response

    def wait_for_run_completion(self, run_id):
        """Waits for the Terraform run to complete."""
        endpoint = f"/runs/{run_id}"
        start_time = time.time()
        while True:
            response = self._request("GET", endpoint)
            status = response["data"]["attributes"]["status"]
            if status in ["planned_and_finished", "applied", "errored", "discarded", "canceled", "force_canceled"]:
                return status, response
            if time.time() - start_time > self.timeout:
                self.fail_json(msg=f"Timeout waiting for Terraform run {run_id} to complete.", result=response)
            time.sleep(10)

    def run(self):
        """Main logic for triggering and monitoring the Terraform run."""
        try:
            if self.check_mode:
                self.exit_json(changed=False, msg="Check mode: no run triggered.")
                
            run_id, result = self.trigger_run()
            
            if self.wait:
                status, final_response = self.wait_for_run_completion(run_id)
                self.exit_json(
                    changed=True, 
                    run_id=run_id, 
                    status=status, 
                    result=final_response
                )
            else:
                self.exit_json(
                    changed=True, 
                    run_id=run_id, 
                    result=result
                )
        except Exception as e:
            error_msg = f"Error triggering Terraform run: {str(e)}"
            self.fail_json(msg=error_msg)

def main():
    module = TerraformRunModule()
    module.run()

if __name__ == "__main__":
    main()