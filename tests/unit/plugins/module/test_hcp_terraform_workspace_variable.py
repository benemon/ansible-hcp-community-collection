from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest
from unittest.mock import patch, MagicMock

from ansible_collections.benemon.hcp_community_collection.plugins.modules.hcp_terraform_workspace_variable import TerraformWorkspaceVariableModule
from ansible.module_utils.basic import AnsibleModule

# Mock responses for variable API
VARIABLE_CREATE_RESPONSE = {
    "data": {
        "id": "var-123456",
        "type": "vars",
        "attributes": {
            "key": "test_key",
            "value": "test_value",
            "description": "Test description",
            "category": "terraform",
            "hcl": False,
            "sensitive": False
        },
        "relationships": {
            "workspace": {
                "data": {
                    "id": "ws-abc123",
                    "type": "workspaces"
                }
            }
        }
    }
}

VARIABLE_SENSITIVE_RESPONSE = {
    "data": {
        "id": "var-789012",
        "type": "vars",
        "attributes": {
            "key": "sensitive_key",
            "description": "Sensitive variable",
            "category": "env",
            "hcl": False,
            "sensitive": True
        },
        "relationships": {
            "workspace": {
                "data": {
                    "id": "ws-abc123",
                    "type": "workspaces"
                }
            }
        }
    }
}

WORKSPACE_VARIABLES_RESPONSE = {
    "data": [
        {
            "id": "var-123456",
            "type": "vars",
            "attributes": {
                "key": "test_key",
                "value": "test_value",
                "description": "Test description",
                "category": "terraform",
                "hcl": False,
                "sensitive": False
            }
        },
        {
            "id": "var-789012",
            "type": "vars",
            "attributes": {
                "key": "sensitive_key",
                "description": "Sensitive variable",
                "category": "env",
                "hcl": False,
                "sensitive": True
            }
        }
    ]
}

# Mock AnsibleModule for testing
class MockAnsibleModule:
    def __init__(self, **kwargs):
        self.params = kwargs.get('params', {})
        self.check_mode = kwargs.get('check_mode', False)
        self.no_log_values = set()

    def fail_json(self, **kwargs):
        self.exit_args = kwargs
        self.exit_code = 1
        raise Exception(kwargs.get('msg', 'Module failed'))

    def exit_json(self, **kwargs):
        self.exit_args = kwargs
        self.exit_code = 0

# Fixture to create a mock TerraformVariableModule instance
@pytest.fixture
def variable_module():
    # Create a proper mock for AnsibleModule
    mock_ansible_module = MagicMock()
    mock_ansible_module.params = {
        'token': 'test-token',
        'hostname': 'https://app.terraform.io',
        'workspace_id': 'ws-abc123',
        'key': 'test_key',
        'value': 'test_value',
        'description': 'Test description',
        'category': 'terraform',
        'hcl': False,
        'sensitive': False,
        'state': 'present'
    }
    mock_ansible_module.check_mode = False
    mock_ansible_module.fail_json = MagicMock()
    mock_ansible_module.exit_json = MagicMock()
    
    # Patch the __init__ of AnsibleModule to return our mock
    with patch.object(AnsibleModule, '__init__', return_value=None):
        with patch.object(TerraformWorkspaceVariableModule, '__init__', return_value=None) as mock_init:
            # Create the module
            module = TerraformWorkspaceVariableModule()
            
            # Set up the module with our mock properties
            module.params = mock_ansible_module.params
            module.check_mode = False
            module.workspace_id = 'ws-abc123'
            module.key = 'test_key'
            module.value = 'test_value'
            module.state = 'present'
            module.sensitive = False
            module.no_log_values = set()
            module.fail_json = mock_ansible_module.fail_json
            module.exit_json = mock_ansible_module.exit_json
            module.token = 'test-token'
            module.hostname = 'https://app.terraform.io'
            
            yield module

# Test variable creation
def test_create_variable(variable_module):
    # Mock the API request
    with patch.object(variable_module, '_get_variable', return_value=None):
        with patch.object(variable_module, '_create_variable', return_value=VARIABLE_CREATE_RESPONSE):
            # Run the module
            variable_module.run()
            
            # Verify exit_json was called with the right parameters
            variable_module.exit_json.assert_called_once()
            call_args = variable_module.exit_json.call_args[1]
            assert call_args['changed'] is True
            assert 'variable' in call_args
            assert call_args['variable']['key'] == 'test_key'
            assert call_args['variable']['value'] == 'test_value'
            assert call_args['msg'] == "Variable 'test_key' created successfully"

