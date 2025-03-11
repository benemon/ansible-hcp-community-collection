from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest
from unittest.mock import patch, MagicMock

from ansible_collections.benemon.hcp_community_collection.plugins.modules.hcp_terraform_variable_set import TerraformVariableSetModule
from ansible.module_utils.basic import AnsibleModule

# Mock responses for Variable Set API
VARSET_LIST_RESPONSE = {
    "data": [
        {
            "id": "varset-123456",
            "type": "varsets",
            "attributes": {
                "name": "test-variable-set",
                "global": False,
                "priority": False
            }
        }
    ]
}

VARSET_CREATE_RESPONSE = {
    "data": {
        "id": "varset-123456",
        "type": "varsets",
        "attributes": {
            "name": "test-variable-set",
            "global": False,
            "priority": False,
            "description": "A new variable set"
        },
        "relationships": {
            "vars": {
                "data": [
                    {"id": "var-abc123", "type": "vars"}
                ]
            },
            "projects": {
                "data": [
                    {"id": "prj-def456", "type": "projects"}
                ]
            }
        },
        "included": [
            {
                "id": "var-abc123",
                "type": "vars",
                "attributes": {
                    "key": "test_var",
                    "value": "test_value",
                    "category": "terraform",
                    "sensitive": False
                }
            }
        ]
    }
}

VARSET_DETAILS_RESPONSE = {
    "data": {
        "id": "varset-123456",
        "type": "varsets",
        "attributes": {
            "name": "test-variable-set",
            "global": False,
            "priority": False,
            "description": "Test variable set"
        },
        "relationships": {
            "vars": {
                "data": [
                    {"id": "var-abc123", "type": "vars"}
                ]
            },
            "projects": {
                "data": [
                    {"id": "prj-def456", "type": "projects"}
                ]
            }
        },
        "included": [
            {
                "id": "var-abc123",
                "type": "vars",
                "attributes": {
                    "key": "test_var",
                    "value": "test_value",
                    "category": "terraform",
                    "sensitive": False
                }
            }
        ]
    }
}

# Fixture to create a mock TerraformVariableSetModule instance
@pytest.fixture
def variable_set_module():
    # Create a proper mock for AnsibleModule
    mock_ansible_module = MagicMock()
    mock_ansible_module.params = {
        'token': 'test-token',
        'hostname': 'https://app.terraform.io',
        'organization': 'test-org',
        'name': 'test-variable-set',
        'description': 'Test variable set',
        'state': 'present',
        'global_set': False,
        'priority': False,
        'project_ids': ['prj-def456'],
        'workspace_ids': [],
        'variables': [
            {
                'key': 'test_var',
                'value': 'test_value',
                'category': 'terraform'
            }
        ]
    }
    mock_ansible_module.check_mode = False
    mock_ansible_module.fail_json = MagicMock()
    mock_ansible_module.exit_json = MagicMock()
    
    # Patch the __init__ of AnsibleModule to return our mock
    with patch.object(AnsibleModule, '__init__', return_value=None):
        with patch.object(TerraformVariableSetModule, '__init__', return_value=None) as mock_init:
            # Create the module
            module = TerraformVariableSetModule()
            
            # Set up the module with our mock properties
            module.params = mock_ansible_module.params
            module.check_mode = False
            module.organization = 'test-org'
            module.name = 'test-variable-set'
            module.state = 'present'
            module.fail_json = mock_ansible_module.fail_json
            module.exit_json = mock_ansible_module.exit_json
            module.token = 'test-token'
            module.hostname = 'https://app.terraform.io'
            
            yield module

# Test variable set creation
def test_create_variable_set(variable_set_module):
    # Mock the API requests
    with patch.object(variable_set_module, '_get_variable_set', return_value=None):
        with patch.object(variable_set_module, '_create_variable_set', return_value=VARSET_CREATE_RESPONSE):
            # Run the module
            variable_set_module.run()
            
            # Verify exit_json was called with the right parameters
            variable_set_module.exit_json.assert_called_once()
            call_args = variable_set_module.exit_json.call_args[1]
            assert call_args['changed'] is True
            assert call_args['msg'] == "Variable set 'test-variable-set' created successfully"
            assert 'variable_set' in call_args
            assert call_args['variable_set']['name'] == 'test-variable-set'

# Test variable set update
def test_update_variable_set(variable_set_module):
    # Set up parameters that would trigger an update
    variable_set_module.params['description'] = "Updated description"  # Different from VARSET_DETAILS_RESPONSE
    
    # Current variable in API (from VARSET_DETAILS_RESPONSE)
    # The description will be different from what's in params, triggering an update
    current_variable_set = VARSET_DETAILS_RESPONSE.copy()
    current_variable_set['data']['attributes']['description'] = "Test variable set"  # Original description
    
    # Mock the API requests
    with patch.object(variable_set_module, '_get_variable_set', return_value=current_variable_set):
        with patch.object(variable_set_module, '_update_variable_set', return_value=VARSET_CREATE_RESPONSE):
            # Run the module
            variable_set_module.run()
            
            # Verify exit_json was called with the right parameters
            variable_set_module.exit_json.assert_called_once()
            call_args = variable_set_module.exit_json.call_args[1]
            assert call_args['changed'] is True
            assert call_args['msg'] == "Variable set 'test-variable-set' updated successfully"

