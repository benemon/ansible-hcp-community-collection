#!/usr/bin/python
# -*- coding: utf-8 -*-

import pytest
import copy
from unittest.mock import patch, MagicMock

# Sample response data for tests
STATE_VERSION_RESPONSE = {
    "data": {
        "id": "sv-123456",
        "type": "state-versions",
        "attributes": {
            "created-at": "2023-01-01T12:00:00Z",
            "size": 12345,
            "hosted-state-download-url": "https://app.terraform.io/api/v2/state-versions/sv-123456/download",
            "modules": {
                "root": {
                    "resources": [
                        {
                            "name": "example",
                            "type": "aws_instance",
                            "count": 1
                        }
                    ]
                }
            },
            "providers": {
                "aws": {
                    "version": "4.0.0"
                }
            },
            "resources-processed": True,
            "state-version": 4,
            "terraform-version": "1.0.0",
            "serial": 1
        },
        "relationships": {
            "workspace": {
                "data": {
                    "id": "ws-12345",
                    "type": "workspaces"
                }
            },
            "outputs": {
                "data": [
                    {
                        "id": "wsout-12345",
                        "type": "state-version-outputs"
                    }
                ]
            }
        }
    }
}

STATE_VERSIONS_LIST_RESPONSE = {
    "data": [
        {
            "id": "sv-123456",
            "type": "state-versions",
            "attributes": {
                "created-at": "2023-01-01T12:00:00Z",
                "size": 12345,
                "resources-processed": True,
                "state-version": 4,
                "terraform-version": "1.0.0",
                "serial": 1
            }
        },
        {
            "id": "sv-654321",
            "type": "state-versions",
            "attributes": {
                "created-at": "2022-12-01T12:00:00Z",
                "size": 10000,
                "resources-processed": True,
                "state-version": 3,
                "terraform-version": "1.0.0",
                "serial": 0
            }
        }
    ],
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

@pytest.fixture
def lookup_instance():
    from ansible_collections.benemon.hcp_community_collection.plugins.lookup.hcp_terraform_state_versions import LookupModule
    return LookupModule()

@pytest.fixture
def mock_auth_token(lookup_instance):
    with patch.object(lookup_instance, '_get_auth_token') as mock:
        mock.return_value = 'mock-token'
        yield mock

@pytest.fixture
def mock_hostname(lookup_instance):
    with patch.object(lookup_instance, '_get_hostname') as mock:
        mock.return_value = 'https://app.terraform.io/api/v2'
        yield mock

def test_get_state_version_by_id(lookup_instance, mock_auth_token, mock_hostname):
    with patch.object(lookup_instance, '_make_request') as mock_request:
        mock_request.return_value = STATE_VERSION_RESPONSE
        variables = {"state_version_id": "sv-123456"}
        result = lookup_instance.run([], variables)
        
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0] == STATE_VERSION_RESPONSE
        
        # Update this line to match the actual call signature with the empty dict parameter
        mock_request.assert_called_once_with('GET', '/state-versions/sv-123456', variables, {})

def test_get_current_state_version(lookup_instance, mock_auth_token, mock_hostname):
    with patch.object(lookup_instance, '_get_current_state_version') as mock_get:
        mock_get.return_value = STATE_VERSION_RESPONSE
        
        with patch.object(lookup_instance, '_make_request') as mock_request:
            # Mock the workspace lookup response
            mock_request.return_value = {"data": {"id": "ws-12345"}}
            
            variables = {"workspace_id": "ws-12345"}
            result = lookup_instance.run([], variables)
            
            assert isinstance(result, list)
            assert len(result) == 1
            assert result[0] == STATE_VERSION_RESPONSE
            
            mock_get.assert_called_once_with("ws-12345", variables)

def test_list_state_versions(lookup_instance, mock_auth_token, mock_hostname):
    # Mock _make_request to avoid real HTTP calls
    with patch.object(lookup_instance, '_make_request') as mock_request:
        # Mock the workspace lookup response
        mock_request.return_value = {"data": {"id": "ws-12345"}}
        
        with patch.object(lookup_instance, '_list_state_versions') as mock_list:
            mock_list.return_value = STATE_VERSIONS_LIST_RESPONSE
            variables = {"organization": "my-org", "workspace_name": "my-workspace", "get_current": False}
            result = lookup_instance.run([], variables)
            
            assert isinstance(result, list)
            assert len(result) == 1
            assert result[0] == STATE_VERSIONS_LIST_RESPONSE
            
            # Verify _list_state_versions was called with correct parameters
            mock_list.assert_called_once_with("my-org", "my-workspace", variables)

def test_list_state_versions_with_status(lookup_instance, mock_auth_token, mock_hostname):
    # Mock _make_request to avoid real HTTP calls
    with patch.object(lookup_instance, '_make_request') as mock_request:
        # Mock the workspace lookup response
        mock_request.return_value = {"data": {"id": "ws-12345"}}
        
        with patch.object(lookup_instance, '_list_state_versions') as mock_list:
            mock_list.return_value = STATE_VERSIONS_LIST_RESPONSE
            variables = {
                "organization": "my-org",
                "workspace_name": "my-workspace",
                "get_current": False,
                "status": "finalized"
            }
            result = lookup_instance.run([], variables)
            
            assert isinstance(result, list)
            assert len(result) == 1
            assert result[0] == STATE_VERSIONS_LIST_RESPONSE
            
            # Verify _list_state_versions was called with correct parameters
            mock_list.assert_called_once()

def test_wait_for_processing(lookup_instance, mock_auth_token, mock_hostname):
    with patch.object(lookup_instance, '_get_state_version_by_id') as mock_get:
        # First return an unprocessed version
        unprocessed = copy.deepcopy(STATE_VERSION_RESPONSE)
        unprocessed['data']['attributes']['resources-processed'] = False
        mock_get.return_value = unprocessed
        
        with patch.object(lookup_instance, '_wait_for_state_version_processing') as mock_wait:
            mock_wait.return_value = STATE_VERSION_RESPONSE
            variables = {"state_version_id": "sv-123456", "wait_for_processing": True}
            result = lookup_instance.run([], variables)
            
            assert isinstance(result, list)
            assert len(result) == 1
            assert result[0] == STATE_VERSION_RESPONSE
            
            # Verify _wait_for_state_version_processing was called with correct parameters
            mock_wait.assert_called_once_with("sv-123456", 120)

def test_missing_parameters(lookup_instance, mock_auth_token, mock_hostname):
    with pytest.raises(Exception) as excinfo:
        variables = {}
        lookup_instance.run([], variables)
    
    assert "Either workspace_id or both organization and workspace_name must be provided" in str(excinfo.value)

def test_api_error(lookup_instance, mock_auth_token, mock_hostname):
    with patch.object(lookup_instance, '_get_state_version_by_id') as mock_get:
        mock_get.side_effect = Exception("API Error")
        
        with pytest.raises(Exception) as excinfo:
            variables = {"state_version_id": "sv-123456"}
            lookup_instance.run([], variables)
        
        assert "Error retrieving state versions" in str(excinfo.value)