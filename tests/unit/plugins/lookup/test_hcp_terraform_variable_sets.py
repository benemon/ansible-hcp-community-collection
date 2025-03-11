from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest
from unittest.mock import patch, MagicMock

from ansible.errors import AnsibleError
from ansible.plugins.loader import lookup_loader
from ansible_collections.benemon.hcp_community_collection.plugins.lookup.hcp_terraform_variable_sets import LookupModule

# Mock response for variable sets API
VARSETS_RESPONSE = {
    "data": [
        {
            "id": "varset-123456",
            "type": "varsets",
            "attributes": {
                "name": "AWS Credentials",
                "description": "AWS access keys for production",
                "global": False,
                "priority": False,
                "updated-at": "2023-03-06T21:48:33.588Z",
                "var-count": 2,
                "workspace-count": 3,
                "project-count": 1
            },
            "relationships": {
                "organization": {
                    "data": {
                        "id": "my-org",
                        "type": "organizations"
                    }
                },
                "vars": {
                    "data": [
                        {"id": "var-abc123", "type": "vars"},
                        {"id": "var-def456", "type": "vars"}
                    ]
                },
                "workspaces": {
                    "data": [
                        {"id": "ws-123456", "type": "workspaces"},
                        {"id": "ws-654321", "type": "workspaces"},
                        {"id": "ws-789012", "type": "workspaces"}
                    ]
                },
                "projects": {
                    "data": [
                        {"id": "prj-123456", "type": "projects"}
                    ]
                },
                "parent": {
                    "data": {
                        "id": "my-org",
                        "type": "organizations"
                    }
                }
            }
        },
        {
            "id": "varset-789012",
            "type": "varsets",
            "attributes": {
                "name": "GCP Credentials",
                "description": "GCP service account keys",
                "global": True,
                "priority": True,
                "updated-at": "2023-04-15T18:22:11.423Z",
                "var-count": 3,
                "workspace-count": 0,
                "project-count": 0
            },
            "relationships": {
                "organization": {
                    "data": {
                        "id": "my-org",
                        "type": "organizations"
                    }
                },
                "vars": {
                    "data": [
                        {"id": "var-ghi789", "type": "vars"},
                        {"id": "var-jkl012", "type": "vars"},
                        {"id": "var-mno345", "type": "vars"}
                    ]
                },
                "workspaces": {
                    "data": []
                },
                "projects": {
                    "data": []
                },
                "parent": {
                    "data": {
                        "id": "my-org",
                        "type": "organizations"
                    }
                }
            }
        }
    ],
    "links": {
        "self": "https://app.terraform.io/api/v2/organizations/my-org/varsets?page[number]=1&page[size]=20",
        "first": "https://app.terraform.io/api/v2/organizations/my-org/varsets?page[number]=1&page[size]=20",
        "prev": None,
        "next": None,
        "last": "https://app.terraform.io/api/v2/organizations/my-org/varsets?page[number]=1&page[size]=20"
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

VARSET_DETAIL_RESPONSE = {
    "data": {
        "id": "varset-123456",
        "type": "varsets",
        "attributes": {
            "name": "AWS Credentials",
            "description": "AWS access keys for production",
            "global": False,
            "priority": False,
            "updated-at": "2023-03-06T21:48:33.588Z",
            "var-count": 2,
            "workspace-count": 3,
            "project-count": 1
        },
        "relationships": {
            "organization": {
                "data": {
                    "id": "my-org",
                    "type": "organizations"
                }
            },
            "vars": {
                "data": [
                    {"id": "var-abc123", "type": "vars"},
                    {"id": "var-def456", "type": "vars"}
                ]
            },
            "workspaces": {
                "data": [
                    {"id": "ws-123456", "type": "workspaces"},
                    {"id": "ws-654321", "type": "workspaces"},
                    {"id": "ws-789012", "type": "workspaces"}
                ]
            },
            "projects": {
                "data": [
                    {"id": "prj-123456", "type": "projects"}
                ]
            },
            "parent": {
                "data": {
                    "id": "my-org",
                    "type": "organizations"
                }
            }
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
        mock.return_value = VARSETS_RESPONSE
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

# Test successful variable set lookup by organization
def test_varsets_lookup_by_organization(lookup_instance, mock_make_request, mock_auth_token, mock_hostname):
    # Setup variables with organization parameter
    variables = {"organization": "my-org"}
    result = lookup_instance.run([], variables)
    
    # Verify the result
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0] == VARSETS_RESPONSE
    
    # Verify the _make_request call
    mock_make_request.assert_called_once_with('GET', 'organizations/my-org/varsets', variables, {})

# Test variable set lookup by project ID
def test_varsets_lookup_by_project(lookup_instance, mock_make_request, mock_auth_token, mock_hostname):
    # Setup variables with project_id parameter
    variables = {"project_id": "prj-123456"}
    result = lookup_instance.run([], variables)
    
    # Verify the result
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0] == VARSETS_RESPONSE
    
    # Verify the _make_request call
    mock_make_request.assert_called_once_with('GET', 'projects/prj-123456/varsets', variables, {})

# Test variable set lookup by workspace ID
def test_varsets_lookup_by_workspace(lookup_instance, mock_make_request, mock_auth_token, mock_hostname):
    # Setup variables with workspace_id parameter
    variables = {"workspace_id": "ws-123456"}
    result = lookup_instance.run([], variables)
    
    # Verify the result
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0] == VARSETS_RESPONSE
    
    # Verify the _make_request call
    mock_make_request.assert_called_once_with('GET', 'workspaces/ws-123456/varsets', variables, {})

# Test variable set lookup by ID
def test_varsets_lookup_by_id(lookup_instance, mock_auth_token, mock_hostname):
    # Mock _make_request to return a single variable set
    with patch.object(LookupModule, '_make_request') as mock:
        mock.return_value = VARSET_DETAIL_RESPONSE
        
        # Setup variables with id parameter
        variables = {"id": "varset-123456"}
        result = lookup_instance.run([], variables)
        
        # Verify the result
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0] == VARSET_DETAIL_RESPONSE
        
        # Verify the _make_request call
        mock.assert_called_once_with('GET', 'varsets/varset-123456', variables, {})

# Test variable set lookup with search query
def test_varsets_lookup_with_search_query(lookup_instance, mock_make_request, mock_auth_token, mock_hostname):
    variables = {"organization": "my-org", "q": "AWS"}
    result = lookup_instance.run([], variables)
    
    # Verify the result
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0] == VARSETS_RESPONSE
    
    # Verify the _make_request call includes the q parameter
    mock_make_request.assert_called_once_with('GET', 'organizations/my-org/varsets', variables, {'q': 'AWS'})

