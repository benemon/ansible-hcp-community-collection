from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest
import json
from unittest.mock import MagicMock, patch, call
from ansible.errors import AnsibleError
from ansible_collections.benemon.hcp_community_collection.plugins.lookup.hvs_secrets import LookupModule

# Mock response data for secrets listing
MOCK_SECRETS_RESPONSE = {
    'secrets': [{
        'name': 'test-secret-1',
        'type': 'kv',
        'provider': 'static',
        'latest_version': 1,
        'created_at': '2025-01-29T21:16:38.820489Z',
        'created_by': {
            'name': 'test-user',
            'type': 'user',
            'email': 'test@example.com'
        },
        'static_version': {
            'version': 1,
            'created_at': '2025-01-29T21:16:38.820489Z',
            'created_by': {
                'name': 'test-user',
                'type': 'user',
                'email': 'test@example.com'
            }
        },
        'version_count': '1'
    }],
    'pagination': {
        'next_page_token': None,
        'previous_page_token': None
    }
}

@pytest.fixture
def lookup():
    return LookupModule()

@pytest.fixture
def mock_response():
    with patch('requests.request') as mock_request:
        mock = MagicMock()
        mock.json.return_value = MOCK_SECRETS_RESPONSE
        mock.status_code = 200
        mock_request.return_value = mock
        yield mock_request

def test_run_basic(lookup, mock_response):
    """Test basic secrets listing"""
    variables = {
        'organization_id': 'test-org',
        'project_id': 'test-proj',
        'app_name': 'test-app',
        'hcp_token': 'test-token'
    }
    
    result = lookup.run([], variables)
    
    expected_calls = [
        call('GET', 
             'https://api.cloud.hashicorp.com/secrets/2023-11-28/organizations/test-org/projects/test-proj/apps/test-app/secrets',
             headers={'Authorization': 'Bearer test-token', 'Content-Type': 'application/json'},
             params={})
    ]
    
    assert mock_response.call_args_list == expected_calls
    assert len(result[0]) == 1
    assert result[0][0]['name'] == 'test-secret-1'
    assert result[0][0]['type'] == 'kv'

def test_run_with_filters(lookup, mock_response):
    """Test secrets listing with filters"""
    variables = {
        'organization_id': 'test-org',
        'project_id': 'test-proj',
        'app_name': 'test-app',
        'hcp_token': 'test-token',
        'name_contains': 'test',
        'types': 'kv,rotating'
    }
    
    result = lookup.run([], variables)
    
    expected_calls = [
        call('GET',
             'https://api.cloud.hashicorp.com/secrets/2023-11-28/organizations/test-org/projects/test-proj/apps/test-app/secrets',
             headers={'Authorization': 'Bearer test-token', 'Content-Type': 'application/json'},
             params={'name_contains': 'test', 'types': ['kv', 'rotating']})
    ]
    
    assert mock_response.call_args_list == expected_calls
    assert len(result[0]) == 1

def test_run_pagination(lookup, mock_response):
    """Test handling of paginated results"""
    variables = {
        'organization_id': 'test-org',
        'project_id': 'test-proj',
        'app_name': 'test-app',
        'hcp_token': 'test-token',
        'page_size': 10
    }
    
    result = lookup.run([], variables)
    
    expected_calls = [
        call('GET',
             'https://api.cloud.hashicorp.com/secrets/2023-11-28/organizations/test-org/projects/test-proj/apps/test-app/secrets',
             headers={'Authorization': 'Bearer test-token', 'Content-Type': 'application/json'},
             params={'pagination.page_size': 10})
    ]
    
    assert mock_response.call_args_list == expected_calls

def test_run_missing_required_params(lookup):
    """Test error handling for missing required parameters"""
    variables = {
        'organization_id': 'test-org',
        'project_id': 'test-proj',
        # Missing app_name
        'hcp_token': 'test-token'
    }
    
    with pytest.raises(AnsibleError) as exc:
        lookup.run([], variables)
    assert "Missing required parameter: app_name" in str(exc.value)

def test_api_error_handling(lookup):
    """Test handling of API errors"""
    with patch('requests.request') as mock_request:
        # Simulate API error
        mock_request.side_effect = Exception('API Error')
        
        variables = {
            'organization_id': 'test-org',
            'project_id': 'test-proj',
            'app_name': 'test-app',
            'hcp_token': 'test-token',
            'disable_pagination': True
        }
        
        with pytest.raises(AnsibleError) as exc:
            lookup.run([], variables)
        assert 'Error listing secrets' in str(exc.value)

def test_pagination_with_next_token(lookup):
    """Test pagination with next page token"""
    with patch('requests.request') as mock_request:
        # Create responses for pagination
        first_response = MagicMock()
        first_response.status_code = 200
        first_response.json.return_value = {
            'secrets': [{'name': 'secret-1', 'type': 'kv'}],
            'pagination': {'next_page_token': 'next-token'}
        }
        
        second_response = MagicMock()
        second_response.status_code = 200
        second_response.json.return_value = {
            'secrets': [{'name': 'secret-2', 'type': 'kv'}],
            'pagination': {'next_page_token': None}
        }
        
        mock_request.side_effect = [first_response, second_response]
        
        variables = {
            'organization_id': 'test-org',
            'project_id': 'test-proj',
            'app_name': 'test-app',
            'hcp_token': 'test-token',
            'page_size': 1
        }
        
        result = lookup.run([], variables)
        
        assert len(result[0]) == 2
        assert mock_request.call_count == 2

def test_secret_type_filtering(lookup, mock_response):
    """Test filtering secrets by type"""
    variables = {
        'organization_id': 'test-org',
        'project_id': 'test-proj',
        'app_name': 'test-app',
        'hcp_token': 'test-token',
        'types': 'kv'
    }
    
    result = lookup.run([], variables)
    
    expected_calls = [
        call('GET',
             'https://api.cloud.hashicorp.com/secrets/2023-11-28/organizations/test-org/projects/test-proj/apps/test-app/secrets',
             headers={'Authorization': 'Bearer test-token', 'Content-Type': 'application/json'},
             params={'types': ['kv']})
    ]
    
    assert mock_response.call_args_list == expected_calls

def test_empty_response_handling(lookup):
    """Test handling of empty response"""
    with patch('requests.request') as mock_request:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'secrets': []}
        mock_request.return_value = mock_response
        
        variables = {
            'organization_id': 'test-org',
            'project_id': 'test-proj',
            'app_name': 'test-app',
            'hcp_token': 'test-token'
        }
        
        result = lookup.run([], variables)
        
        assert isinstance(result, list)
        assert len(result[0]) == 0

def test_api_version(lookup):
    """Test that correct API version is used"""
    assert lookup.api_version == '2023-11-28'