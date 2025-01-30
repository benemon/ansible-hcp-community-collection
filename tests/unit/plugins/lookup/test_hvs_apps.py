from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest
import json
from unittest.mock import MagicMock, patch
from ansible.errors import AnsibleError
from ansible.plugins.lookup import LookupBase
from ansible_collections.benemon.hcp_community_collection.plugins.lookup.hvs_apps import LookupModule

# Mock response data that matches the Swagger specification
MOCK_APPS_RESPONSE = {
    'apps': [
        {
            'name': 'test-app-1',
            'description': 'Test App 1',
            'organization_id': 'org-123',
            'project_id': 'proj-123',
            'created_at': '2025-01-29T21:16:38.820489Z',
            'created_by': {
                'email': 'test@example.com',
                'name': 'test-user',
                'type': 'TYPE_USER'
            },
            'resource_id': 'test-resource-id',
            'resource_name': 'test-resource-name',
            'secret_count': 0,
            'sync_names': [],
            'updated_at': None,
            'updated_by': None
        }
    ],
    'pagination': {
        'next_page_token': '',
        'previous_page_token': ''
    }
}

@pytest.fixture
def lookup():
    return LookupModule()

@pytest.fixture(autouse=True)
def mock_platform():
    """Mock sys.platform to avoid macOS fork safety checks"""
    with patch('sys.platform', 'linux'):
        yield

@pytest.fixture
def mock_response():
    """Set up mock response with proper data structure"""
    with patch('requests.request') as mock_request:
        # Create mock response
        mock = MagicMock()
        mock.json.return_value = MOCK_APPS_RESPONSE
        mock.status_code = 200
        mock_request.return_value = mock
        
        # Print debug info
        print(f"\nMock response setup with data: {json.dumps(mock.json.return_value, indent=2)}")
        yield mock_request

def test_run_basic(lookup, mock_response):
    """Test basic lookup functionality with required parameters"""
    variables = {
        'organization_id': 'test-org',
        'project_id': 'test-project',
        'hcp_token': 'test-token'
    }
    
    result = lookup.run([], variables)
    
    # Verify the mock was called with correct parameters
    mock_response.assert_called_once()
    call_args = mock_response.call_args
    assert 'headers' in call_args[1]
    assert call_args[1]['headers']['Authorization'] == 'Bearer test-token'
    print(f"\nMock result: {json.dumps(result, indent=2)}")

    
    # Verify response structure
    assert isinstance(result, list)
    assert len(result) == 1
    assert isinstance(result[0], list)
    assert len(result[0]) == 1
    assert result[0][0]['name'] == 'test-app-1'

def test_run_missing_required_params(lookup):
    """Test that missing required parameters raise appropriate errors"""
    variables = {
        'organization_id': 'test-org'
        # Missing project_id
    }
    
    with pytest.raises(AnsibleError) as exc:
        lookup.run([], variables)
    assert 'Missing required parameter: project_id' in str(exc.value)

def test_run_with_name_filter(lookup, mock_response):
    """Test lookup with name filtering"""
    variables = {
        'organization_id': 'test-org',
        'project_id': 'test-project',
        'hcp_token': 'test-token',
        'name_contains': 'test'
    }
    
    result = lookup.run([], variables)
    
    mock_response.assert_called_once()
    call_args = mock_response.call_args
    assert 'params' in call_args[1]
    assert call_args[1]['params'].get('name_contains') == 'test'
    
    assert isinstance(result, list)
    assert len(result) == 1
    assert len(result[0]) == 1
    assert result[0][0]['name'] == 'test-app-1'

def test_run_with_pagination(lookup, mock_response):
    """Test lookup with pagination parameters"""
    variables = {
        'organization_id': 'test-org',
        'project_id': 'test-project',
        'hcp_token': 'test-token',
        'page_size': 10,
        'max_pages': 1
    }
    
    result = lookup.run([], variables)
    
    mock_response.assert_called_once()
    call_args = mock_response.call_args
    assert 'params' in call_args[1]
    assert call_args[1]['params'].get('pagination.page_size') == 10
    
    assert isinstance(result, list)
    assert len(result) == 1
    assert len(result[0]) == 1

@patch('requests.request')
def test_run_api_error(mock_request, lookup):
    """Test handling of API errors"""
    mock_request.side_effect = Exception('API Error')
    
    variables = {
        'organization_id': 'test-org',
        'project_id': 'test-project',
        'hcp_token': 'test-token'
    }
    
    with pytest.raises(AnsibleError) as exc:
        lookup.run([], variables)
    assert 'Error listing apps' in str(exc.value)

def test_run_with_terms(lookup, mock_response):
    """Test lookup with parameters passed as terms"""
    terms = [
        'organization_id=test-org',
        'project_id=test-project'
    ]
    variables = {
        'hcp_token': 'test-token'
    }
    
    result = lookup.run(terms, variables)
    
    mock_response.assert_called_once()
    assert isinstance(result, list)
    assert len(result) == 1
    assert len(result[0]) == 1
    assert result[0][0]['name'] == 'test-app-1'

def test_empty_results(lookup):
    """Test handling of empty results from API"""
    empty_response = {'apps': [], 'pagination': {}}
    
    with patch('requests.request') as mock_request:
        mock = MagicMock()
        mock.json.return_value = empty_response
        mock.status_code = 200
        mock_request.return_value = mock
        
        variables = {
            'organization_id': 'test-org',
            'project_id': 'test-project',
            'hcp_token': 'test-token'
        }
        
        result = lookup.run([], variables)
        
        assert isinstance(result, list)
        assert len(result) == 1
        assert len(result[0]) == 0