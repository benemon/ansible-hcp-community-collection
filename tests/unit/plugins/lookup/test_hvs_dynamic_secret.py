from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest
import json
from unittest.mock import MagicMock, patch, call
from ansible.errors import AnsibleError
from ansible_collections.benemon.hcp_community_collection.plugins.lookup.hvs_dynamic_secret import LookupModule

# Mock response that matches Swagger spec for GetAppSecret
MOCK_METADATA_RESPONSE = {
    'secret': {
        'name': 'test-secret',
        'type': 'dynamic',
        'provider': 'aws',
        'latest_version': 1,
        'created_at': '2025-01-29T21:16:38.820489Z',
        'created_by': {
            'name': 'test-user',
            'type': 'user',
            'email': 'test@example.com'
        },
        'dynamic_config': {
            'ttl': '1h'
        }
    }
}

# Mock response that matches Swagger spec for OpenAppSecret
MOCK_DYNAMIC_SECRET_RESPONSE = {
    'secret': {
        'name': 'test-secret',
        'type': 'dynamic',
        'provider': 'aws',
        'latest_version': 1,
        'dynamic_instance': {
            'values': {
                'access_key': 'AKIA...',
                'secret_key': 'abcd1234...'
            },
            'created_at': '2025-01-29T21:16:38.820489Z',
            'expires_at': '2025-01-30T21:16:38.820489Z',
            'ttl': '1h'
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
        mock.json.side_effect = [
            MOCK_METADATA_RESPONSE,
            MOCK_DYNAMIC_SECRET_RESPONSE
        ]
        mock.status_code = 200
        mock_request.return_value = mock
        yield mock_request

def test_run_basic(lookup, mock_response):
    """Test basic dynamic secret lookup"""
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
        # Second call - get secret value using :open endpoint
        call('GET',
             'https://api.cloud.hashicorp.com/secrets/2023-11-28/organizations/test-org/projects/test-project/apps/test-app/secrets/test-secret:open',
             headers={'Authorization': 'Bearer test-token', 'Content-Type': 'application/json'},
             params={})
    ]
    
    assert mock_response.call_args_list == expected_calls
    
    # Verify response structure and content
    assert len(result) == 1
    assert result[0]['type'] == 'dynamic'
    assert result[0]['provider'] == 'aws'
    assert 'dynamic_instance' in result[0]
    assert result[0]['dynamic_instance']['values']['access_key'] == 'AKIA...'
    assert result[0]['dynamic_instance']['values']['secret_key'] == 'abcd1234...'
    assert result[0]['dynamic_instance']['ttl'] == '1h'

def test_run_with_ttl(lookup, mock_response):
    """Test dynamic secret lookup with custom TTL"""
    variables = {
        'organization_id': 'test-org',
        'project_id': 'test-project',
        'app_name': 'test-app',
        'secret_name': 'test-secret',
        'hcp_token': 'test-token',
        'ttl': '2h'
    }
    
    result = lookup.run([], variables)
    
    # Verify both API calls were made correctly
    expected_calls = [
        # First call - metadata check
        call('GET',
             'https://api.cloud.hashicorp.com/secrets/2023-11-28/organizations/test-org/projects/test-project/apps/test-app/secrets/test-secret',
             headers={'Authorization': 'Bearer test-token', 'Content-Type': 'application/json'},
             params=None),
        # Second call - get secret value with TTL
        call('GET',
             'https://api.cloud.hashicorp.com/secrets/2023-11-28/organizations/test-org/projects/test-project/apps/test-app/secrets/test-secret:open',
             headers={'Authorization': 'Bearer test-token', 'Content-Type': 'application/json'},
             params={'ttl': '2h'})
    ]
    
    assert mock_response.call_args_list == expected_calls

def test_run_missing_required_params(lookup):
    """Test error handling for missing parameters"""
    variables = {
        'organization_id': 'test-org',
        'project_id': 'test-project',
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
                'name': 'test-secret',
                'type': 'kv',  # Wrong type
                'latest_version': 1,
                'created_at': '2025-01-29T21:16:38.820489Z',
                'created_by': {
                    'name': 'test-user',
                    'type': 'user',
                    'email': 'test@example.com'
                }
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
        assert "not a dynamic secret" in str(exc.value)

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

def test_invalid_api_response(lookup):
    """Test handling of invalid API response"""
    with patch('requests.request') as mock_request:
        mock = MagicMock()
        mock.json.return_value = {}  # Empty response
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
        assert "Invalid metadata response from API" in str(exc.value)

def test_api_version(lookup):
    """Test that correct API version is used"""
    assert lookup.api_version == '2023-11-28'