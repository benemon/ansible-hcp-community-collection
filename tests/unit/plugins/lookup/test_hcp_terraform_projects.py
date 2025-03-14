from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest
from unittest.mock import patch, MagicMock

from ansible.errors import AnsibleError
from ansible.plugins.loader import lookup_loader
from ansible_collections.benemon.hcp_community_collection.plugins.lookup.hcp_terraform_projects import LookupModule

# Mock response for projects API
PROJECTS_RESPONSE = {
    "data": [
        {
            "id": "prj-123456",
            "type": "projects",
            "attributes": {
                "name": "Project 1",
                "created-at": "2023-01-01T00:00:00.000Z",
                "permissions": {
                    "can-update": True,
                    "can-destroy": True,
                    "can-access-resources": True
                }
            },
            "relationships": {
                "organization": {
                    "data": {
                        "id": "org-123",
                        "type": "organizations"
                    }
                }
            },
            "links": {
                "self": "/api/v2/projects/prj-123456"
            }
        },
        {
            "id": "prj-789012",
            "type": "projects",
            "attributes": {
                "name": "Project 2",
                "created-at": "2023-02-01T00:00:00.000Z",
                "permissions": {
                    "can-update": True,
                    "can-destroy": True,
                    "can-access-resources": True
                }
            },
            "relationships": {
                "organization": {
                    "data": {
                        "id": "org-123",
                        "type": "organizations"
                    }
                }
            },
            "links": {
                "self": "/api/v2/projects/prj-789012"
            }
        }
    ],
    "links": {
        "self": "https://app.terraform.io/api/v2/organizations/my-org/projects?page[number]=1&page[size]=20",
        "first": "https://app.terraform.io/api/v2/organizations/my-org/projects?page[number]=1&page[size]=20",
        "prev": None,
        "next": None,
        "last": "https://app.terraform.io/api/v2/organizations/my-org/projects?page[number]=1&page[size]=20"
    },
    "meta": {
        "pagination": {
            "current-page": 1,
            "prev-page": None,
            "next-page": None,
            "total-pages": 1,
            "total-count": 2
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
        mock.return_value = PROJECTS_RESPONSE
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

# Test successful project lookup
def test_projects_lookup_success(lookup_instance, mock_make_request, mock_auth_token, mock_hostname):
    variables = {"organization": "my-org"}
    result = lookup_instance.run([], variables)
    
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0] == PROJECTS_RESPONSE
    
    mock_make_request.assert_called_once_with('GET', 'organizations/my-org/projects', variables, {})

# Test project lookup with client-side name filter
def test_projects_lookup_with_name_filter(lookup_instance, mock_make_request, mock_auth_token, mock_hostname):
    variables = {"organization": "my-org", "name": "Project 1"}
    result = lookup_instance.run([], variables)
    
    assert isinstance(result, list)
    assert len(result) == 1
    # Verify that only the project with the exact name "Project 1" is returned
    assert result[0]["data"][0]["attributes"]["name"] == "Project 1"
    assert len(result[0]["data"]) == 1
    
    mock_make_request.assert_called_once_with('GET', 'organizations/my-org/projects', variables, {})

# Test missing required parameters
def test_projects_lookup_missing_params(lookup_instance, mock_auth_token, mock_hostname):
    with pytest.raises(AnsibleError) as excinfo:
        variables = {}
        lookup_instance.run([], variables)
    
    assert "Missing required parameter: organization" in str(excinfo.value)

# Test error handling when the API call fails
def test_projects_lookup_api_error(lookup_instance, mock_auth_token, mock_hostname):
    with patch.object(LookupModule, '_make_request') as mock:
        mock.side_effect = Exception("API Error")
        
        with pytest.raises(AnsibleError) as excinfo:
            variables = {"organization": "my-org"}
            lookup_instance.run([], variables)
        
        assert "API Error" in str(excinfo.value)

# Test parsing parameters from terms
def test_projects_lookup_parse_terms(lookup_instance, mock_make_request, mock_auth_token, mock_hostname):
    with patch.object(LookupModule, '_parse_parameters') as mock_parse:
        mock_parse.return_value = {"organization": "my-org"}
        
        result = lookup_instance.run(["organization=my-org"], {})
        
        assert isinstance(result, list)
        assert len(result) == 1
        
        mock_make_request.assert_called_once_with('GET', 'organizations/my-org/projects', {"organization": "my-org"}, {})

# Test pagination handling
def test_projects_lookup_pagination(lookup_instance, mock_auth_token, mock_hostname):
    with patch.object(LookupModule, '_handle_pagination') as mock:
        mock.return_value = PROJECTS_RESPONSE
        
        variables = {"organization": "my-org"}
        result = lookup_instance.run([], variables)
        
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0] == PROJECTS_RESPONSE
        
        mock.assert_called_once_with('organizations/my-org/projects', variables, {})

# New test: Verify that the q parameter is passed for server-side filtering
def test_projects_lookup_with_q_parameter(lookup_instance, mock_auth_token, mock_hostname):
    with patch.object(LookupModule, '_handle_pagination') as mock_pagination:
        mock_pagination.return_value = PROJECTS_RESPONSE
        variables = {"organization": "my-org", "q": "Project"}
        result = lookup_instance.run([], variables)
        
        # Assert that the q parameter is passed correctly in the query parameters
        mock_pagination.assert_called_once_with(
            'organizations/my-org/projects', 
            variables, 
            {"q": "Project"}
        )
        
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0] == PROJECTS_RESPONSE

# Ensure lookup plugin is properly registered and can be loaded
def test_plugin_registered():
    lookup = lookup_loader.get("benemon.hcp_community_collection.hcp_terraform_projects")
    assert lookup is not None
