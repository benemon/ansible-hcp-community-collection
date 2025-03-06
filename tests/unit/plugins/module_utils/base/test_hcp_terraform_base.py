import os
import pytest
import requests
import responses
from ansible_collections.benemon.hcp_community_collection.plugins.module_utils.base.hcp_terraform_base import HCPTerraformBase

@pytest.fixture
def mock_env():
    """Fixture to reset environment variables before and after tests."""
    original_env = os.environ.copy()
    yield
    os.environ.clear()
    os.environ.update(original_env)

def test_auth_with_provided_token():
    """Test authentication using a directly provided API token."""
    base = HCPTerraformBase(api_token="my-test-token")
    assert base.api_token == "my-test-token"
    assert base.base_url == "https://app.terraform.io/api/v2"

def test_auth_with_env_token(mock_env):
    """Test authentication using TF_API_TOKEN environment variable."""
    os.environ["TF_API_TOKEN"] = "env-test-token"
    base = HCPTerraformBase()
    assert base.api_token == "env-test-token"

def test_missing_api_token(mock_env):
    """Test error handling when no API token is provided."""
    os.environ.pop("TF_API_TOKEN", None)  # Ensure no token is set
    with pytest.raises(ValueError, match="HCP Terraform API token is required"):
        HCPTerraformBase()

def test_custom_base_url():
    """Test overriding the base URL for Terraform Enterprise."""
    base = HCPTerraformBase(api_token="test-token", base_url="https://tfe.example.com/api/v2")
    assert base.base_url == "https://tfe.example.com/api/v2"

def test_auth_headers():
    """Test that authentication headers are generated correctly."""
    base = HCPTerraformBase(api_token="test-token")
    headers = base._get_headers()
    assert headers == {
        "Authorization": "Bearer test-token",
        "Content-Type": "application/json"
    }

@responses.activate
def test_successful_get_request():
    """Test a successful GET request."""
    responses.add(
        responses.GET,
        "https://app.terraform.io/api/v2/test-endpoint",
        json={"data": "success"},
        status=200
    )
    
    base = HCPTerraformBase(api_token="test-token")
    response = base._request("GET", "/test-endpoint")
    
    assert response == {"data": "success"}

@responses.activate
def test_successful_post_request():
    """Test a successful POST request."""
    responses.add(
        responses.POST,
        "https://app.terraform.io/api/v2/test-endpoint",
        json={"result": "created"},
        status=201
    )
    
    base = HCPTerraformBase(api_token="test-token")
    response = base._request("POST", "/test-endpoint", data={"key": "value"})
    
    assert response == {"result": "created"}

@responses.activate
def test_unauthorized_request():
    """Test handling of a 401 Unauthorized response."""
    responses.add(
        responses.GET,
        "https://app.terraform.io/api/v2/test-endpoint",
        json={"errors": "Unauthorized"},
        status=401
    )
    
    base = HCPTerraformBase(api_token="test-token")
    
    with pytest.raises(ValueError, match="HTTP Error: 401"):
        base._request("GET", "/test-endpoint")

@responses.activate
def test_connection_error():
    """Test handling of a connection error."""
    responses.add(
        responses.GET,
        "https://app.terraform.io/api/v2/test-endpoint",
        body=requests.exceptions.ConnectionError()
    )
    
    base = HCPTerraformBase(api_token="test-token")
    
    with pytest.raises(ValueError, match="Error: Unable to connect to Terraform API"):
        base._request("GET", "/test-endpoint")

@responses.activate
def test_timeout_error():
    """Test handling of a request timeout."""
    responses.add(
        responses.GET,
        "https://app.terraform.io/api/v2/test-endpoint",
        body=requests.exceptions.Timeout()
    )
    
    base = HCPTerraformBase(api_token="test-token")
    
    with pytest.raises(ValueError, match="Error: Request to Terraform API timed out"):
        base._request("GET", "/test-endpoint")