# Test missing required parameters
def test_varsets_lookup_missing_params(lookup_instance, mock_auth_token, mock_hostname):
    with pytest.raises(AnsibleError) as excinfo:
        variables = {}
        lookup_instance.run([], variables)
    
    # Verify the error message
    assert "One of 'organization', 'project_id', 'workspace_id', or 'id' must be specified" in str(excinfo.value)

# Test error handling
def test_varsets_lookup_api_error(lookup_instance, mock_auth_token, mock_hostname):
    # Mock _make_request to raise an exception
    with patch.object(LookupModule, '_make_request') as mock:
        mock.side_effect = Exception("API Error")
        
        with pytest.raises(AnsibleError) as excinfo:
            variables = {"organization": "my-org"}
            lookup_instance.run([], variables)
        
        # Verify the error message contains our API error
        assert "API Error" in str(excinfo.value)

# Test pagination handling
def test_varsets_lookup_pagination(lookup_instance, mock_auth_token, mock_hostname):
    # Create a paginated response
    page1 = {
        "data": [VARSETS_RESPONSE["data"][0]],
        "meta": {
            "pagination": {
                "current-page": 1,
                "next-page": 2,
                "total-pages": 2
            }
        }
    }
    
    page2 = {
        "data": [VARSETS_RESPONSE["data"][1]],
        "meta": {
            "pagination": {
                "current-page": 2,
                "next-page": None,
                "total-pages": 2
            }
        }
    }
    
    # Mock _handle_pagination to return combined data
    with patch.object(LookupModule, '_handle_pagination') as mock:
        mock.return_value = VARSETS_RESPONSE
        
        variables = {"organization": "my-org"}
        result = lookup_instance.run([], variables)
        
        # Verify the result
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0] == VARSETS_RESPONSE
        
        # Verify the _handle_pagination call
        mock.assert_called_once_with('organizations/my-org/varsets', variables, {})

# Ensure lookup plugin is properly registered and can be loaded
def test_plugin_registered():
    lookup = lookup_loader.get("benemon.hcp_community_collection.hcp_terraform_variable_sets")
    assert lookup is not None