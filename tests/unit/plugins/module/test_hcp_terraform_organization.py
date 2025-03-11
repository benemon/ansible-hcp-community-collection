from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest
from unittest.mock import patch, MagicMock

from ansible_collections.benemon.hcp_community_collection.plugins.modules.hcp_terraform_organization import TerraformOrganizationModule
from ansible.module_utils.basic import AnsibleModule

# Mock responses for Organization API
ORGANIZATION_DETAILS_RESPONSE = {
    "data": {
        "id": "my-organization",
        "type": "organizations",
        "attributes": {
            "name": "my-organization",
            "email": "admin@example.com",
            "description": "Test organization description",
            "collaborator-auth-policy": "password",
            "created-at": "2023-04-16T20:42:53.771Z",
            "updated-at": "2023-04-16T20:42:53.771Z",
            "cost-estimation-enabled": False,
            "assessments-enforced": False,
            "default-execution-mode": "remote",
            "allow-force-delete-workspaces": False
        }
    }
}

ORGANIZATION_CREATE_RESPONSE = {
    "data": {
        "id": "new-organization",
        "type": "organizations",
        "attributes": {
            "name": "new-organization",
            "email": "new@example.com",
            "description": "New organization",
            "collaborator-auth-policy": "password",
            "created-at": "2023-04-16T20:42:53.771Z",
            "updated-at": "2023-04-16T20:42:53.771Z",
            "cost-estimation-enabled": False,
            "assessments-enforced": False,
            "default-execution-mode": "remote",
            "allow-force-delete-workspaces": False
        }
    }
}

# Fixture to create a mock TerraformOrganizationModule instance
@pytest.fixture
def organization_module():
    # Create a proper mock for AnsibleModule
    mock_ansible_module = MagicMock()
    mock_ansible_module.params = {
        'token': 'test-token',
        'hostname': 'https://app.terraform.io',
        'name': 'my-organization',
        'email': 'admin@example.com',
        'description': 'Test organization description',
        'collaborator_auth_policy': 'password',
        'cost_estimation_enabled': False,
        'assessments_enforced': False,
        'default_execution_mode': 'remote',
        'allow_force_delete_workspaces': False,
        'state': 'present'
    }
    mock_ansible_module.check_mode = False
    mock_ansible_module.fail_json = MagicMock()
    mock_ansible_module.exit_json = MagicMock()
    
    # Patch the __init__ of AnsibleModule to return our mock
    with patch.object(AnsibleModule, '__init__', return_value=None):
        with patch.object(TerraformOrganizationModule, '__init__', return_value=None) as mock_init:
            # Create the module
            module = TerraformOrganizationModule()
            
            # Set up the module with our mock properties
            module.params = mock_ansible_module.params
            module.check_mode = False
            module.name = 'my-organization'
            module.email = 'admin@example.com'
            module.state = 'present'
            module.fail_json = mock_ansible_module.fail_json
            module.exit_json = mock_ansible_module.exit_json
            module.token = 'test-token'
            module.hostname = 'https://app.terraform.io'
            
            yield module

# Test organization creation
def test_create_organization(organization_module):
    # Update params for a new organization
    organization_module.name = 'new-organization'
    organization_module.email = 'new@example.com'
    organization_module.params['name'] = 'new-organization'
    organization_module.params['email'] = 'new@example.com'
    
    # Mock the API requests
    with patch.object(organization_module, '_get_organization', return_value=None):
        with patch.object(organization_module, '_create_organization', return_value=ORGANIZATION_CREATE_RESPONSE):
            # Run the module
            organization_module.run()
            
            # Verify exit_json was called with the right parameters
            organization_module.exit_json.assert_called_once()
            call_args = organization_module.exit_json.call_args[1]
            assert call_args['changed'] is True
            assert call_args['msg'] == "Organization 'new-organization' created successfully"
            assert 'organization' in call_args
            assert call_args['organization']['name'] == 'new-organization'

