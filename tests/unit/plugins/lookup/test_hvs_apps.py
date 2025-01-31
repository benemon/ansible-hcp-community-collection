from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest
import json
from unittest.mock import MagicMock, patch, call
from ansible.errors import AnsibleError
from ansible_collections.benemon.hcp_community_collection.plugins.lookup.hvs_apps import LookupModule

# Mock response data that matches the Swagger specification
MOCK_APPS_RESPONSE = {
    'apps': [
        {
            'name': 'test-app-1',
            'description': 'Test App 1',
            'organization_id': 'test-org',
            'project_id': 'test-proj',
            'created_at': '2025-01-29T21:16:38.820489Z',
            'created_by': {
                'name': 'test-user',
                'type': 'user',
                'email': 'test@example.com'
            },
            'resource_id': 'test-resource-id',
            'resource_name': 'test-resource-name',
            'secret_count': 0,
            'sync_names': [],
            'updated_at': '2025-01-29T21:16:38.820489Z',
            'updated_by': None
        }
    ],
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
        mock.json.return_value = MOCK_APPS_RESPONSE
        mock.status_code = 200
        mock_request.return_value = mock
        yield mock_request

def test_run_basic(lookup, mock_response):
    """Test basic apps listing"""
    variables = {
        'organization_id': 'test-org',
        'project_id': 'test-proj',
        'hcp_token': 'test-token'
    }
    
    result = lookup.run([], variables)
    
    # Verify API call was made correctly
    expected_calls = [
        call('GET', 
             'https://api.cloud.hashicorp.com/secrets/2023-11-28/organizations/test-org/projects/test-proj/apps',
             headers={'Authorization': 'Bearer test-token', 'Content-Type': 'application/json'},
             params={})
    ]
    
    assert mock_response.call_args_list == expected_calls
    assert len(result[0]) == 1
    assert result[0][0]['name'] == 'test-app-1'

def test_run_with_filters(lookup, mock_response):
    """Test apps listing with filters"""
    variables = {
        'organization_id': 'test-org',
        'project_id': 'test-proj',
        'hcp_token': 'test-token',
        'name_contains': 'test'
    }
    
    result = lookup.run([], variables)
    
    # Verify API call includes the name_contains filter parameter
    expected_calls = [
        call('GET',
             'https://api.cloud.hashicorp.com/secrets/2023-11-28/organizations/test-org/projects/test-proj/apps',
             headers={'Authorization': 'Bearer test-token', 'Content-Type': 'application/json'},
             params={'name_contains': 'test'})
    ]
    
    assert mock_response.call_args_list == expected_calls
    assert len(result[0]) == 1

def test_run_pagination(lookup, mock_response):
    """Test apps listing with pagination parameters"""
    variables = {
        'organization_id': 'test-org',
        'project_id': 'test-proj',
        'hcp_token': 'test-token',
        'page_size': 10
    }
    
    result = lookup.run([], variables)
    
    # Verify API call was made with pagination parameters
    expected_calls = [
        call('GET',
             'https://api.cloud.hashicorp.com/secrets/2023-11-28/organizations/test-org/projects/test-proj/apps',
             headers={'Authorization': 'Bearer test-token', 'Content-Type': 'application/json'},
             params={'pagination.page_size': 10})
    ]
    
    assert mock_response.call_args_list == expected_calls

def test_run_missing_required_params(lookup):
    """Test error handling for missing parameters"""
    variables = {
        'organization_id': 'test-org'
        # Missing project_id
    }
    
    with pytest.raises(AnsibleError) as exc:
        lookup.run([], variables)
    assert 'Missing required parameter' in str(exc.value)

def test_api_error(lookup):
    """Test handling of API errors"""
    with patch('requests.request') as mock_request:
        # Set up mock to first fail metadata call
        mock_request.side_effect = Exception('API Error')
        
        variables = {
            'organization_id': 'test-org',
            'project_id': 'test-proj',
            'hcp_token': 'test-token',
            'disable_pagination': True  # Disable pagination to ensure only one call
        }
        
        with pytest.raises(AnsibleError) as exc:
            lookup.run([], variables)
        assert 'Error listing apps' in str(exc.value)