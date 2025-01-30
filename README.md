# Ansible Collection: benemon.hcp_community

## Overview

The `benemon.hcp_community` Ansible Collection provides lookup plugins and utility modules for interacting with HashiCorp Cloud Platform (HCP) services.

It currently focuses on enabling the consumption of HashiCorp Vault Secrets in Ansible.

## Requirements

### Ansible Version Compatibility

This collection has been tested on Ansible Core 2.15.0 and later.

There are no expectations that earlier versions of Ansible Core will not work, but you may do so at your own risk.

*Please do feed back if earlier versions of Ansible Core work succesfully*

### Python Version Compatibility

This collection has been tested on Python 3.11 and later.

There are no expectations that earlier versions of Python will not work, but you may do so at your own risk. 

*Please do feed back if earlier versions of Python 3 work succesfully*

## Installation

To install the `benemon.hcp_community` collection, run:

```bash
ansible-galaxy collection install benemon.hcp_community
```

Alternatively, add it to a `requirements.yml` file:

```yaml
collections:
  - name: benemon.hcp_community
```

Then install it with:

```bash
ansible-galaxy collection install -r requirements.yml
```

## Available Plugins

### Lookup Plugins

## Available Lookup Plugins

The `benemon.hcp_community` collection provides the following lookup plugins:

| Plugin Name | Description |
|-------------|------------|
| `hvs_static_secret` | Retrieve a static secret from an Application in HCP Vault Secrets. |
| `hvs_dynamic_secret` | Retrieve a dynamic secret from an Application in HCP Vault Secrets. |
| `hvs_rotating_secret` | Retrieve a rotating secret from an Application in HCP Vault Secrets. |
| `hvs_secrets` | Retrieve all secret metadata from an Application in HCP Vault Secrets. |
| `hvs_apps` | Retrieve Application metadata from Applications in HCP Vault Secrets|

Each plugin can be used in playbooks by invoking the `lookup` function, as demonstrated in the examples below.

### Example Usage

#### Retrieving Static Secrets

```yaml
- name: Retrieve a static secret
  set_fact:
    secret_value: "{{ lookup('benemon.hcp_community.hvs_static_secret', 
                   'organization_id=' ~ hcp_organisation_id, 
                   'project_id=' ~ hcp_project_id,
                   'app_name=' ~ test_app_name,
                   'secret_name=' ~ test_secret_name) }}"

- name: Show static secret
  debug:
    var: secret_value
```

#### Retrieving Dynamic Secrets

```yaml
- name: Retrieve a dynamic secret
  set_fact:
    secret_value: "{{ lookup('benemon.hcp_community.hvs_dynamic_secret', 
                   'organization_id=' ~ hcp_organisation_id, 
                   'project_id=' ~ hcp_project_id,
                   'app_name=' ~ test_dynamic_app_name,
                   'secret_name=' ~ test_dynamic_secret_name) }}"

- name: Show dynamic secret
  debug:
    var: secret_value
```

#### Retrieving Rotating Secrets

```yaml
- name: Retrieve a rotating secret
  set_fact:
    secret_value: "{{ lookup('benemon.hcp_community.hvs_rotating_secret', 
                   'organization_id=' ~ hcp_organisation_id, 
                   'project_id=' ~ hcp_project_id,
                   'app_name=' ~ test_rotating_app_name,
                   'secret_name=' ~ test_rotating_secret_name) }}"

- name: Show rotating secret
  debug:
    var: secret_value
```

#### Retrieving All Secrets in an App

```yaml
- name: Retrieve all secret metadata from an app
  set_fact:
    all_secrets: "{{ lookup('benemon.hcp_community.hvs_secrets', 
                   'organization_id=' ~ hcp_organisation_id, 
                   'project_id=' ~ hcp_project_id,
                   'app_name=' ~ test_app_name) }}"

- name: Show all secrets
  debug:
    var: all_secrets
```

#### Retrieving Application

```yaml
- name: Retrieve all applications in an HCP Organisation
  set_fact:
    all_apps: "{{ lookup('benemon.hcp_community.hvs_apps', 
                'organization_id=' ~ hcp_organisation_id, 
                'project_id=' ~ hcp_project_id) }}"

- name: Show applications
  debug:
    var: all_apps
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
