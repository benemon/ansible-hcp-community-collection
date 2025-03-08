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

| Plugin Name               | Description                                                   |
|---------------------------|---------------------------------------------------------------|
| `hvs_static_secret`       | Retrieve a static secret from an Application in HCP Vault Secrets. |
| `hvs_dynamic_secret`      | Retrieve a dynamic secret from an Application in HCP Vault Secrets. |
| `hvs_rotating_secret`     | Retrieve a rotating secret from an Application in HCP Vault Secrets. |
| `hvs_secrets`             | Retrieve all secret metadata from an Application in HCP Vault Secrets. |
| `hvs_apps`                | Retrieve Application metadata from Applications in HCP Vault Secrets. |
| `packer_channel`          | Retrieve Channel metadata from HCP Packer. |
| `packer_version`          | Retrieve Version metadata from HCP Packer. |
| `packer_buckets`          | Retrieve metadata about buckets used for artifact storage in HCP Packer. |
| `packer_channels`         | Retrieve a list of available channels in HCP Packer. |
| `packer_versions`         | Retrieve a list of available Packer versions in HCP. |
| `hcp_terraform_projects`  | Retrieve a list of projects in HCP Terraform. |
| `hcp_terraform_oauth_tokens` | Retrieve OAuth tokens used for authentication with VCS providers in HCP Terraform. |


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
| `hcp_terraform_workspace`           | Manages Terraform workspaces in HCP.            |
| `hcp_terraform_workspace_variable`  | Manages workspace variables in Terraform.       |

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

```yaml
- name: Create and Configure Terraform Cloud Workspace
  hosts: localhost
  connection: local
  gather_facts: false
  vars:
    # Credentials will be read from environment variables
    organization: "my-organisation"
    project_name: "my-project"
    workspace_name: "aws-infra-ansible"
    repo_identifier: "my-repo/aws-infra"
    working_directory: ""  # Root of the repository
    oauth_client_id: "oc-someClientId67516v"  # Specific OAuth client ID
    tfe_token: "mySuperSecretToken"

  tasks:
    - name: Get OAuth tokens for the specified client
      set_fact:
        oauth_tokens: "{{ lookup('benemon.hcp_community_collection.hcp_terraform_oauth_tokens', 
                          'oauth_client_id=' ~ oauth_client_id,
                          'token=' ~ tfe_token) }}"
      register: oauth_result

    - name: Extract OAuth token ID
      set_fact:
        oauth_token_id: "{{ oauth_tokens.data[0].id }}"
      when: oauth_tokens.data | length > 0
      
    - name: Display OAuth token ID
      debug:
        msg: "Using OAuth token ID: {{ oauth_token_id }}"

    - name: Get project ID
      set_fact:
        projects: "{{ lookup('benemon.hcp_community_collection.hcp_terraform_projects', 
                      'organization=' ~organization,
                      'token=' ~ tfe_token) }}"
      register: projects_result

    - name: Find AWS project
      set_fact:
        project_id: "{{ projects.data | 
                       selectattr('attributes.name', 'equalto', project_name) | 
                       map(attribute='id') | first }}"
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

    - name: Display workspace information
      debug:
        msg: "Workspace created with ID: {{ workspace_result.workspace.id }}"

    - name: Create workspace variable
      benemon.hcp_community_collection.hcp_terraform_variable:
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

    - name: Trigger a plan-only run
      benemon.hcp_community_collection.hcp_terraform_run:
        workspace_id: "{{ workspace_result.workspace.id }}"
        message: "Initial plan triggered by Ansible"
        token: "{{ tfe_token }}"
        plan_only: true
        wait: true
      register: run_result

    - name: Display run status
      debug:
        msg: "Terraform plan completed with status: {{ run_result.status }}"

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