# Test organization update
def test_update_organization(organization_module):
    # Set up a parameter that will trigger an update
    organization_module.params['description'] = "Updated organization description"
    
    # Mock the API requests
    with patch.object(organization_module, '_get_organization', return_value=ORGANIZATION_DETAILS_RESPONSE):
        with patch.object(organization_module, '_update_organization', return_value=ORGANIZATION_DETAILS_RESPONSE):
            # Run the module
            organization_module.run()
            
            # Verify exit_json was called with the right parameters
            organization_module.exit_json.assert_called_once()
            call_args = organization_module.exit_json.call_args[1]
            assert call_args['changed'] is True
            assert call_args['msg'] == "Organization 'my-organization' updated successfully"
            assert 'organization' in call_args

# Test organization deletion
def test_delete_organization(organization_module):
    # Set state to absent
    organization_module.state = 'absent'
    organization_module.params['state'] = 'absent'
    
    # Mock the API requests
    with patch.object(organization_module, '_get_organization', return_value=ORGANIZATION_DETAILS_RESPONSE):
        with patch.object(organization_module, '_delete_organization', return_value={"changed": True, "msg": "Organization 'my-organization' deleted successfully"}):
            # Run the module
            organization_module.run()
            
            # Verify exit_json was called with the right parameters
            organization_module.exit_json.assert_called_once()
            call_args = organization_module.exit_json.call_args[1]
            assert call_args['changed'] is True
            assert call_args['msg'] == "Organization 'my-organization' deleted successfully"

# Test check mode for creation
def test_check_mode_create(organization_module):
    # Set check mode to True
    organization_module.check_mode = True
    
    # Mock the API request
    with patch.object(organization_module, '_get_organization', return_value=None):
        # Run the module
        organization_module.run()
        
        # Verify exit_json was called with the right parameters
        organization_module.exit_json.assert_called_once()
        call_args = organization_module.exit_json.call_args[1]
        assert call_args['changed'] is True
        assert call_args['msg'] == "Would create organization 'my-organization'"

# Test check mode for update
def test_check_mode_update(organization_module):
    # Set check mode to True
    organization_module.check_mode = True
    
    # Mock the API request
    with patch.object(organization_module, '_get_organization', return_value=ORGANIZATION_DETAILS_RESPONSE):
        # Run the module
        organization_module.run()
        
        # Verify exit_json was called with the right parameters
        organization_module.exit_json.assert_called_once()
        call_args = organization_module.exit_json.call_args[1]
        assert call_args['changed'] is True
        assert call_args['msg'] == "Would update organization 'my-organization'"

# Test check mode for deletion
def test_check_mode_delete(organization_module):
    # Set check mode to True and state to absent
    organization_module.check_mode = True
    organization_module.state = 'absent'
    organization_module.params['state'] = 'absent'
    
    # Mock the API request
    with patch.object(organization_module, '_get_organization', return_value=ORGANIZATION_DETAILS_RESPONSE):
        # Run the module
        organization_module.run()
        
        # Verify exit_json was called with the right parameters
        organization_module.exit_json.assert_called_once()
        call_args = organization_module.exit_json.call_args[1]
        assert call_args['changed'] is True
        assert call_args['msg'] == "Would delete organization 'my-organization'"

# Test organization already exists (no op)
def test_organization_already_exists(organization_module):
    # Set state to absent for a non-existent organization
    organization_module.state = 'absent'
    organization_module.params['state'] = 'absent'
    
    # Mock the API request
    with patch.object(organization_module, '_get_organization', return_value=None):
        # Run the module
        organization_module.run()
        
        # Verify exit_json was called with the right parameters
        organization_module.exit_json.assert_called_once()
        call_args = organization_module.exit_json.call_args[1]
        assert call_args['changed'] is False
        assert call_args['msg'] == "Organization 'my-organization' already does not exist"

# Test error handling
def test_error_handling(organization_module):
    # Define a custom function that would be called by run() to handle errors properly
    def fail_json_side_effect(**kwargs):
        assert "Error managing organization: API Error" in kwargs.get('msg', '')
        raise Exception(kwargs.get('msg', 'API Error'))
    
    # Set up the fail_json mock to have a side effect
    organization_module.fail_json.side_effect = fail_json_side_effect
    
    # Mock the API request to raise an exception
    with patch.object(organization_module, '_get_organization', side_effect=Exception("API Error")):
        # Run the module
        with pytest.raises(Exception) as excinfo:
            organization_module.run()
        
        # Verify the error message contains our API error
        assert "Error managing organization" in str(excinfo.value)