from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest
import requests
from requests.exceptions import JSONDecodeError, RequestException
from unittest.mock import MagicMock, patch, call
from ansible.errors import AnsibleError
from ansible_collections.benemon.hcp_community_collection.plugins.lookup.packer_buckets import LookupModule

# Mock response data that matches the actual API response structure
MOCK_BUCKETS_RESPONSE = {
    'buckets': [
        {
            'id': 'bucket_123456',
            'name': 'test-images',
            'location': {
                'organization_id': 'test-org',
                'project_id': 'test-proj'
            },
            'latest_version': {
                'id': 'ver_123',
                'fingerprint': 'abcd1234',
                'name': 'v1.0.0',
                'created_at': '2025-01-29T21:16:38.820489Z',
                'updated_at': '2025-01-29T21:16:38.820489Z'
            },
            'created_at': '2025-01-29T21:16:38.820489Z',
            'updated_at': '2025-01-29T21:16:38.820489Z',
            'platforms': ['aws', 'gcp'],
            'description': 'Test image bucket',
            'labels': {
                'env': 'test',
                'team': 'platform'
            },
            'version_count': '5',
            'parents': {
                'href': '/packer/v1/bucket/123/parents',
                'status': 'UP_TO_DATE'
            },
            'children': {
                'href': '/packer/v1/bucket/123/children',
                'status': 'UP_TO_DATE'
            },
            'resource_name': 'packer/project/test-proj/bucket/test-images'
        }
    ]
}

@pytest.fixture
def lookup():
    return LookupModule()

@pytest.fixture
def mock_response():
    with patch('requests.request') as mock_request:
        mock = MagicMock()
        mock.json.return_value = MOCK_BUCKETS_RESPONSE
        mock.status_code = 200
        mock_request.return_value = mock
        yield mock_request

def test_run_basic(lookup, mock_response):
    """Test basic bucket listing"""
    variables = {
        'organization_id': 'test-org',
        'project_id': 'test-proj',
        'hcp_token': 'test-token'
    }
    
    result = lookup.run([], variables)
    
    # Verify API call was made correctly
    expected_calls = [
        call('GET', 
             'https://api.cloud.hashicorp.com/packer/2023-01-01/organizations/test-org/projects/test-proj/buckets',
             headers={'Authorization': 'Bearer test-token', 'Content-Type': 'application/json'},
             params={})
    ]
    
    assert mock_response.call_args_list == expected_calls
    assert len(result[0]) == 1
    assert result[0][0]['name'] == 'test-images'

def test_run_with_sorting_by_name(lookup, mock_response):
    """Test bucket listing with name sorting"""
    variables = {
        'organization_id': 'test-org',
        'project_id': 'test-proj',
        'hcp_token': 'test-token',
        'order_by': ['name desc']
    }
    
    result = lookup.run([], variables)
    
    expected_calls = [
        call('GET',
             'https://api.cloud.hashicorp.com/packer/2023-01-01/organizations/test-org/projects/test-proj/buckets',
             headers={'Authorization': 'Bearer test-token', 'Content-Type': 'application/json'},
             params={'sorting.order_by': ['name desc']})
    ]
    
    assert mock_response.call_args_list == expected_calls

def test_run_with_sorting_by_updated_at(lookup, mock_response):
    """Test bucket listing with updated_at sorting"""
    variables = {
        'organization_id': 'test-org',
        'project_id': 'test-proj',
        'hcp_token': 'test-token',
        'order_by': ['updated_at desc']
    }
    
    result = lookup.run([], variables)
    
    expected_calls = [
        call('GET',
             'https://api.cloud.hashicorp.com/packer/2023-01-01/organizations/test-org/projects/test-proj/buckets',
             headers={'Authorization': 'Bearer test-token', 'Content-Type': 'application/json'},
             params={'sorting.order_by': ['updated_at desc']})
    ]
    
    assert mock_response.call_args_list == expected_calls

def test_run_pagination(lookup, mock_response):
    """Test bucket listing with pagination"""
    variables = {
        'organization_id': 'test-org',
        'project_id': 'test-proj',
        'hcp_token': 'test-token',
        'page_size': 10
    }
    
    result = lookup.run([], variables)
    
    expected_calls = [
        call('GET',
             'https://api.cloud.hashicorp.com/packer/2023-01-01/organizations/test-org/projects/test-proj/buckets',
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
        # Set up mock to fail the request
        mock_request.side_effect = Exception('API Error')
        
        variables = {
            'organization_id': 'test-org',
            'project_id': 'test-proj',
            'hcp_token': 'test-token',
            'disable_pagination': True  # Disable pagination to ensure only one call
        }
        
        with pytest.raises(AnsibleError) as exc:
            lookup.run([], variables)
        
        # For buckets lookup, we expect 'Error listing buckets'
        assert 'Error listing buckets' in str(exc.value)

def test_empty_response_handling(lookup):
    """Test handling of empty response"""
    with patch('requests.request') as mock_request:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'buckets': []}
        mock_request.return_value = mock_response
        
        variables = {
            'organization_id': 'test-org',
            'project_id': 'test-proj',
            'hcp_token': 'test-token'
        }
        
        result = lookup.run([], variables)
        
        assert isinstance(result, list)
        assert len(result[0]) == 0

def test_response_structure(lookup, mock_response):
    """Test detailed response structure matches actual API response"""
    variables = {
        'organization_id': 'test-org',
        'project_id': 'test-proj',
        'hcp_token': 'test-token'
    }
    
    result = lookup.run([], variables)
    bucket = result[0][0]
    
    # Verify all expected fields
    assert bucket['id'] == 'bucket_123456'
    assert bucket['name'] == 'test-images'
    assert bucket['location']['organization_id'] == 'test-org'
    assert bucket['location']['project_id'] == 'test-proj'
    assert bucket['latest_version']['fingerprint'] == 'abcd1234'
    assert bucket['platforms'] == ['aws', 'gcp']
    assert bucket['labels'] == {'env': 'test', 'team': 'platform'}
    assert bucket['version_count'] == '5'
    assert bucket['resource_name'].startswith('packer/project/')

def test_api_version(lookup):
    """Test that correct API version is used"""
    assert lookup.api_version == '2023-01-01'