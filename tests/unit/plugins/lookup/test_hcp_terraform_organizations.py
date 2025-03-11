from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest
from unittest.mock import patch, MagicMock

from ansible.errors import AnsibleError
from ansible.plugins.loader import lookup_loader
from ansible_collections.benemon.hcp_community_collection.plugins.lookup.hcp_terraform_organizations import LookupModule

# Mock response for organizations API
ORGANIZATIONS_RESPONSE = {
    "data": [
        {
            "id": "my-org-1",
            "type": "organizations",
            "attributes": {
                "name": "My Organization 1",
                "email": "admin@example.com",
                "created-at": "2023-01-01T00:00:00.000Z",
                "collaborator-auth-policy": "password",
                "permissions": {
                    "can-update": True,
                    "can-destroy": True,
                    "can-access-via-teams": True
                }
            },
            "links": {
                "self": "/api/v2/organizations/my-org-1"
            }
        },
        {
            "id": "my-org-2",
            "type": "organizations",
            "attributes": {
                "name": "My Organization 2",
                "email": "admin2@example.com",
                "created-at": "2023-02-01T00:00:00.000Z",
                "collaborator-auth-policy": "two_factor_mandatory",
                "permissions": {
                    "can-update": True,
                    "can-destroy": True,
                    "can-access-via-teams": True
                }
            },
            "links": {
                "self": "/api/v2/organizations/my-org-2"
            }
        }
    ],
    "links": {
        "self": "https://app.terraform.io/api/v2/organizations?page[number]=1&page[size]=20",
        "first": "https://app.terraform.io/api/v2/organizations?page[number]=1&page[size]=20",
        "prev": None,
        "next": None,
        "last": "https://app.terraform.io/api/v2/organizations?page[number]=1&page[size]=20"
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
        mock.return_value = ORGANIZATIONS_RESPONSE
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

# Test successful organization lookup
def test_organizations_lookup_success(lookup_instance, mock_make_request, mock_auth_token, mock_hostname):
    variables = {}
    result = lookup_instance.run([], variables)
    
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0] == ORGANIZATIONS_RESPONSE
    
    mock_make_request.assert_called_once_with('GET', 'organizations', variables, {})

# Test organization lookup with client-side name filter
def test_organizations_lookup_with_name_filter(lookup_instance, mock_make_request, mock_auth_token, mock_hostname):
    variables = {"name": "My Organization 1"}
    result = lookup_instance.run([], variables)
    
    assert isinstance(result, list)
    assert len(result) == 1
    # Verify that only the organization with the exact name "My Organization 1" is returned
    assert result[0]["data"][0]["attributes"]["name"] == "My Organization 1"
    assert len(result[0]["data"]) == 1
    
    mock_make_request.assert_called_once_with('GET', 'organizations', variables, {})

# Test server-side query parameter
def test_organizations_lookup_with_query(lookup_instance, mock_auth_token, mock_hostname):
    with patch.object(LookupModule, '_handle_pagination') as mock_pagination:
        mock_pagination.return_value = ORGANIZATIONS_RESPONSE
        variables = {"q": "example"}
        result = lookup_instance.run([], variables)
        
        # Assert that the q parameter is passed correctly in the query parameters
        mock_pagination.assert_called_once_with(
            'organizations', 
            variables, 
            {"q": "example"}
        )
        
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0] == ORGANIZATIONS_RESPONSE

# Test server-side email filtering
def test_organizations_lookup_with_email_filter(lookup_instance, mock_auth_token, mock_hostname):
    with patch.object(LookupModule, '_handle_pagination') as mock_pagination:
        mock_pagination.return_value = ORGANIZATIONS_RESPONSE
        variables = {"q_email": "admin@example.com"}
        result = lookup_instance.run([], variables)
        
        # Assert that the q[email] parameter is passed correctly
        mock_pagination.assert_called_once_with(
            'organizations', 
            variables, 
            {"q[email]": "admin@example.com"}
        )
        
        assert isinstance(result, list)
        assert len(result) == 1

# Test error handling when the API call fails
def test_organizations_lookup_api_error(lookup_instance, mock_auth_token, mock_hostname):
    with patch.object(LookupModule, '_make_request') as mock:
        mock.side_effect = Exception("API Error")
        
        with pytest.raises(AnsibleError) as excinfo:
            variables = {}
            lookup_instance.run([], variables)
        
        assert "API Error" in str(excinfo.value)

# Test pagination handling
def test_organizations_lookup_pagination(lookup_instance, mock_auth_token, mock_hostname):
    with patch.object(LookupModule, '_handle_pagination') as mock:
        mock.return_value = ORGANIZATIONS_RESPONSE
        
        variables = {}
        result = lookup_instance.run([], variables)
        
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0] == ORGANIZATIONS_RESPONSE
        
        mock.assert_called_once_with('organizations', variables, {})

# Ensure lookup plugin is properly registered and can be loaded
def test_plugin_registered():
    lookup = lookup_loader.get("benemon.hcp_community_collection.hcp_terraform_organizations")
    assert lookup is not None