from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest
import json
from unittest.mock import MagicMock, patch, call
from ansible.errors import AnsibleError
from ansible_collections.benemon.hcp_community_collection.plugins.lookup.hvs_static_secret import LookupModule

# Mock response that matches Swagger spec for metadata check
MOCK_METADATA_RESPONSE = {
    'secret': {
        'name': 'test-secret',
        'type': 'kv',  # This is the correct type for static secrets
        'latest_version': 1,
        'created_at': '2025-01-29T21:16:38.820489Z',
        'created_by': {
            'name': 'test-user',
            'type': 'user',
            'email': 'test@example.com'
        }
    }
}

# Mock response that matches Swagger spec for secret value
MOCK_STATIC_SECRET_RESPONSE = {
    'secret': {
        'name': 'test-secret',
        'type': 'kv',
        'static_version': {
            'version': 1,
            'value': 'test-value',
            'created_at': '2025-01-29T21:16:38.820489Z',
            'created_by': {
                'name': 'test-user',
                'type': 'user',
                'email': 'test@example.com'
            }
        }
    }
}

@pytest.fixture
def lookup():
    return LookupModule()

@pytest.fixture
def mock_response():
    with patch('requests.request') as mock_request:
        mock = MagicMock()
        # Configure mock to return different responses for metadata and secret calls
        mock.json.side_effect = [
            MOCK_METADATA_RESPONSE,  # First call gets metadata
            MOCK_STATIC_SECRET_RESPONSE  # Second call gets secret value
        ]
        mock.status_code = 200
        mock_request.return_value = mock
        yield mock_request

def test_run_basic(lookup, mock_response):
    """Test basic static secret lookup"""
    variables = {
        'organization_id': 'test-org',
        'project_id': 'test-project',
        'app_name': 'test-app',
        'secret_name': 'test-secret',
        'hcp_token': 'test-token'
    }
    
    result = lookup.run([], variables)
    
    # Verify both API calls were made correctly
    expected_calls = [
        # First call - metadata check
        call('GET', 
             'https://api.cloud.hashicorp.com/secrets/2023-11-28/organizations/test-org/projects/test-project/apps/test-app/secrets/test-secret',
             headers={'Authorization': 'Bearer test-token', 'Content-Type': 'application/json'},
             params=None),
        # Second call - get secret value
        call('GET',
             'https://api.cloud.hashicorp.com/secrets/2023-11-28/organizations/test-org/projects/test-project/apps/test-app/secrets/test-secret:open',
             headers={'Authorization': 'Bearer test-token', 'Content-Type': 'application/json'},
             params=None)
    ]
    
    assert mock_response.call_args_list == expected_calls
    assert result[0]['static_version']['value'] == 'test-value'

def test_run_specific_version(lookup, mock_response):
    """Test retrieving specific version of static secret"""
    variables = {
        'organization_id': 'test-org',
        'project_id': 'test-project',
        'app_name': 'test-app',
        'secret_name': 'test-secret',
        'version': '2',
        'hcp_token': 'test-token'
    }
    
    result = lookup.run([], variables)
    
    # Verify both API calls
    expected_calls = [
        # First call - metadata check
        call('GET', 
             'https://api.cloud.hashicorp.com/secrets/2023-11-28/organizations/test-org/projects/test-project/apps/test-app/secrets/test-secret',
             headers={'Authorization': 'Bearer test-token', 'Content-Type': 'application/json'},
             params=None),
        # Second call - get specific version
        call('GET',
             'https://api.cloud.hashicorp.com/secrets/2023-11-28/organizations/test-org/projects/test-project/apps/test-app/secrets/test-secret/versions/2:open',
             headers={'Authorization': 'Bearer test-token', 'Content-Type': 'application/json'},
             params=None)
    ]
    
    assert mock_response.call_args_list == expected_calls
    
def test_run_missing_required_params(lookup):
    """Test error handling for missing parameters"""
    variables = {
        'organization_id': 'test-org',
        'project_id': 'test-project'
        # Missing app_name and secret_name
    }
    
    with pytest.raises(AnsibleError) as exc:
        lookup.run([], variables)
    assert 'Missing required parameter' in str(exc.value)

def test_run_wrong_secret_type(lookup):
    """Test error handling for wrong secret type"""
    with patch('requests.request') as mock_request:
        mock = MagicMock()
        mock.json.return_value = {
            'secret': {
                'type': 'rotating',  # Wrong type
                'name': 'test-secret'
            }
        }
        mock.status_code = 200
        mock_request.return_value = mock
        
        variables = {
            'organization_id': 'test-org',
            'project_id': 'test-project',
            'app_name': 'test-app',
            'secret_name': 'test-secret',
            'hcp_token': 'test-token'
        }
        
        with pytest.raises(AnsibleError) as exc:
            lookup.run([], variables)
        assert "not a static secret" in str(exc.value)

def test_api_error(lookup):
    """Test handling of API errors"""
    with patch('requests.request') as mock_request:
        mock_request.side_effect = Exception('API Error')
        
        variables = {
            'organization_id': 'test-org',
            'project_id': 'test-project',
            'app_name': 'test-app',
            'secret_name': 'test-secret',
            'hcp_token': 'test-token'
        }
        
        with pytest.raises(AnsibleError) as exc:
            lookup.run([], variables)
        assert 'Error retrieving secret metadata' in str(exc.value)

def test_api_version(lookup):
    """Test that correct API version is used"""
    assert lookup.api_version == '2023-11-28'