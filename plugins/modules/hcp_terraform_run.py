from ansible.module_utils.basic import AnsibleModule
from ansible_collections.benemon.hcp_community_collection.plugins.module_utils.base.hcp_terraform_base import HCPTerraformBase
import time

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

class TerraformRunModule(HCPTerraformBase):
    def __init__(self, module):
        """Initialize the module with input parameters."""
        super().__init__(token=module.params['token'], base_url=module.params['base_url'])
        self.module = module
        self.workspace_id = module.params['workspace_id']
        self.message = module.params['message']
        self.is_destroy = module.params['is_destroy']
        self.auto_apply = module.params['auto_apply']
        self.plan_only = module.params['plan_only']
        self.variables = module.params['variables']
        self.targets = module.params['targets']
        self.wait = module.params['wait']
        self.timeout = module.params['timeout']

    def trigger_run(self):
        """Triggers a Terraform run in the specified workspace."""
        endpoint = f"/runs"
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

        # Add variables if provided
        if self.variables:
            payload["data"]["attributes"]["variables"] = [
                {"key": k, "value": v, "category": "terraform"} for k, v in self.variables.items()
            ]

        # Add targets if provided
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

            if status in ["applied", "errored", "discarded"]:
                return status, response

            if time.time() - start_time > self.timeout:
                self.module.fail_json(msg=f"Timeout waiting for Terraform run {run_id} to complete.", api_response=response)

            time.sleep(10)

    def run(self):
        """Main logic for triggering and monitoring the Terraform run."""
        run_id, api_response = self.trigger_run()

        if self.wait:
            status, final_response = self.wait_for_run_completion(run_id)
            self.module.exit_json(changed=True, run_id=run_id, status=status, api_response=final_response)
        else:
            self.module.exit_json(changed=True, run_id=run_id, api_response=api_response)

def main():
    """Ansible module entry point."""
    module = AnsibleModule(
        argument_spec=dict(
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
        ),
        supports_check_mode=True
    )

    terraform_run = TerraformRunModule(module)
    terraform_run.run()

if __name__ == "__main__":
    main()
