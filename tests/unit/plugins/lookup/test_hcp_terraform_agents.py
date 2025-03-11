from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest
from unittest.mock import patch, MagicMock

from ansible.errors import AnsibleError
from ansible.plugins.loader import lookup_loader
from ansible_collections.benemon.hcp_community_collection.plugins.lookup.hcp_terraform_agents import LookupModule

# Mock response for agents API
AGENTS_RESPONSE = {
    "data": [
        {
            "id": "agent-A726QeosTCpCumAs",
            "type": "agents",
            "attributes": {
                "name": "my-cool-agent",
                "status": "idle",
                "ip-address": "123.123.123.123",
                "last-ping-at": "2020-10-09T18:52:25.246Z"
            },
            "links": {
                "self": "/api/v2/agents/agent-A726QeosTCpCumAs"
            }
        },
        {
            "id": "agent-4cQzjbr1cnM6Pcxr",
            "type": "agents",
            "attributes": {
                "name": "my-other-cool-agent",
                "status": "busy",
                "ip-address": "123.123.123.123",
                "last-ping-at": "2020-10-09T15:25:09.726Z"
            },
            "links": {
                "self": "/api/v2/agents/agent-4cQzjbr1cnM6Pcxr"
            }
        },
        {
            "id": "agent-yEJjXQCucpNxtxd2",
            "type": "agents",
            "attributes": {
                "name": None,
                "status": "errored",
                "ip-address": "123.123.123.123",
                "last-ping-at": "2020-08-11T06:22:20.300Z"
            },
            "links": {
                "self": "/api/v2/agents/agent-yEJjXQCucpNxtxd2"
            }
        }
    ],
    "links": {
        "self": "https://app.terraform.io/api/v2/agent-pools/apool-yoGUFz5zcRMMz53i/agents?page[number]=1&page[size]=20",
        "first": "https://app.terraform.io/api/v2/agent-pools/apool-yoGUFz5zcRMMz53i/agents?page[number]=1&page[size]=20",
        "prev": None,
        "next": None,
        "last": "https://app.terraform.io/api/v2/agent-pools/apool-yoGUFz5zcRMMz53i/agents?page[number]=1&page[size]=20"
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
        mock.return_value = AGENTS_RESPONSE
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

# Test retrieving all agents for a pool
def test_get_all_agents(lookup_instance, mock_handle_pagination, mock_auth_token, mock_hostname):
    variables = {"agent_pool_id": "apool-yoGUFz5zcRMMz53i"}
    result = lookup_instance.run([], variables)
    
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0] == AGENTS_RESPONSE
    
    # Verify the correct endpoint and parameters were used
    mock_handle_pagination.assert_called_once_with(
        "agent-pools/apool-yoGUFz5zcRMMz53i/agents", 
        variables, 
        {}
    )

# Test with last ping since filter
def test_get_agents_with_last_ping_filter(lookup_instance, mock_handle_pagination, mock_auth_token, mock_hostname):
    variables = {
        "agent_pool_id": "apool-yoGUFz5zcRMMz53i",
        "last_ping_since": "2020-09-01T00:00:00Z"
    }
    result = lookup_instance.run([], variables)
    
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0] == AGENTS_RESPONSE
    
    # Verify the last ping filter was passed
    mock_handle_pagination.assert_called_once_with(
        "agent-pools/apool-yoGUFz5zcRMMz53i/agents", 
        variables, 
        {"filter[last-ping-since]": "2020-09-01T00:00:00Z"}
    )

# Test client-side status filtering
def test_get_agents_with_status_filter(lookup_instance, mock_handle_pagination, mock_auth_token, mock_hostname):
    variables = {
        "agent_pool_id": "apool-yoGUFz5zcRMMz53i",
        "status": "idle"
    }
    result = lookup_instance.run([], variables)
    
    assert isinstance(result, list)
    assert len(result) == 1
    
    # Result should contain only the idle agent after client-side filtering
    filtered_data = result[0]["data"]
    assert len(filtered_data) == 1
    assert filtered_data[0]["attributes"]["status"] == "idle"
    assert filtered_data[0]["id"] == "agent-A726QeosTCpCumAs"
    
    # The original request doesn't include status filtering (that's done client-side)
    mock_handle_pagination.assert_called_once_with(
        "agent-pools/apool-yoGUFz5zcRMMz53i/agents", 
        variables, 
        {}
    )

# Test with multiple filters
def test_get_agents_with_multiple_filters(lookup_instance, mock_handle_pagination, mock_auth_token, mock_hostname):
    variables = {
        "agent_pool_id": "apool-yoGUFz5zcRMMz53i",
        "last_ping_since": "2020-09-01T00:00:00Z",
        "status": "busy"
    }
    
    # Set up mock to return multiple agents
    mock_handle_pagination.return_value = AGENTS_RESPONSE
    
    result = lookup_instance.run([], variables)
    
    assert isinstance(result, list)
    assert len(result) == 1
    
    # Should have filtered to just the busy agent
    filtered_data = result[0]["data"]
    assert len(filtered_data) == 1
    assert filtered_data[0]["attributes"]["status"] == "busy"
    assert filtered_data[0]["id"] == "agent-4cQzjbr1cnM6Pcxr"
    
    # Verify server-side filter was passed but status filtering is client-side
    mock_handle_pagination.assert_called_once_with(
        "agent-pools/apool-yoGUFz5zcRMMz53i/agents", 
        variables, 
        {"filter[last-ping-since]": "2020-09-01T00:00:00Z"}
    )

# Test missing agent_pool_id parameter
def test_missing_agent_pool_id(lookup_instance, mock_auth_token, mock_hostname):
    with pytest.raises(AnsibleError) as excinfo:
        variables = {}
        lookup_instance.run([], variables)
    
    assert "agent_pool_id" in str(excinfo.value)

# Test API error handling
def test_api_error(lookup_instance, mock_auth_token, mock_hostname):
    with patch.object(lookup_instance, '_handle_pagination') as mock_pagination:
        mock_pagination.side_effect = Exception("API Error")
        
        with pytest.raises(AnsibleError) as excinfo:
            variables = {"agent_pool_id": "apool-yoGUFz5zcRMMz53i"}
            lookup_instance.run([], variables)
        
        assert "Error retrieving agents" in str(excinfo.value)

# Verify plugin registration
def test_plugin_registered():
    lookup = lookup_loader.get("benemon.hcp_community_collection.hcp_terraform_agents")
    assert lookup is not None