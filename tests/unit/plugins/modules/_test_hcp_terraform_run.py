from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest
import json
from unittest.mock import patch, MagicMock

from ansible_collections.benemon.hcp_community_collection.plugins.modules.hcp_terraform_run import TerraformRunModule

@pytest.fixture
def mock_module():
    """Mock AnsibleModule instance to simulate Ansible behavior."""
    mock_module = MagicMock()
    mock_module.params = {
        "token": "test_token",
        "workspace_id": "ws-12345",
        "base_url": "https://app.terraform.io/api/v2",
        "message": "Triggered by Ansible",
        "is_destroy": False,
        "auto_apply": False,
        "plan_only": False,
        "variables": {},
        "targets": [],
        "wait": True,
        "timeout": 600
    }
    mock_module.fail_json = MagicMock(side_effect=SystemExit)
    mock_module.exit_json = MagicMock()
    return mock_module

@pytest.fixture
def terraform_run_module(mock_module):
    """Create a TerraformRunModule instance with mocked dependencies."""
    with patch.object(TerraformRunModule, '_request') as mock_request:
        module = TerraformRunModule(mock_module)
        module._request = mock_request
        yield module

def test_successful_run_execution(terraform_run_module, mock_module):
    """Test successful execution of a Terraform run."""
    # Set up the mock responses
    terraform_run_module._request.return_value = {
        "data": {
            "id": "run-12345",
            "attributes": {"status": "pending"}
        }
    }

    # Call the run method
    terraform_run_module.run()

    # Assertions
    mock_module.exit_json.assert_called_once_with(
        changed=True,
        run_id="run-12345",
        api_response={"data": {"id": "run-12345", "attributes": {"status": "pending"}}}
    )

def test_api_failure_on_run_creation(terraform_run_module, mock_module):
    """Test failure when the Terraform API rejects the request."""
    # Set up the mock to raise an exception
    terraform_run_module._request.side_effect = Exception("API Error: Unauthorized")

    # Expect the run method to call fail_json which raises SystemExit
    with pytest.raises(SystemExit):
        terraform_run_module.run()

    # Assertions
    mock_module.fail_json.assert_called_once_with(msg="API Error: Unauthorized")

def test_wait_for_run_completion(terraform_run_module, mock_module):
    """Test waiting for a Terraform run to complete."""
    # Configure the module to wait
    mock_module.params["wait"] = True

    # Configure the mock to return different responses in sequence
    terraform_run_module._request.side_effect = [
        {"data": {"id": "run-12345", "attributes": {"status": "pending"}}},  # trigger_run response
        {"data": {"id": "run-12345", "attributes": {"status": "applying"}}},  # first status check
        {"data": {"id": "run-12345", "attributes": {"status": "applied"}}}   # final status
    ]

    # Call the run method
    terraform_run_module.run()

    # Assertions
    mock_module.exit_json.assert_called_once_with(
        changed=True,
        run_id="run-12345",
        status="applied",
        api_response={"data": {"id": "run-12345", "attributes": {"status": "applied"}}}
    )

def test_run_timeout(terraform_run_module, mock_module):
    """Test Terraform run timeout scenario."""
    # Configure the module with a short timeout
    mock_module.params["timeout"] = 5

    # Mock time.time() to simulate passage of time
    with patch('time.time') as mock_time, patch('time.sleep') as mock_sleep:
        # First call is start time, second call is check time (after timeout)
        mock_time.side_effect = [100, 106]  # 6 seconds elapsed (> timeout of 5)
        
        # Run creation response
        terraform_run_module._request.side_effect = [
            {"data": {"id": "run-12345", "attributes": {"status": "pending"}}},  # trigger_run response
            {"data": {"id": "run-12345", "attributes": {"status": "pending"}}}   # status still pending
        ]

        # Call should timeout
        with pytest.raises(SystemExit):
            terraform_run_module.run()

        # Verify fail_json was called with timeout message
        mock_module.fail_json.assert_called_once_with(
            msg="Timeout waiting for Terraform run run-12345 to complete.",
            api_response={"data": {"id": "run-12345", "attributes": {"status": "pending"}}}
        )

def test_trigger_run_with_variables(terraform_run_module):
    """Test triggering a run with variables."""
    # Configure variables
    terraform_run_module.variables = {"env": "prod", "region": "us-west-2"}
    
    # Configure mock response
    terraform_run_module._request.return_value = {
        "data": {"id": "run-12345", "attributes": {"status": "pending"}}
    }
    
    # Call the method
    run_id, response = terraform_run_module.trigger_run()
    
    # Verify the request was made with the correct payload
    expected_payload = {
        "data": {
            "attributes": {
                "message": terraform_run_module.message,
                "is_destroy": terraform_run_module.is_destroy,
                "auto_apply": terraform_run_module.auto_apply,
                "plan_only": terraform_run_module.plan_only,
                "variables": [
                    {"key": "env", "value": "prod", "category": "terraform"},
                    {"key": "region", "value": "us-west-2", "category": "terraform"}
                ]
            },
            "type": "runs",
            "relationships": {
                "workspace": {
                    "data": {"type": "workspaces", "id": terraform_run_module.workspace_id}
                }
            }
        }
    }
    
    # Assertions
    terraform_run_module._request.assert_called_once_with("POST", "/runs", data=pytest.approx(expected_payload))
    assert run_id == "run-12345"
    assert response == {"data": {"id": "run-12345", "attributes": {"status": "pending"}}}

def test_run_with_no_wait(terraform_run_module, mock_module):
    """Test running without waiting for completion."""
    # Configure the module to not wait
    mock_module.params["wait"] = False
    
    # Set up the mock response
    terraform_run_module._request.return_value = {
        "data": {"id": "run-12345", "attributes": {"status": "pending"}}
    }
    
    # Call the run method
    terraform_run_module.run()
    
    # Assertions
    mock_module.exit_json.assert_called_once_with(
        changed=True,
        run_id="run-12345",
        api_response={"data": {"id": "run-12345", "attributes": {"status": "pending"}}}
    )
