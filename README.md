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

| Plugin Name         | Description                                                                           |
|---------------------|---------------------------------------------------------------------------------------|
| `hvs_static_secret` | Retrieve a static secret from an Application in HCP Vault Secrets.                     |
| `hvs_dynamic_secret`| Retrieve a dynamic secret from an Application in HCP Vault Secrets.                    |
| `hvs_rotating_secret`| Retrieve a rotating secret from an Application in HCP Vault Secrets.                  |
| `hvs_secrets`       | Retrieve all secret metadata from an Application in HCP Vault Secrets.                  |
| `hvs_apps`          | Retrieve Application metadata from Applications in HCP Vault Secrets.                   |
| `packer_channel`    | Retrieve Channel metadata from HCP Packer.                                             |
| `packer_version`    | Retrieve Version metadata from HCP Packer.                                             |
| `packer_buckets`    | Retrieve metadata about buckets used for artifact storage in HCP Packer.                |
| `packer_channels`   | Retrieve a list of available channels in HCP Packer.                                    |
| `packer_versions`   | Retrieve a list of available Packer versions in HCP.                                    |


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

| Module Name | Description |
|-------------|-------------|
| `hcp_terraform_run` | Triggers a Terraform run in HCP Terraform or Terraform Enterprise. |

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
