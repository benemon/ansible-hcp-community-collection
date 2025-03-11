from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest
from unittest.mock import patch, MagicMock

from ansible.errors import AnsibleError
from ansible.plugins.loader import lookup_loader
from ansible_collections.benemon.hcp_community_collection.plugins.lookup.hcp_terraform_agent_pools import LookupModule

# Mock response for agent pools API
AGENT_POOLS_RESPONSE = {
    "data": [
        {
            "id": "apool-yoGUFz5zcRMMz53i",
            "type": "agent-pools",
            "attributes": {
                "name": "example-pool",
                "created-at": "2020-08-05T18:10:26.964Z",
                "organization-scoped": False,
                "agent-count": 3
            },
            "relationships": {
                "agents": {
                    "links": {
                        "related": "/api/v2/agent-pools/apool-yoGUFz5zcRMMz53i/agents"
                    }
                },
                "authentication-tokens": {
                    "links": {
                        "related": "/api/v2/agent-pools/apool-yoGUFz5zcRMMz53i/authentication-tokens"
                    }
                },
                "workspaces": {
                    "data": [
                        {
                            "id": "ws-9EEkcEQSA3XgWyGe",
                            "type": "workspaces"
                        }
                    ]
                },
                "allowed-workspaces": {
                    "data": [
                        {
                            "id": "ws-x9taqV23mxrGcDrn",
                            "type": "workspaces"
                        }
                    ]
                }
            },
            "links": {
                "self": "/api/v2/agent-pools/apool-yoGUFz5zcRMMz53i"
            }
        },
        {
            "id": "apool-2BdvTNUrBmQKdcqr",
            "type": "agent-pools",
            "attributes": {
                "name": "production-pool",
                "created-at": "2020-09-10T14:20:30.123Z",
                "organization-scoped": True,
                "agent-count": 5
            },
            "relationships": {
                "agents": {
                    "links": {
                        "related": "/api/v2/agent-pools/apool-2BdvTNUrBmQKdcqr/agents"
                    }
                },
                "authentication-tokens": {
                    "links": {
                        "related": "/api/v2/agent-pools/apool-2BdvTNUrBmQKdcqr/authentication-tokens"
                    }
                },
                "workspaces": {
                    "data": []
                },
                "allowed-workspaces": {
                    "data": []
                }
            },
            "links": {
                "self": "/api/v2/agent-pools/apool-2BdvTNUrBmQKdcqr"
            }
        }
    ],
    "links": {
        "self": "https://app.terraform.io/api/v2/organizations/my-organization/agent-pools?page[number]=1&page[size]=20",
        "first": "https://app.terraform.io/api/v2/organizations/my-organization/agent-pools?page[number]=1&page[size]=20",
        "prev": None,
        "next": None,
        "last": "https://app.terraform.io/api/v2/organizations/my-organization/agent-pools?page[number]=1&page[size]=20"
    },
    "meta": {
        "pagination": {
            "current-page": 1,
            "prev-page": None,
            "next-page": None,
            "total-pages": 1,
            "total-count": 2
        },
        "status-counts": {
            "total": 2,
            "matching": 2
        }
    }
}

# Fixture to create a LookupModule instance
@pytest.fixture
def lookup_instance():
    lookup = LookupModule()
    lookup.base_url = "https://app.terraform.io/api/v2"
    return lookup

# Fixture to mock the _handle_pagination method
@pytest.fixture
def mock_handle_pagination():
    with patch.object(LookupModule, '_handle_pagination') as mock:
        mock.return_value = AGENT_POOLS_RESPONSE
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

# Test retrieving all agent pools for an organization
def test_get_all_agent_pools(lookup_instance, mock_handle_pagination, mock_auth_token, mock_hostname):
    variables = {"organization": "my-organization"}
    result = lookup_instance.run([], variables)
    
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0] == AGENT_POOLS_RESPONSE
    
    # Verify the correct endpoint and parameters were used
    mock_handle_pagination.assert_called_once_with(
        "organizations/my-organization/agent-pools", 
        variables, 
        {}
    )

# Test with server-side filtering
def test_get_agent_pools_with_search_query(lookup_instance, mock_handle_pagination, mock_auth_token, mock_hostname):
    variables = {"organization": "my-organization", "q": "production"}
    result = lookup_instance.run([], variables)
    
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0] == AGENT_POOLS_RESPONSE
    
    # Verify the search query was passed
    mock_handle_pagination.assert_called_once_with(
        "organizations/my-organization/agent-pools", 
        variables, 
        {"q": "production"}
    )

# Test with sorting
def test_get_agent_pools_with_sorting(lookup_instance, mock_handle_pagination, mock_auth_token, mock_hostname):
    variables = {"organization": "my-organization", "sort": "-name"}
    result = lookup_instance.run([], variables)
    
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0] == AGENT_POOLS_RESPONSE
    
    # Verify the sort parameter was passed
    mock_handle_pagination.assert_called_once_with(
        "organizations/my-organization/agent-pools", 
        variables, 
        {"sort": "-name"}
    )

# Test filtering by workspace
def test_get_agent_pools_for_workspace(lookup_instance, mock_handle_pagination, mock_auth_token, mock_hostname):
    variables = {"organization": "my-organization", "allowed_workspace_name": "my-workspace"}
    result = lookup_instance.run([], variables)
    
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0] == AGENT_POOLS_RESPONSE
    
    # Verify the workspace filter was passed
    mock_handle_pagination.assert_called_once_with(
        "organizations/my-organization/agent-pools", 
        variables, 
        {"filter[allowed_workspaces][name]": "my-workspace"}
    )

# Test client-side name filtering
def test_get_agent_pools_with_name_filter(lookup_instance, mock_handle_pagination, mock_auth_token, mock_hostname):
    variables = {"organization": "my-organization", "name": "example-pool"}
    result = lookup_instance.run([], variables)
    
    assert isinstance(result, list)
    assert len(result) == 1
    
    # Result should contain only the matching pool after client-side filtering
    filtered_data = result[0]["data"]
    assert len(filtered_data) == 1
    assert filtered_data[0]["attributes"]["name"] == "example-pool"
    
    # The original request doesn't include name filtering (that's done client-side)
    mock_handle_pagination.assert_called_once_with(
        "organizations/my-organization/agent-pools", 
        variables, 
        {}
    )

# Test missing organization parameter
def test_missing_organization(lookup_instance, mock_auth_token, mock_hostname):
    with pytest.raises(AnsibleError) as excinfo:
        variables = {}
        lookup_instance.run([], variables)
    
    assert "organization" in str(excinfo.value)

# Test API error handling
def test_api_error(lookup_instance, mock_auth_token, mock_hostname):
    with patch.object(lookup_instance, '_handle_pagination') as mock_pagination:
        mock_pagination.side_effect = Exception("API Error")
        
        with pytest.raises(AnsibleError) as excinfo:
            variables = {"organization": "my-organization"}
            lookup_instance.run([], variables)
        
        assert "Error retrieving agent pools" in str(excinfo.value)

# Verify plugin registration
def test_plugin_registered():
    lookup = lookup_loader.get("benemon.hcp_community_collection.hcp_terraform_agent_pools")
    assert lookup is not None