# Test variable update
def test_update_variable(variable_module):
    # Current variable in API
    current_variable = {
        "id": "var-123456",
        "attributes": {
            "key": "test_key",
            "value": "old_value",
            "description": "Old description",
            "category": "terraform",
            "hcl": False,
            "sensitive": False
        }
    }
    
    # Mock the API request
    with patch.object(variable_module, '_get_variable', return_value=current_variable):
        with patch.object(variable_module, '_update_variable', return_value=VARIABLE_CREATE_RESPONSE):
            # Run the module
            variable_module.run()
            
            # Verify exit_json was called with the right parameters
            variable_module.exit_json.assert_called_once()
            call_args = variable_module.exit_json.call_args[1]
            assert call_args['changed'] is True
            assert 'variable' in call_args
            assert call_args['variable']['key'] == 'test_key'
            assert call_args['msg'] == "Variable 'test_key' updated successfully"

# Test no update needed
def test_no_update_needed(variable_module):
    # Current variable in API matches what we want to set
    current_variable = {
        "id": "var-123456",
        "attributes": {
            "key": "test_key",
            "value": "test_value",
            "description": "Test description",
            "category": "terraform",
            "hcl": False,
            "sensitive": False
        }
    }
    
    # Mock the API request
    with patch.object(variable_module, '_get_variable', return_value=current_variable):
        # Run the module
        variable_module.run()
        
        # Verify exit_json was called with the right parameters
        variable_module.exit_json.assert_called_once()
        call_args = variable_module.exit_json.call_args[1]
        assert call_args['changed'] is False
        assert 'variable' in call_args
        assert call_args['msg'] == "Variable 'test_key' already up-to-date"

# Test variable deletion
def test_delete_variable(variable_module):
    # Set state to absent
    variable_module.state = 'absent'
    
    # Current variable in API
    current_variable = {
        "id": "var-123456",
        "attributes": {
            "key": "test_key",
            "value": "test_value",
            "description": "Test description",
            "category": "terraform",
            "hcl": False,
            "sensitive": False
        }
    }
    
    # Mock the API request
    with patch.object(variable_module, '_get_variable', return_value=current_variable):
        with patch.object(variable_module, '_delete_variable', return_value={"changed": True, "msg": "Variable 'test_key' deleted successfully"}):
            # Run the module
            variable_module.run()
            
            # Verify exit_json was called with the right parameters
            variable_module.exit_json.assert_called_once()
            call_args = variable_module.exit_json.call_args[1]
            assert call_args['changed'] is True
            assert call_args['msg'] == "Variable 'test_key' deleted successfully"

# Test sensitive variable handling
def test_sensitive_variable(variable_module):
    # Set sensitive to True
    variable_module.sensitive = True
    variable_module.params['sensitive'] = True
    
    # Mock the API request
    with patch.object(variable_module, '_get_variable', return_value=None):
        with patch.object(variable_module, '_create_variable', return_value=VARIABLE_SENSITIVE_RESPONSE):
            # Run the module
            variable_module.run()
            
            # Verify exit_json was called with the right parameters
            variable_module.exit_json.assert_called_once()
            call_args = variable_module.exit_json.call_args[1]
            assert call_args['changed'] is True
            assert 'variable' in call_args
            assert 'value' not in call_args['variable']
            assert call_args['variable']['sensitive'] is True

# Test check mode
def test_check_mode(variable_module):
    # Set check mode to True
    variable_module.check_mode = True
    
    # Mock the API request
    with patch.object(variable_module, '_get_variable', return_value=None):
        # Run the module
        variable_module.run()
        
        # Verify exit_json was called with the right parameters
        variable_module.exit_json.assert_called_once()
        call_args = variable_module.exit_json.call_args[1]
        assert call_args['changed'] is True
        assert call_args['msg'] == "Would create variable 'test_key'"

# Test error handling
def test_error_handling(variable_module):
    # Define a custom function that would be called by run() to handle errors properly
    def fail_json_side_effect(**kwargs):
        assert "Error managing variable: API Error" in kwargs.get('msg', '')
        raise Exception(kwargs.get('msg', 'API Error'))
    
    # Set up the fail_json mock to have a side effect
    variable_module.fail_json.side_effect = fail_json_side_effect
    
    # Mock the API request to raise an exception
    with patch.object(variable_module, '_get_variable', side_effect=Exception("API Error")):
        # Run the module
        with pytest.raises(Exception) as excinfo:
            variable_module.run()
        
        # Verify the error message contains our API error
        assert "API Error" in str(excinfo.value)