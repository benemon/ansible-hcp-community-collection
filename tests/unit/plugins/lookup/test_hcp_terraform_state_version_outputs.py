from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest
from unittest.mock import patch, MagicMock

from ansible.errors import AnsibleError
from ansible.plugins.loader import lookup_loader
from ansible_collections.benemon.hcp_community_collection.plugins.lookup.hcp_terraform_state_version_outputs import LookupModule

# Mock response for state version outputs API
STATE_VERSION_OUTPUTS_RESPONSE = {
    "data": [
        {
            "id": "wsout-123456",
            "type": "state-version-outputs",
            "attributes": {
                "name": "vpc_id",
                "sensitive": False,
                "type": "string",
                "value": "vpc-12345",
                "detailed-type": "string"
            },
            "links": {
                "self": "/api/v2/state-version-outputs/wsout-123456"
            }
        },
        {
            "id": "wsout-654321",
            "type": "state-version-outputs",
            "attributes": {
                "name": "subnet_ids",
                "sensitive": False,
                "type": "array",
                "value": ["subnet-1", "subnet-2"],
                "detailed-type": ["tuple", ["string", "string"]]
            },
            "links": {
                "self": "/api/v2/state-version-outputs/wsout-654321"
            }
        },
        {
            "id": "wsout-789012",
            "type": "state-version-outputs",
            "attributes": {
                "name": "db_password",
                "sensitive": True,
                "type": "string",
                "value": None,
                "detailed-type": "string"
            },
            "links": {
                "self": "/api/v2/state-version-outputs/wsout-789012"
            }
        }
    ],
    "links": {
        "self": "https://app.terraform.io/api/v2/state-versions/sv-123456/outputs?page[number]=1&page[size]=20",
        "first": "https://app.terraform.io/api/v2/state-versions/sv-123456/outputs?page[number]=1&page[size]=20",
        "prev": None,
        "next": None,
        "last": "https://app.terraform.io/api/v2/state-versions/sv-123456/outputs?page[number]=1&page[size]=20"
    },
    "meta": {
        "pagination": {
            "current-page": 1,
            "prev-page": None,
            "next-page": None,
            "total-pages": 1,
            "total-count": 3
        }
    }
}

SINGLE_OUTPUT_RESPONSE = {
    "data": {
        "id": "wsout-123456",
        "type": "state-version-outputs",
        "attributes": {
            "name": "vpc_id",
            "sensitive": False,
            "type": "string",
            "value": "vpc-12345",
            "detailed-type": "string"
        },
        "links": {
            "self": "/api/v2/state-version-outputs/wsout-123456"
        }
    }
}

# Fixture to create a LookupModule instance
@pytest.fixture
def lookup_instance():
    lookup = LookupModule()
    lookup.base_url = "https://app.terraform.io/api/v2"
    return lookup

# Fixture to mock the _make_request method
@pytest.fixture
def mock_make_request():
    with patch.object(LookupModule, '_make_request') as mock:
        mock.return_value = STATE_VERSION_OUTPUTS_RESPONSE
        yield mock

# Fixture to mock the _get_auth_token method
@pytest.fixture
def mock_auth_token():
    with patch.object(LookupModule, '_get_auth_token') as mock:
        mock.return_value = "mock-token"
        yield mock

# Fixture to mock the _get_hostname method
@pytest.fixture
def mock_hostname():
    with patch.object(LookupModule, '_get_hostname') as mock:
        mock.return_value = "https://app.terraform.io/api/v2"
        yield mock

# Test getting all outputs by state version ID
def test_get_outputs_by_state_version_id(lookup_instance, mock_make_request, mock_auth_token, mock_hostname):
    variables = {"state_version_id": "sv-123456"}
    result = lookup_instance.run([], variables)
    
    assert isinstance(result, list)
    assert len(result) == 1
    assert isinstance(result[0], dict)
    assert "vpc_id" in result[0]
    assert "subnet_ids" in result[0]
    assert result[0]["vpc_id"] == "vpc-12345"
    assert result[0]["subnet_ids"] == ["subnet-1", "subnet-2"]
    
    mock_make_request.assert_called_once()

# Test getting all outputs by workspace ID
def test_get_outputs_by_workspace_id(lookup_instance, mock_auth_token, mock_hostname):
    with patch.object(lookup_instance, '_get_current_state_version_outputs') as mock_get_outputs:
        mock_get_outputs.return_value = STATE_VERSION_OUTPUTS_RESPONSE
        
        variables = {"workspace_id": "ws-12345"}
        result = lookup_instance.run([], variables)
        
        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], dict)
        assert "vpc_id" in result[0]
        assert "subnet_ids" in result[0]
        
        mock_get_outputs.assert_called_once_with("ws-12345", variables)

