#!/usr/bin/python
DOCUMENTATION = """
---
module: hcp_terraform_run
short_description: Triggers a Terraform run in HCP Terraform or Terraform Enterprise.
description:
  - Starts a Terraform run in a specified workspace.
  - Supports plan-only, destroy, and auto-apply options.
  - Can wait for the run to complete before exiting.
author: "Your Name"
options:
  token:
    description: "HCP Terraform API token."
    required: true
    type: str
  base_url:
    description: "Base URL for the Terraform API (Terraform Cloud or Terraform Enterprise)."
    required: false
    type: str
    default: "https://app.terraform.io/api/v2"
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
    description: "Key-value pairs of input variables for the run."
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
  hcp_terraform_run:
    token: "{{ lookup('env', 'TF_API_TOKEN') }}"
    workspace_id: "ws-abc123"
    message: "Run triggered from Ansible"
    auto_apply: true
    wait: true

- name: Plan-only run
  hcp_terraform_run:
    token: "{{ lookup('env', 'TF_API_TOKEN') }}"
    workspace_id: "ws-abc123"
    plan_only: true
    wait: false
"""

RETURN = """
run_id:
  description: "The ID of the triggered run."
  returned: always
  type: str
status:
  description: "The final status of the run (only if wait=True)."
  returned: when wait=True
  type: str
api_response:
  description: "Raw API response from Terraform."
  returned: always
  type: dict
"""

from ansible_collections.benemon.hcp_community_collection.plugins.module_utils.hcp_terraform_base import HCPTerraformBase
import time

class TerraformRunModule(HCPTerraformBase):
    def __init__(self):
        # Define the argument specification for this module.
        argument_spec = dict(
            token=dict(type='str', required=True, no_log=True),
            base_url=dict(type='str', required=False, default="https://app.terraform.io/api/v2"),
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
                    "is_destroy": self.is_destroy,
                    "auto_apply": self.auto_apply,
                    "plan_only": self.plan_only
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
            payload["data"]["attributes"]["target_addrs"] = self.targets

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
            if status in ["planned_and_finished","applied", "errored", "discarded", "canceled", "force_canceled"]:
                return status, response
            if time.time() - start_time > self.timeout:
                self.fail_json(msg=f"Timeout waiting for Terraform run {run_id} to complete.", api_response=response)
            time.sleep(10)

    def run(self):
        """Main logic for triggering and monitoring the Terraform run."""
        if self.check_mode:
            self.exit_json(changed=False, msg="Check mode: no run triggered.")
        run_id, api_response = self.trigger_run()
        if self.wait:
            status, final_response = self.wait_for_run_completion(run_id)
            self.exit_json(changed=True, run_id=run_id, status=status, api_response=final_response)
        else:
            self.exit_json(changed=True, run_id=run_id, api_response=api_response)

def main():
    module = TerraformRunModule()
    module.run()

if __name__ == "__main__":
    main()
