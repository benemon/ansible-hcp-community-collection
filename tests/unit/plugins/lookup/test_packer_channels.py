from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest
import json
from unittest.mock import MagicMock, patch, call
from ansible.errors import AnsibleError
from ansible_collections.benemon.hcp_community_collection.plugins.lookup.packer_channels import LookupModule

# Mock response data that matches actual API response structure
MOCK_CHANNELS_RESPONSE = {
    'channels': [
        {
            'id': 'ch_123456',
            'name': 'production',
            'bucket_name': 'test-images',
            'author_id': 'user_123',
            'created_at': '2025-01-29T21:16:38.820489Z',
            'updated_at': '2025-01-29T21:16:38.820489Z',
            'version': {
                'id': 'ver_123',
                'name': 'v1.0.0',
                'fingerprint': 'abcd1234'
            },
            'managed': False,
            'restricted': True
        },
        {
            'id': 'ch_123457',
            'name': 'latest',
            'bucket_name': 'test-images',
            'author_id': 'system',
            'created_at': '2025-01-29T21:16:38.820489Z',
            'updated_at': '2025-01-29T21:16:38.820489Z',
            'version': {
                'id': 'ver_124',
                'name': 'v1.1.0',
                'fingerprint': 'efgh5678'
            },
            'managed': True,
            'restricted': False
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
        mock.json.return_value = MOCK_CHANNELS_RESPONSE
        mock.status_code = 200
        mock_request.return_value = mock
        yield mock_request

def test_run_basic(lookup, mock_response):
    """Test basic channel listing"""
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
             'https://api.cloud.hashicorp.com/packer/2023-01-01/organizations/test-org/projects/test-proj/buckets/test-images/channels',
             headers={'Authorization': 'Bearer test-token', 'Content-Type': 'application/json'},
             params=None)
    ]
    
    assert mock_response.call_args_list == expected_calls
    assert len(result[0]) == 2
    assert result[0][0]['name'] == 'production'
    assert result[0][1]['name'] == 'latest'

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
        mock_request.side_effect = Exception('API Error')
        
        variables = {
            'organization_id': 'test-org',
            'project_id': 'test-proj',
            'bucket_name': 'test-images',
            'hcp_token': 'test-token'
        }
        
        with pytest.raises(AnsibleError) as exc:
            lookup.run([], variables)
        assert 'Error listing channels' in str(exc.value)

def test_empty_response_handling(lookup):
    """Test handling of empty response"""
    with patch('requests.request') as mock_request:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'channels': []}
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
    
    # Test regular channel structure
    channel = result[0][0]
    assert channel['id'] == 'ch_123456'
    assert channel['name'] == 'production'
    assert channel['bucket_name'] == 'test-images'
    assert channel['author_id'] == 'user_123'
    assert 'created_at' in channel
    assert 'updated_at' in channel
    assert channel['version']['fingerprint'] == 'abcd1234'
    assert channel['managed'] is False
    assert channel['restricted'] is True
    
    # Test managed channel structure
    managed_channel = result[0][1]
    assert managed_channel['name'] == 'latest'
    assert managed_channel['managed'] is True
    assert managed_channel['restricted'] is False

def test_api_version(lookup):
    """Test that correct API version is used"""
    assert lookup.api_version == '2023-01-01'