# Test getting all outputs by workspace name
def test_get_outputs_by_workspace_name(lookup_instance, mock_auth_token, mock_hostname):
    with patch.object(lookup_instance, '_get_workspace_id') as mock_get_id:
        mock_get_id.return_value = "ws-12345"
        
        with patch.object(lookup_instance, '_get_current_state_version_outputs') as mock_get_outputs:
            mock_get_outputs.return_value = STATE_VERSION_OUTPUTS_RESPONSE
            
            variables = {"organization": "my-org", "workspace_name": "my-workspace"}
            result = lookup_instance.run([], variables)
            
            assert isinstance(result, list)
            assert len(result) == 1
            assert isinstance(result[0], dict)
            assert "vpc_id" in result[0]
            assert "subnet_ids" in result[0]
            
            mock_get_id.assert_called_once_with("my-org", "my-workspace")
            mock_get_outputs.assert_called_once_with("ws-12345", variables)

# Test getting a specific output by name
def test_get_output_by_name(lookup_instance, mock_make_request, mock_auth_token, mock_hostname):
    variables = {"state_version_id": "sv-123456", "output_name": "vpc_id"}
    result = lookup_instance.run([], variables)
    
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0] == "vpc-12345"
    
    mock_make_request.assert_called_once()

# Test getting a specific output by ID
def test_get_output_by_id(lookup_instance, mock_auth_token, mock_hostname):
    with patch.object(lookup_instance, '_get_output_by_id') as mock_get_output:
        mock_get_output.return_value = SINGLE_OUTPUT_RESPONSE
        
        variables = {"output_id": "wsout-123456"}
        result = lookup_instance.run([], variables)
        
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0] == "vpc-12345"
        
        mock_get_output.assert_called_once_with("wsout-123456", variables)

# Test getting raw API response
def test_get_raw_output(lookup_instance, mock_make_request, mock_auth_token, mock_hostname):
    variables = {"state_version_id": "sv-123456", "raw_output": True}
    result = lookup_instance.run([], variables)
    
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0] == STATE_VERSION_OUTPUTS_RESPONSE
    
    mock_make_request.assert_called_once()

# Test waiting for state version processing
def test_wait_for_processing(lookup_instance, mock_auth_token, mock_hostname):
    with patch.object(lookup_instance, '_get_outputs_by_state_version') as mock_get_outputs:
        mock_get_outputs.return_value = STATE_VERSION_OUTPUTS_RESPONSE
        
        with patch.object(lookup_instance, '_wait_for_state_version_if_needed') as mock_wait:
            variables = {"state_version_id": "sv-123456", "wait_for_processing": True}
            result = lookup_instance.run([], variables)
            
            assert isinstance(result, list)
            assert len(result) == 1
            assert isinstance(result[0], dict)
            assert "vpc_id" in result[0]
            
            # Update to expect all three parameters, including the variables dictionary
            mock_wait.assert_called_once_with("sv-123456", 120, variables)

# Test error handling when output name not found
def test_output_name_not_found(lookup_instance, mock_make_request, mock_auth_token, mock_hostname):
    variables = {"state_version_id": "sv-123456", "output_name": "non_existent_output"}
    
    with pytest.raises(AnsibleError) as excinfo:
        lookup_instance.run([], variables)
    
    assert "Output 'non_existent_output' not found" in str(excinfo.value)

# Test error handling when required parameters are missing
def test_missing_parameters(lookup_instance, mock_auth_token, mock_hostname):
    with pytest.raises(AnsibleError) as excinfo:
        variables = {}
        lookup_instance.run([], variables)
    
    assert "must be provided" in str(excinfo.value)

# Test error handling when API request fails
def test_api_error(lookup_instance, mock_auth_token, mock_hostname):
    with patch.object(lookup_instance, '_get_output_by_id') as mock_get:
        mock_get.side_effect = Exception("API Error")
        
        with pytest.raises(AnsibleError) as excinfo:
            variables = {"output_id": "wsout-123456"}
            lookup_instance.run([], variables)
        
        assert "Error retrieving state version outputs" in str(excinfo.value)

# Ensure lookup plugin is properly registered and can be loaded
def test_plugin_registered():
    lookup = lookup_loader.get("benemon.hcp_community_collection.hcp_terraform_state_version_outputs")
    assert lookup is not None