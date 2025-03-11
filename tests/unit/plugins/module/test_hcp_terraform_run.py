from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest
from unittest.mock import patch, MagicMock, call

from ansible.errors import AnsibleError
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.benemon.hcp_community_collection.plugins.modules.hcp_terraform_run import TerraformRunModule

# Mock responses for run API
RUN_RESPONSE = {
    "data": {
        "id": "run-123456",
        "type": "runs",
        "attributes": {
            "status": "pending",
            "message": "Triggered by Ansible",
            "is-destroy": False,
            "auto-apply": True,
            "plan-only": False
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

RUN_COMPLETED_RESPONSE = {
    "data": {
        "id": "run-123456",
        "type": "runs",
        "attributes": {
            "status": "applied",
            "message": "Triggered by Ansible",
            "is-destroy": False,
            "auto-apply": True,
            "plan-only": False
        }
    }
}

# Fixture to create a TerraformRunModule instance with properly mocked dependencies
@pytest.fixture
def terraform_run_module():
    """Create a TerraformRunModule instance with mocked dependencies."""
    # Create a proper mock for AnsibleModule
    mock_ansible_module = MagicMock()
    mock_ansible_module.params = {
        'token': 'test-token',
        'hostname': 'https://app.terraform.io',
        'workspace_id': 'ws-abc123',
        'message': 'Triggered by Ansible',
        'is_destroy': False,
        'auto_apply': True,
        'plan_only': False,
        'variables': {},
        'targets': [],
        'wait': True,
        'timeout': 600
    }
    mock_ansible_module.check_mode = False
    mock_ansible_module.fail_json = MagicMock()
    mock_ansible_module.exit_json = MagicMock()
    
    # Patch the __init__ of TerraformRunModule to return our mock
    with patch.object(TerraformRunModule, '__init__', return_value=None):
        # Create the module
        module = TerraformRunModule()
        
        # Set up the module with our mock properties
        module.params = mock_ansible_module.params
        module.check_mode = False
        module.workspace_id = 'ws-abc123'
        module.message = 'Triggered by Ansible'
        module.is_destroy = False
        module.auto_apply = True
        module.plan_only = False
        module.variables = {}
        module.targets = []
        module.wait = True
        module.timeout = 600
        module.fail_json = mock_ansible_module.fail_json
        module.exit_json = mock_ansible_module.exit_json
        module.token = 'test-token'
        module.hostname = 'https://app.terraform.io'
        module.base_url = 'https://app.terraform.io/api/v2'
        
        # Mock the _request method
        module._request = MagicMock()
        
        yield module

# Test successful run execution
def test_successful_run_execution(terraform_run_module):
    # Mock the API responses
    terraform_run_module._request.side_effect = [
        RUN_RESPONSE,                # trigger_run response
        RUN_COMPLETED_RESPONSE       # wait_for_run_completion response
    ]
    
    # Run the module
    terraform_run_module.run()
    
    # Verify API calls
    assert terraform_run_module._request.call_count == 2
    # First call should be to create the run - check method and endpoint
    assert terraform_run_module._request.call_args_list[0][0][0] == "POST"
    assert terraform_run_module._request.call_args_list[0][0][1] == "/runs"
    
    # Second call should be to get run status
    assert terraform_run_module._request.call_args_list[1][0][0] == "GET"
    assert terraform_run_module._request.call_args_list[1][0][1] == "/runs/run-123456"
    
    # Verify exit_json was called with the right parameters
    terraform_run_module.exit_json.assert_called_once()
    call_args = terraform_run_module.exit_json.call_args[1]
    assert call_args['changed'] is True
    assert call_args['run_id'] == "run-123456"
    assert call_args['status'] == "applied"

# Test run with variables
def test_trigger_run_with_variables(terraform_run_module):
    # Set variables
    terraform_run_module.variables = {"region": "us-west-2", "instance_type": "t3.micro"}
    
    # Mock the API response
    terraform_run_module._request.return_value = RUN_RESPONSE
    terraform_run_module.wait = False
    
    # Create an expected payload
    expected_payload = {
        "data": {
            "attributes": {
                "message": "Triggered by Ansible",
                "is-destroy": False,
                "auto-apply": True,
                "plan-only": False,
                "variables": [
                    {"key": "region", "value": "us-west-2", "category": "terraform"},
                    {"key": "instance_type", "value": "t3.micro", "category": "terraform"}
                ]
            },
            "type": "runs",
            "relationships": {
                "workspace": {
                    "data": {"type": "workspaces", "id": "ws-abc123"}
                }
            }
        }
    }
    
    # Run the module
    terraform_run_module.run()
    
    # Verify API call was made with correct method and endpoint
    terraform_run_module._request.assert_called_once()
    args, kwargs = terraform_run_module._request.call_args
    assert args[0] == "POST"
    assert args[1] == "/runs"
    
    # Since the data might be passed as a positional arg or keyword arg,
    # we need to check both possibilities
    if len(args) > 2:
        # Data passed as positional argument
        payload = args[2]
    else:
        # Data passed as keyword argument
        payload = kwargs.get('data')
    
    # Check that the payload contains our variables
    assert payload is not None
    assert "data" in payload
    assert "attributes" in payload["data"]
    assert "variables" in payload["data"]["attributes"]
    
    # Extract the variables from the payload
    variables = payload["data"]["attributes"]["variables"]
    assert len(variables) == 2
    
    # Check that both variables are included with correct values
    var_dict = {var["key"]: var["value"] for var in variables}
    assert "region" in var_dict
    assert var_dict["region"] == "us-west-2"
    assert "instance_type" in var_dict
    assert var_dict["instance_type"] == "t3.micro"
    
    # Verify exit_json was called with the right parameters
    terraform_run_module.exit_json.assert_called_once()
    call_args = terraform_run_module.exit_json.call_args[1]
    assert call_args['changed'] is True
    assert call_args['run_id'] == "run-123456"

# Test run with no wait
def test_run_with_no_wait(terraform_run_module):
    # Set wait to False
    terraform_run_module.wait = False
    
    # Mock the API response
    terraform_run_module._request.return_value = RUN_RESPONSE
    
    # Run the module
    terraform_run_module.run()
    
    # Verify API call
    terraform_run_module._request.assert_called_once()
    
    # Verify exit_json was called with the right parameters
    terraform_run_module.exit_json.assert_called_once()
    call_args = terraform_run_module.exit_json.call_args[1]
    assert call_args['changed'] is True
    assert call_args['run_id'] == "run-123456"
    assert 'status' not in call_args

# Test wait for run completion
def test_wait_for_run_completion(terraform_run_module):
    # Mock the trigger_run and wait_for_run_completion methods
    with patch.object(terraform_run_module, 'trigger_run') as mock_trigger:
        mock_trigger.return_value = ("run-123456", RUN_RESPONSE)
        
        with patch.object(terraform_run_module, 'wait_for_run_completion') as mock_wait:
            mock_wait.return_value = ("applied", RUN_COMPLETED_RESPONSE)
            
            # Run the module
            terraform_run_module.run()
            
            # Verify methods were called
            mock_trigger.assert_called_once()
            mock_wait.assert_called_once_with("run-123456")
            
            # Verify exit_json was called with the right parameters
            terraform_run_module.exit_json.assert_called_once()
            call_args = terraform_run_module.exit_json.call_args[1]
            assert call_args['changed'] is True
            assert call_args['run_id'] == "run-123456"
            assert call_args['status'] == "applied"

# Test run timeout
def test_run_timeout(terraform_run_module):
    # Set up a side effect for fail_json
    def fail_json_side_effect(**kwargs):
        assert "Timeout" in kwargs.get('msg', '')
        raise Exception(kwargs.get('msg', 'Timeout'))

    terraform_run_module.fail_json.side_effect = fail_json_side_effect
    
    # Mock the trigger_run method
    with patch.object(terraform_run_module, 'trigger_run') as mock_trigger:
        mock_trigger.return_value = ("run-123456", RUN_RESPONSE)
        
        # Mock the wait_for_run_completion method to simulate timeout
        with patch.object(terraform_run_module, 'wait_for_run_completion') as mock_wait:
            mock_wait.side_effect = Exception("Timeout waiting for Terraform run")
            
            # Run the module and expect an exception
            with pytest.raises(Exception) as excinfo:
                terraform_run_module.run()
            
            # Verify the exception message
            assert "Timeout" in str(excinfo.value) or "Error" in str(excinfo.value)
            
            # Verify methods were called
            mock_trigger.assert_called_once()
            mock_wait.assert_called_once_with("run-123456")

# Test API failure on run creation
def test_api_failure_on_run_creation(terraform_run_module):
    # Set up a side effect for fail_json
    def fail_json_side_effect(**kwargs):
        assert "Error" in kwargs.get('msg', '')
        raise Exception(kwargs.get('msg', 'API Error'))
    
    terraform_run_module.fail_json.side_effect = fail_json_side_effect
    
    # Mock the trigger_run method to raise an exception
    with patch.object(terraform_run_module, 'trigger_run') as mock_trigger:
        mock_trigger.side_effect = Exception("API Error")
        
        # Run the module and expect an exception
        with pytest.raises(Exception) as excinfo:
            terraform_run_module.run()
        
        # Verify the exception message
        assert "API Error" in str(excinfo.value) or "Error" in str(excinfo.value)
        
        # Verify the trigger_run method was called
        mock_trigger.assert_called_once()