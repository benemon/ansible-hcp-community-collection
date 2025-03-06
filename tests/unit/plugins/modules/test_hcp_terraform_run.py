import pytest
import json
from unittest.mock import patch, MagicMock
from ansible.errors import AnsibleError
from ansible_collections.benemon.hcp_community_collection.plugins.modules.hcp_terraform_run import main

@pytest.fixture
def mock_module():
    """Mock AnsibleModule instance to simulate Ansible behavior."""
    with patch("ansible.module_utils.basic.AnsibleModule") as mock_module:
        yield mock_module

@pytest.fixture
def mock_requests():
    """Mock the _request method from HCPTerraformBase to simulate API calls."""
    with patch("ansible_collections.benemon.hcp_community_collection.plugins.module_utils.base.HCPTerraformBase._request") as mock_request:
        yield mock_request

def test_successful_run_execution(mock_module, mock_requests):
    """Test successful execution of a Terraform run."""
    mock_module_instance = mock_module.return_value
    mock_module_instance.params = {
        "token": "test_token",
        "workspace_id": "ws-12345",
        "plan_only": False,
        "wait": True
    }

    mock_requests.return_value = {
        "data": {
            "id": "run-12345",
            "attributes": {"status": "pending"}
        }
    }

    main()

    mock_module_instance.exit_json.assert_called_once_with(
        changed=True,
        run_id="run-12345",
        api_response={"data": {"id": "run-12345", "attributes": {"status": "pending"}}}
    )

def test_api_failure_on_run_creation(mock_module, mock_requests):
    """Test failure when the Terraform API rejects the request."""
    mock_module_instance = mock_module.return_value
    mock_module_instance.params = {
        "token": "test_token",
        "workspace_id": "ws-12345",
        "plan_only": False,
        "wait": True
    }

    mock_requests.side_effect = AnsibleError("API Error: Unauthorized")

    with pytest.raises(SystemExit):
        main()

    mock_module_instance.fail_json.assert_called_once_with(msg="API Error: Unauthorized")

def test_missing_token_parameter(mock_module):
    """Test missing token parameter, ensuring validation triggers."""
    mock_module_instance = mock_module.return_value
    mock_module_instance.params = {
        "workspace_id": "ws-12345",
        "plan_only": False,
        "wait": True
    }

    with pytest.raises(SystemExit):
        main()

    mock_module_instance.fail_json.assert_called_once_with(msg="Missing required parameter: token")

def test_wait_for_run_completion(mock_module, mock_requests):
    """Test waiting for a Terraform run to complete."""
    mock_module_instance = mock_module.return_value
    mock_module_instance.params = {
        "token": "test_token",
        "workspace_id": "ws-12345",
        "plan_only": False,
        "wait": True
    }

    # Simulated responses: Start → In Progress → Applied
    mock_requests.side_effect = [
        {"data": {"id": "run-12345", "attributes": {"status": "pending"}}},
        {"data": {"id": "run-12345", "attributes": {"status": "applying"}}},
        {"data": {"id": "run-12345", "attributes": {"status": "applied"}}},
    ]

    main()

    mock_module_instance.exit_json.assert_called_once_with(
        changed=True,
        run_id="run-12345",
        status="applied",
        api_response={"data": {"id": "run-12345", "attributes": {"status": "applied"}}}
    )

def test_run_timeout(mock_module, mock_requests):
    """Test Terraform run timeout scenario."""
    mock_module_instance = mock_module.return_value
    mock_module_instance.params = {
        "token": "test_token",
        "workspace_id": "ws-12345",
        "plan_only": False,
        "wait": True,
        "timeout": 5
    }

    # Simulated API response: Run remains "pending"
    mock_requests.side_effect = [
        {"data": {"id": "run-12345", "attributes": {"status": "pending"}}}
    ] * 10  # Repeated responses to simulate timeout

    with pytest.raises(SystemExit):
        main()

    mock_module_instance.fail_json.assert_called_once_with(
        msg="Timeout waiting for Terraform run run-12345 to complete."
    )

def test_api_rate_limit_with_retries(mock_module, mock_requests):
    """Test retry logic when API rate limit (429) is hit."""
    mock_module_instance = mock_module.return_value
    mock_module_instance.params = {
        "token": "test_token",
        "workspace_id": "ws-12345",
        "plan_only": False,
        "wait": True
    }

    # First two requests fail due to 429, third succeeds
    mock_requests.side_effect = [
        AnsibleError("API rate limit exceeded"),
        AnsibleError("API rate limit exceeded"),
        {"data": {"id": "run-12345", "attributes": {"status": "pending"}}}
    ]

    main()

    mock_module_instance.exit_json.assert_called_once_with(
        changed=True,
        run_id="run-12345",
        api_response={"data": {"id": "run-12345", "attributes": {"status": "pending"}}}
    )

def test_api_service_unavailable_with_retries(mock_module, mock_requests):
    """Test retry logic when API returns 503 Service Unavailable."""
    mock_module_instance = mock_module.return_value
    mock_module_instance.params = {
        "token": "test_token",
        "workspace_id": "ws-12345",
        "plan_only": False,
        "wait": True
    }

    # First request fails with 503, second succeeds
    mock_requests.side_effect = [
        AnsibleError("Service unavailable"),
        {"data": {"id": "run-12345", "attributes": {"status": "pending"}}}
    ]

    main()

    mock_module_instance.exit_json.assert_called_once_with(
        changed=True,
        run_id="run-12345",
        api_response={"data": {"id": "run-12345", "attributes": {"status": "pending"}}}
    )
