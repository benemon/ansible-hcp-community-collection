from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest
import requests
from requests.exceptions import JSONDecodeError, RequestException
from unittest.mock import MagicMock, patch, call
from ansible.errors import AnsibleError
from ansible_collections.benemon.hcp_community_collection.plugins.lookup.packer_versions import LookupModule

# Mock response data that matches actual API response structure
MOCK_VERSIONS_RESPONSE = {
    'versions': [
        {
            'id': 'ver_123456',
            'bucket_name': 'test-images',
            'name': 'v1.0.0',
            'status': 'VERSION_ACTIVE',
            'author_id': 'user_123',
            'created_at': '2025-01-29T21:16:38.820489Z',
            'updated_at': '2025-01-29T21:16:38.820489Z',
            'fingerprint': 'abcd1234',
            'builds': [
                {
                    'id': 'build_123',
                    'version_id': 'ver_123456',
                    'component_type': 'amazon-ebs',
                    'status': 'BUILD_DONE',
                    'packer_run_uuid': 'run_123',
                    'created_at': '2025-01-29T21:16:38.820489Z',
                    'updated_at': '2025-01-29T21:16:38.820489Z',
                    'platform': 'aws',
                    'artifacts': [
                        {
                            'id': 'art_123',
                            'external_identifier': 'ami-123456789',
                            'region': 'us-west-1',
                            'created_at': '2025-01-29T21:16:38.820489Z'
                        }
                    ]
                }
            ],
            'has_descendants': True,
            'template_type': 'HCL2',
            'parents': {
                'href': '/packer/v1/version/123/parents',
                'status': 'UP_TO_DATE'
            }
        },
        {
            'id': 'ver_123457',
            'bucket_name': 'test-images',
            'name': 'v1.1.0',
            'status': 'VERSION_ACTIVE',
            'author_id': 'user_123',
            'created_at': '2025-01-29T22:16:38.820489Z',
            'updated_at': '2025-01-29T22:16:38.820489Z',
            'fingerprint': 'efgh5678',
            'builds': [],
            'has_descendants': False,
            'template_type': 'HCL2',
            'parents': {
                'href': '/packer/v1/version/124/parents',
                'status': 'UP_TO_DATE'
            }
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
        mock.json.return_value = MOCK_VERSIONS_RESPONSE
        mock.status_code = 200
        mock_request.return_value = mock
        yield mock_request

def test_run_basic(lookup, mock_response):
    """Test basic version listing"""
    variables = {
        'organization_id': 'test-org',
        'project_id': 'test-proj',
        'bucket_name': 'test-images',
        'hcp_token': 'test-token'
    }
    
    result = lookup.run([], variables)
    
    # Verify API call was made correctly
    expected_calls = [
        call('GET', 
             'https://api.cloud.hashicorp.com/packer/2023-01-01/organizations/test-org/projects/test-proj/buckets/test-images/versions',
             headers={'Authorization': 'Bearer test-token', 'Content-Type': 'application/json'},
             params={})
    ]
    
    assert mock_response.call_args_list == expected_calls
    assert len(result[0]) == 2
    assert result[0][0]['name'] == 'v1.0.0'
    assert result[0][1]['name'] == 'v1.1.0'

def test_run_with_sorting_by_name(lookup, mock_response):
    """Test version listing with name sorting"""
    variables = {
        'organization_id': 'test-org',
        'project_id': 'test-proj',
        'bucket_name': 'test-images',
        'hcp_token': 'test-token',
        'order_by': ['name desc']
    }
    
    result = lookup.run([], variables)
    
    expected_calls = [
        call('GET',
             'https://api.cloud.hashicorp.com/packer/2023-01-01/organizations/test-org/projects/test-proj/buckets/test-images/versions',
             headers={'Authorization': 'Bearer test-token', 'Content-Type': 'application/json'},
             params={'sorting.order_by': ['name desc']})
    ]
    
    assert mock_response.call_args_list == expected_calls

def test_run_with_sorting_by_updated_at(lookup, mock_response):
    """Test version listing with updated_at sorting"""
    variables = {
        'organization_id': 'test-org',
        'project_id': 'test-proj',
        'bucket_name': 'test-images',
        'hcp_token': 'test-token',
        'order_by': ['updated_at desc']
    }
    
    result = lookup.run([], variables)
    
    expected_calls = [
        call('GET',
             'https://api.cloud.hashicorp.com/packer/2023-01-01/organizations/test-org/projects/test-proj/buckets/test-images/versions',
             headers={'Authorization': 'Bearer test-token', 'Content-Type': 'application/json'},
             params={'sorting.order_by': ['updated_at desc']})
    ]
    
    assert mock_response.call_args_list == expected_calls

def test_run_pagination(lookup, mock_response):
    """Test version listing with pagination"""
    variables = {
        'organization_id': 'test-org',
        'project_id': 'test-proj',
        'bucket_name': 'test-images',
        'hcp_token': 'test-token',
        'page_size': 10
    }
    
    result = lookup.run([], variables)
    
    expected_calls = [
        call('GET',
             'https://api.cloud.hashicorp.com/packer/2023-01-01/organizations/test-org/projects/test-proj/buckets/test-images/versions',
             headers={'Authorization': 'Bearer test-token', 'Content-Type': 'application/json'},
             params={'pagination.page_size': 10})
    ]
    
    assert mock_response.call_args_list == expected_calls

def test_run_missing_required_params(lookup):
    """Test error handling for missing parameters"""
    variables = {
        'organization_id': 'test-org',
        'project_id': 'test-proj'
        # Missing bucket_name
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
        
        # Add bucket_name for versions lookup
        if hasattr(lookup, 'api_version'):  # For packer_versions.py
            variables['bucket_name'] = 'test-images'
        
        with pytest.raises(AnsibleError) as exc:
            lookup.run([], variables)
        
        error_text = 'Error listing versions' if 'bucket_name' in variables else 'Error listing buckets'
        assert error_text in str(exc.value)

def test_empty_response_handling(lookup):
    """Test handling of empty response"""
    with patch('requests.request') as mock_request:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'versions': []}
        mock_request.return_value = mock_response
        
        variables = {
            'organization_id': 'test-org',
            'project_id': 'test-proj',
            'bucket_name': 'test-images',
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
        'bucket_name': 'test-images',
        'hcp_token': 'test-token'
    }
    
    result = lookup.run([], variables)
    version = result[0][0]
    
    # Verify version fields
    assert version['id'] == 'ver_123456'
    assert version['name'] == 'v1.0.0'
    assert version['status'] == 'VERSION_ACTIVE'
    assert version['fingerprint'] == 'abcd1234'
    assert version['template_type'] == 'HCL2'
    assert version['has_descendants'] is True
    
    # Verify build information
    build = version['builds'][0]
    assert build['id'] == 'build_123'
    assert build['component_type'] == 'amazon-ebs'
    assert build['status'] == 'BUILD_DONE'
    assert build['platform'] == 'aws'
    
    # Verify artifact information
    artifact = build['artifacts'][0]
    assert artifact['external_identifier'] == 'ami-123456789'
    assert artifact['region'] == 'us-west-1'

def test_api_version(lookup):
    """Test that correct API version is used"""
    assert lookup.api_version == '2023-01-01'