# Test variable set deletion
def test_delete_variable_set(variable_set_module):
    # Set state to absent
    variable_set_module.state = 'absent'
    
    # Mock the API requests
    with patch.object(variable_set_module, '_get_variable_set', return_value=VARSET_DETAILS_RESPONSE):
        with patch.object(variable_set_module, '_delete_variable_set', return_value={"changed": True, "msg": "Variable set 'test-variable-set' deleted successfully"}):
            # Run the module
            variable_set_module.run()
            
            # Verify exit_json was called with the right parameters
            variable_set_module.exit_json.assert_called_once()
            call_args = variable_set_module.exit_json.call_args[1]
            assert call_args['changed'] is True
            assert call_args['msg'] == "Variable set 'test-variable-set' deleted successfully"

# Test check mode behavior
def test_check_mode(variable_set_module):
    # Set check mode to True
    variable_set_module.check_mode = True
    
    # Mock the API request
    with patch.object(variable_set_module, '_get_variable_set', return_value=None):
        # Run the module
        variable_set_module.run()
        
        # Verify exit_json was called with the right parameters
        variable_set_module.exit_json.assert_called_once()
        call_args = variable_set_module.exit_json.call_args[1]
        assert call_args['changed'] is True
        assert call_args['msg'] == "Would create variable set 'test-variable-set'"

# Test global variable set creation
def test_create_global_variable_set(variable_set_module):
    # Modify the module to create a global variable set
    variable_set_module.params['global_set'] = True
    
    # Create a modified response for global variable set
    global_varset_response = VARSET_CREATE_RESPONSE.copy()
    global_varset_response['data']['attributes']['global'] = True
    
    # Mock the API requests
    with patch.object(variable_set_module, '_get_variable_set', return_value=None):
        with patch.object(variable_set_module, '_create_variable_set', return_value=global_varset_response):
            # Run the module
            variable_set_module.run()
            
            # Verify exit_json was called with the right parameters
            variable_set_module.exit_json.assert_called_once()
            call_args = variable_set_module.exit_json.call_args[1]
            assert call_args['changed'] is True
            assert 'variable_set' in call_args
            assert call_args['variable_set']['global'] is True

# Test no update needed
def test_no_update_needed(variable_set_module):
    # Create a response that matches the current state
    no_change_response = VARSET_DETAILS_RESPONSE.copy()
    
    # Mock the API request
    with patch.object(variable_set_module, '_get_variable_set', return_value=no_change_response):
        # Run the module
        variable_set_module.run()
        
        # Verify exit_json was called with the right parameters
        variable_set_module.exit_json.assert_called_once()
        call_args = variable_set_module.exit_json.call_args[1]
        assert call_args['changed'] is False
        assert call_args['msg'] == "Variable set 'test-variable-set' already up-to-date"

# Test error handling
def test_error_handling(variable_set_module):
    # Define a custom function that would be called by run() to handle errors properly
    def fail_json_side_effect(**kwargs):
        assert "Error managing variable set" in kwargs.get('msg', '')
        raise Exception(kwargs.get('msg', 'API Error'))
    
    # Set up the fail_json mock to have a side effect
    variable_set_module.fail_json.side_effect = fail_json_side_effect
    
    # Mock the API request to raise an exception
    with patch.object(variable_set_module, '_get_variable_set', side_effect=Exception("API Error")):
        # Run the module
        with pytest.raises(Exception) as excinfo:
            variable_set_module.run()
        
        # Verify the error message contains our API error
        assert "API Error" in str(excinfo.value)

# Test variable set with multiple project assignments
def test_create_variable_set_multiple_projects(variable_set_module):
    # Modify the module to have multiple project IDs
    variable_set_module.params['project_ids'] = ['prj-def456', 'prj-ghi789']
    
    # Create a modified response with multiple projects
    multi_project_response = VARSET_CREATE_RESPONSE.copy()
    multi_project_response['data']['relationships']['projects']['data'] = [
        {"id": "prj-def456", "type": "projects"},
        {"id": "prj-ghi789", "type": "projects"}
    ]
    
    # Mock the API requests
    with patch.object(variable_set_module, '_get_variable_set', return_value=None):
        with patch.object(variable_set_module, '_create_variable_set', return_value=multi_project_response):
            # Run the module
            variable_set_module.run()
            
            # Verify exit_json was called with the right parameters
            variable_set_module.exit_json.assert_called_once()
            call_args = variable_set_module.exit_json.call_args[1]
            assert call_args['changed'] is True
            assert 'variable_set' in call_args
            assert len(call_args['variable_set']['project_ids']) == 2
            assert 'prj-def456' in call_args['variable_set']['project_ids']
            assert 'prj-ghi789' in call_args['variable_set']['project_ids']