# Ansible Collection: benemon.hcp_community_collection

[![Ansible Collection CI/CD](https://github.com/benemon/ansible-hcp-community-collection/actions/workflows/ansible-collection.yml/badge.svg)](https://github.com/benemon/ansible-hcp-community-collection/actions/workflows/ansible-collection.yml)

## Overview

The `benemon.hcp_community_collection` Ansible Collection provides lookup plugins and utility modules for interacting with HashiCorp Cloud Platform (HCP) services.

### Implemented Services

* [HashiCorp Vault Secrets](https://developer.hashicorp.com/hcp/docs/vault-secrets) - Partial
* [HashiCorp HCP Packer](https://developer.hashicorp.com/hcp/docs/packer) - Partial
* [HCP Terraform / Terraform Enterprise](https://developer.hashicorp.com/terraform/cloud-docs) - Partial

## Requirements

### Ansible Version Compatibility

This collection has been tested on Ansible Core 2.15.0 and later.

There are no expectations that earlier versions of Ansible Core will not work, but you may do so at your own risk.

*Please do feed back if earlier versions of Ansible Core work succesfully*

### Python Version Compatibility

This collection has been tested on Python 3.9 and later.

There are no expectations that earlier versions of Python will not work, but you may do so at your own risk. 

*Please do feed back if earlier versions of Python 3 work succesfully*

## Installation

To install the `benemon.hcp_community` collection, run:

```bash
ansible-galaxy collection install benemon.hcp_community_collection
```

Alternatively, add it to a `requirements.yml` file:

```yaml
collections:
  - name: benemon.hcp_community_collection
```

Then install it with:

```bash
ansible-galaxy collection install -r requirements.yml
```

## Lookup Plugins

### Available Lookup Plugins

The `benemon.hcp_community_collection` collection provides the following lookup plugins:

| Plugin Name                       | Description                                                   |
|-----------------------------------|---------------------------------------------------------------|
| `hvs_static_secret`               | Retrieve a static secret from an Application in HCP Vault Secrets. |
| `hvs_dynamic_secret`              | Retrieve a dynamic secret from an Application in HCP Vault Secrets. |
| `hvs_rotating_secret`             | Retrieve a rotating secret from an Application in HCP Vault Secrets. |
| `hvs_secrets`                     | Retrieve all secret metadata from an Application in HCP Vault Secrets. |
| `hvs_apps`                        | Retrieve Application metadata from Applications in HCP Vault Secrets. |
| `packer_channel`                  | Retrieve Channel metadata from HCP Packer. |
| `packer_version`                  | Retrieve Version metadata from HCP Packer. |
| `packer_buckets`                  | Retrieve metadata about buckets used for artifact storage in HCP Packer. |
| `packer_channels`                 | Retrieve a list of available channels in HCP Packer. |
| `packer_versions`                 | Retrieve a list of available Packer versions in HCP. |
| `hcp_terraform_projects`          | Retrieve a list of projects in HCP Terraform or Terraform Enterprise. |
| `hcp_terraform_oauth_clients`     | Retrieve OAuth clients used for VCS integration in HCP Terraform or Terraform Enterprise. |
| `hcp_terraform_oauth_tokens`      | Retrieve OAuth tokens used for authentication with VCS providers in HCP Terraform or Terraform Enterprise. |
| `hcp_terraform_variable_sets`     | Retrieve a list of variable sets in HCP Terraform or Terraform Enterprise. |
| `hcp_terraform_agent_pools`       | Retrieve a list of agent pools from HCP Terraform or Terraform Enterprise. |
| `hcp_terraform_agents`            | Retrieve a list of agents from HCP Terraform or Terraform Enterprise. |
| `hcp_terraform_organizations`     | Retrieve a list of organizations from HCP Terraform or Terraform Enterprise. |
| `hcp_terraform_state_version_outputs` | Retrieve state version outputs from HCP Terraform or Terraform Enterprise. |
| `hcp_terraform_state_versions`    | Retrieve state versions from HCP Terraform or Terraform Enterprise. |


Each plugin can be used in playbooks by invoking the `lookup` function, as demonstrated in the example below.

### Examples

#### HashiCorp Vault Secrets

```yaml
- name: run through some tasks with HashiCorp HCP Vault Secrets
  hosts: localhost
  vars:
    hcp_organisation_id: "my-organisation-id"
    hcp_project_id: "my-project-id"

  tasks:
  - name: Retrieve a static secret
    set_fact:
      secret_value: "{{ lookup('benemon.hcp_community_collection.hvs_static_secret', 
                    'organization_id=' ~ hcp_organisation_id, 
                    'project_id=' ~ hcp_project_id,
                    'app_name=sample-app',
                    'secret_name=sample-static-secret') }}"

  - name: Show static secret
    debug:
      var: secret_value

  - name: Retrieve a dynamic secret
    set_fact:
      secret_value: "{{ lookup('benemon.hcp_community_collection.hvs_dynamic_secret', 
                    'organization_id=' ~ hcp_organisation_id, 
                    'project_id=' ~ hcp_project_id,
                    'app_name=sample-app',
                    'secret_name=sample-dynamic-secret') }}"

  - name: Show dynamic secret
    debug:
      var: secret_value

  - name: Retrieve a rotating secret
    set_fact:
      secret_value: "{{ lookup('benemon.hcp_community_collection.hvs_rotating_secret', 
                    'organization_id=' ~ hcp_organisation_id, 
                    'project_id=' ~ hcp_project_id,
                    'app_name=sample-app',
                    'secret_name=sample-rotating-secret') }}"

  - name: Show rotating secret
    debug:
      var: secret_value

  - name: Retrieve all secret metadata from an app
    set_fact:
      all_secrets: "{{ lookup('benemon.hcp_community_collection.hvs_secrets', 
                    'organization_id=' ~ hcp_organisation_id, 
                    'project_id=' ~ hcp_project_id,
                    'app_name=sample-app') }}"

  - name: Show all secrets
    debug:
      var: all_secrets

  - name: Retrieve all applications in an HCP Organisation
    set_fact:
      all_apps: "{{ lookup('benemon.hcp_community_collection.hvs_apps', 
                  'organization_id=' ~ hcp_organisation_id, 
                  'project_id=' ~ hcp_project_id) }}"

  - name: Show applications
    debug:
      var: all_apps
```

#### HCP Packer

```yaml
- name: run through some tasks with HashiCorp HCP Packer
  hosts: localhost
  vars:
    hcp_organisation_id: "my-organisation-id"
    hcp_project_id: "my-project-id"

  tasks:
  - name: Retrieve channel information
    set_fact:
      channel_info: "{{ lookup('benemon.hcp_community_collection.packer_channel', 
                    'organization_id=' ~ hcp_organisation_id, 
                    'project_id=' ~ hcp_project_id,
                    'bucket_name=my-bucker-name',
                    'channel_name=latest') }}"

  - name: Show channel info
    debug:
      var: channel_info

    - name: Retrieve version information
      set_fact:
        version_info: "{{ lookup('benemon.hcp_community_collection.packer_version', 
                       'organization_id=' ~ hcp_organisation_id, 
                       'project_id=' ~ hcp_project_id,
                       'bucket_name=my-bucket-name',
                       'fingerprint=abc123') }}"

    - name: Show version info
      debug:
        var: version_info

    - name: Retrieve list of buckets
      hosts: localhost
      vars:
        hcp_organisation_id: "my-organisation-id"
        hcp_project_id: "my-project-id"
      tasks:
      - name: Retrieve bucket details
        set_fact:
          bucket_list: "{{ lookup('benemon.hcp_community_collection.packer_buckets', 
                              'organization_id=' ~ hcp_organisation_id, 
                              'project_id=' ~ hcp_project_id) }}"
      - name: Show buckets list
        debug:
          var: bucket_list

    - name: Retrieve available channels
      hosts: localhost
      vars:
        hcp_organisation_id: "my-organisation-id"
        hcp_project_id: "my-project-id"
        test_bucket_name: "my-bucket-name"
      tasks:
      - name: Retrieve channel information
        set_fact:
          channel_list: "{{ lookup('benemon.hcp_community_collection.packer_channels', 
                              'organization_id=' ~ hcp_organisation_id, 
                              'project_id=' ~ hcp_project_id,
                              'bucket_name=' ~ test_bucket_name) }}"
      - name: Show channels list
        debug:
          var: channel_list

      - name: Retrieve available Packer versions
        hosts: localhost
        vars:
          hcp_organisation_id: "my-organisation-id"
          hcp_project_id: "my-project-id"
          test_bucket_name: "my-bucket-name"
        tasks:
        - name: Retrieve version information
          set_fact:
            version_list: "{{ lookup('benemon.hcp_community_collection.packer_versions', 
                                'organization_id=' ~ hcp_organisation_id, 
                                'project_id=' ~ hcp_project_id,
                                'bucket_name=' ~ test_bucket_name) }}"
        - name: Show versions list
          debug:
            var: version_list
```

## Modules

### Available Modules

| Module Name                         | Description                                      |
|--------------------------------------|--------------------------------------------------|
| `hcp_terraform_run`                  | Triggers a Terraform run in HCP Terraform or Terraform Enterprise. |
| `hcp_terraform_workspace`           | Create and manage workspaces in HCP Terraform or Terraform Enterprise. |
| `hcp_terraform_workspace_variable`  | Create and manage workspace variables in HCP Terraform or Terraform Enterprise. |
| `hcp_terraform_variable_set`        | Create and manage variable sets at organization, project, and workspace levels in HCP Terraform or Terraform Enterprise. |
| `hcp_terraform_agent_pool`         | Create and manage agent pools in HCP Terraform or Terraform Enterprise. |
| `hcp_terraform_agent_token`        | Create and manage agent tokens in HCP Terraform or Terraform Enterprise. |
| `hcp_terraform_organization`        | Create and manage organizations in HCP Terraform or Terraform Enterprise. |
| `hcp_terraform_project`             | Create and manage projects in HCP Terraform or Terraform Enterprise. |

### Example Usage

#### HCP Terraform / Terraform Enterprise

```yaml
- name: Trigger a Terraform run
  hosts: localhost
  vars:
    terraform_token: "{{ lookup('env', 'TFE_TOKEN') }}"
    terraform_workspace_id: "ws-abc123"
  
  tasks:
  - name: Run a Terraform plan with auto-apply
    benemon.hcp_community_collection.hcp_terraform_run:
      token: "{{ terraform_token }}"
      workspace_id: "{{ terraform_workspace_id }}"
      message: "Run triggered from Ansible"
      auto_apply: true
      wait: true
    register: terraform_run

  - name: Show run results
    debug:
      var: terraform_run

  - name: Run a plan-only operation with variables
    benemon.hcp_community_collection.hcp_terraform_run:
      token: "{{ terraform_token }}"
      workspace_id: "{{ terraform_workspace_id }}"
      plan_only: true
      variables:
        instance_type: "t3.medium"
        environment: "staging"
    register: terraform_plan

  - name: Run a destroy operation
    benemon.hcp_community_collection.hcp_terraform_run:
      token: "{{ terraform_token }}"
      workspace_id: "{{ terraform_workspace_id }}"
      message: "Destroy environment"
      is_destroy: true
      auto_apply: true
      wait: true
    register: terraform_destroy
```

```yaml
- name: Create and Configure HCP Terraform / Terraform Enterprise Workspace from scratch
  hosts: localhost
  connection: local
  gather_facts: false
  vars:
    organization: "my-organisation"
    project_name: "my-project"
    workspace_name: "aws-infra-ansible"
    repo_identifier: "my-repo/aws-infra"
    working_directory: ""             # Root of the repository
    tfe_token: "{{ lookup('env', 'TFE_TOKEN') }}"
    varset_name: "AWS Credentials"     # The variable set name to search for
    service_provider: "github"          # Service provider type (must match API value)
    oauth_client_name: "GitHub.com"     # Display name of the OAuth client

  tasks:
    - name: Get OAuth client for GitHub
      set_fact:
        oauth_clients: "{{ lookup('benemon.hcp_community_collection.hcp_terraform_oauth_clients', 'organization=' ~ organization, 'service_provider=github', 'name=' ~ oauth_client_name, 'token=' ~ tfe_token) }}"
      register: oauth_clients_result

    - name: Extract OAuth client ID
      set_fact:
        oauth_client_id: "{{ oauth_clients.data[0].id }}"
      when: oauth_clients.data | length > 0

    - name: Display OAuth client ID
      debug:
        msg: "Using OAuth client ID: {{ oauth_client_id }}"
      when: oauth_clients.data | length > 0

    - name: Get OAuth tokens for the specified client
      set_fact:
        oauth_tokens: "{{ lookup('benemon.hcp_community_collection.hcp_terraform_oauth_tokens', 'oauth_client_id=' ~ oauth_client_id, 'token=' ~ tfe_token) }}"
      register: oauth_tokens_result

    - name: Extract OAuth token ID
      set_fact:
        oauth_token_id: "{{ oauth_tokens.data[0].id }}"
      when: oauth_tokens.data | length > 0
      
    - name: Display OAuth token ID
      debug:
        msg: "Using OAuth token ID: {{ oauth_token_id }}"

    - name: Get project ID with server-side filtering using q
      set_fact:
        projects: "{{ lookup('benemon.hcp_community_collection.hcp_terraform_projects', 'organization=' ~ organization, 'token=' ~ tfe_token, 'q=' ~ project_name) }}"
      register: projects_result

    - name: Extract project ID
      set_fact:
        project_id: "{{ projects.data | map(attribute='id') | first }}"
      when: projects.data | length > 0

    - name: Display project ID
      debug:
        msg: "Using project ID: {{ project_id }}"

    - name: Create Terraform workspace
      benemon.hcp_community_collection.hcp_terraform_workspace:
        organization: "{{ organization }}"
        token: "{{ tfe_token }}"
        name: "{{ workspace_name }}"
        description: "AWS Infrastructure managed through Ansible"
        project_id: "{{ project_id }}"
        terraform_version: "1.10.0"
        execution_mode: "remote"
        auto_apply: false
        working_directory: "{{ working_directory }}"
        vcs_repo:
          oauth_token_id: "{{ oauth_token_id }}"
          identifier: "{{ repo_identifier }}"
          branch: "main"
      register: workspace_result


    - name: Create workspace variable
      benemon.hcp_community_collection.hcp_terraform_workspace_variable:
        workspace_id: "{{ workspace_result.workspace.id }}"
        token: "{{ tfe_token }}"
        key: "instance_name"
        value: "ansible-instance"
        description: "Name of the EC2 instance"
        category: "terraform"
        hcl: false
      register: variable_result

    - name: Display variable information
      debug:
        msg: "Variable created: {{ variable_result.variable.key }}"

    - name: Find the AWS Credentials variable set with server-side filtering using q
      set_fact:
        varsets: "{{ lookup('benemon.hcp_community_collection.hcp_terraform_variable_sets', 
                    'organization=' ~ organization,
                    'token=' ~ tfe_token,
                    'q=' ~ varset_name) }}"
      register: varsets_result

    - name: Check if variable set was found
      debug:
        msg: "Found {{ varsets.data | length }} matching variable sets"

    - name: Extract variable set ID
      set_fact:
        varset_id: "{{ varsets.data[0].id }}"
      when: varsets.data | length > 0
      
    - name: Display variable set ID
      debug:
        msg: "Using variable set ID: {{ varset_id }}"
      when: varsets.data | length > 0

    - name: Update variable set to assign it to the workspace
      benemon.hcp_community_collection.hcp_terraform_variable_set:
        token: "{{ tfe_token }}"
        organization: "{{ organization }}"
        name: "{{ varset_name }}"
        workspace_ids:
          - "{{ workspace_result.workspace.id }}"
        state: present
      when: varsets.data | length > 0
      register: varset_update_result

    - name: Display result of variable set assignment
      debug:
        msg: "Variable set '{{ varset_name }}' successfully assigned to workspace"
      when: varsets.data | length > 0 and varset_update_result.changed

    - name: Trigger a a plan and apply for the workspace
      benemon.hcp_community_collection.hcp_terraform_run:
        workspace_id: "{{ workspace_result.workspace.id }}"
        message: "Initial plan triggered by Ansible"
        token: "{{ tfe_token }}"
        auto_apply: true
        wait: true
      register: run_result

    - name: Display run status
      debug:
        msg: "Terraform plan completed with status: {{ run_result.status }}"
    - name: Get the current state version for the workspace
      set_fact:
        state_version: "{{ lookup('benemon.hcp_community_collection.hcp_terraform_state_versions', 
                          'workspace_id=' ~ workspace_result.workspace.id,
                          'token=' ~ tfe_token,
                          'wait_for_processing=true',
                          'wait_timeout=180') }}"
      register: state_version_result
      when: workspace_result is defined

    - name: Display state version information
      debug:
        msg: 
          - "State version ID: {{ state_version.data.id }}"
          - "Created at: {{ state_version.data.attributes['created-at'] }}"
          - "Terraform version: {{ state_version.data.attributes['terraform-version'] }}"
          - "Resources processed: {{ state_version.data.attributes['resources-processed'] }}"
      when: state_version_result is defined and state_version_result.skipped is not defined

    - name: Get the state outputs for the workspace
      set_fact:
        state_outputs: "{{ lookup('benemon.hcp_community_collection.hcp_terraform_state_version_outputs', 
                          'workspace_id=' ~ workspace_result.workspace.id,
                          'token=' ~ tfe_token,
                          'wait_for_processing=true',
                          'wait_timeout=180') }}"
      register: state_outputs_result
      when: workspace_result is defined

    - name: Display all state outputs
      debug:
        var: state_outputs
      when: state_outputs is defined

    - name: Get instance_ami output
      set_fact:
        instance_ami: "{{ lookup('benemon.hcp_community_collection.hcp_terraform_state_version_outputs', 
                         'workspace_id=' ~ workspace_result.workspace.id,
                         'token=' ~ tfe_token,
                         'output_name=instance_ami') }}"
      register: instance_ami_result
      when: state_outputs is defined

    - name: Get instance_arn output
      set_fact:
        instance_arn: "{{ lookup('benemon.hcp_community_collection.hcp_terraform_state_version_outputs', 
                         'workspace_id=' ~ workspace_result.workspace.id,
                         'token=' ~ tfe_token,
                         'output_name=instance_arn') }}"
      register: instance_arn_result
      when: state_outputs is defined

    - name: Get instance_ip output
      set_fact:
        instance_ip: "{{ lookup('benemon.hcp_community_collection.hcp_terraform_state_version_outputs', 
                        'workspace_id=' ~ workspace_result.workspace.id,
                        'token=' ~ tfe_token,
                        'output_name=instance_ip') }}"
      register: instance_ip_result
      when: state_outputs is defined

    - name: Get public_dns output
      set_fact:
        public_dns: "{{ lookup('benemon.hcp_community_collection.hcp_terraform_state_version_outputs', 
                       'workspace_id=' ~ workspace_result.workspace.id,
                       'token=' ~ tfe_token,
                       'output_name=public_dns') }}"
      register: public_dns_result
      when: state_outputs is defined

    - name: Display all instance details
      debug:
        msg: |
          AWS EC2 Instance Details:
          ------------------------
          AMI: {{ instance_ami if instance_ami_result is defined else 'Not available' }}
          ARN: {{ instance_arn if instance_arn_result is defined else 'Not available' }}
          Public IP: {{ instance_ip if instance_ip_result is defined else 'Not available' }}
          Public DNS: {{ public_dns if public_dns_result is defined else 'Not available' }}
      when: state_outputs is defined

```

## Testing

This collection includes unit and integration tests:

### Unit Tests

Run unit tests using:

```bash
ansible-test unit --venv --python 3.11
```

### Integration Tests

Run integration tests using:

```bash
ansible-test shell
ansible-test integration
```

## Contributing

Contributions are welcome! To contribute:

1. Fork the repository.
2. Create a feature branch (`git checkout -b feature-branch`).
3. Make changes and test them.
4. Submit a pull request.

See the `CONTRIBUTING.md` file for detailed guidelines.

## License

This collection is licensed under the Apache-2.0 License. See the `LICENSE` file for details.