from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest
import json
from unittest.mock import MagicMock, patch, call
from ansible.errors import AnsibleError
from ansible_collections.benemon.hcp_community_collection.plugins.lookup.packer_channel import LookupModule

# Mock response data that matches the Swagger specification
MOCK_CHANNEL_RESPONSE = {
    'channel': {
        'id': 'ch_123456',
        'name': 'production',
        'bucket_name': 'my-images',
        'author_id': 'user_123',
        'created_at': '2025-01-29T21:16:38.820489Z',
        'updated_at': '2025-01-29T21:16:38.820489Z',
        'version': {
            'id': 'ver_123',
            'name': 'v1.0.0',
            'fingerprint': 'abcd1234',
            'created_at': '2025-01-29T21:16:38.820489Z',
            'updated_at': '2025-01-29T21:16:38.820489Z',
            'builds': [
                {
                    'id': 'build_123',
                    'version_id': 'ver_123',
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
                        },
                        {
                            'id': 'art_124',
                            'external_identifier': 'ami-987654321',
                            'region': 'us-east-1',
                            'created_at': '2025-01-29T21:16:38.820489Z'
                        }
                    ]
                },
                {
                    'id': 'build_124',
                    'version_id': 'ver_123',
                    'component_type': 'amazon-ebs',
                    'status': 'BUILD_DONE',
                    'packer_run_uuid': 'run_123',
                    'created_at': '2025-01-29T21:16:38.820489Z',
                    'updated_at': '2025-01-29T21:16:38.820489Z',
                    'platform': 'aws',
                    'artifacts': [
                        {
                            'id': 'art_125',
                            'external_identifier': 'ami-abcdef123',
                            'region': 'eu-west-1',
                            'created_at': '2025-01-29T21:16:38.820489Z'
                        }
                    ]
                }
            ]
        },
        'managed': False,
        'restricted': True
    }
}

@pytest.fixture
def lookup():
    return LookupModule()

@pytest.fixture
def mock_response():
    with patch('requests.request') as mock_request:
        mock = MagicMock()
        mock.json.return_value = MOCK_CHANNEL_RESPONSE
        mock.status_code = 200
        mock_request.return_value = mock
        yield mock_request

def test_run_basic(lookup, mock_response):
    """Test basic channel retrieval"""
    variables = {
        'organization_id': 'test-org',
        'project_id': 'test-proj',
        'bucket_name': 'my-images',
        'channel_name': 'production',
        'hcp_token': 'test-token'
    }
    
    result = lookup.run([], variables)
    
    # Verify API call was made correctly
    expected_calls = [
        call('GET', 
             'https://api.cloud.hashicorp.com/packer/2023-01-01/organizations/test-org/projects/test-proj/buckets/my-images/channels/production',
             headers={'Authorization': 'Bearer test-token', 'Content-Type': 'application/json'},
             params=None)
    ]
    
    assert mock_response.call_args_list == expected_calls
    
    # Basic channel verification
    assert result[0]['name'] == 'production'
    assert result[0]['bucket_name'] == 'my-images'
    
    # Version verification
    assert result[0]['version']['fingerprint'] == 'abcd1234'
    
    # Builds verification
    builds = result[0]['version']['builds']
    assert len(builds) == 2
    assert builds[0]['component_type'] == 'amazon-ebs'
    assert builds[0]['platform'] == 'aws'
    assert builds[0]['status'] == 'BUILD_DONE'
    
    # Artifacts verification
    artifacts = builds[0]['artifacts']
    assert len(artifacts) == 2
    assert artifacts[0]['external_identifier'] == 'ami-123456789'
    assert artifacts[0]['region'] == 'us-west-1'
    assert artifacts[1]['external_identifier'] == 'ami-987654321'
    assert artifacts[1]['region'] == 'us-east-1'

def test_build_artifacts_structure(lookup, mock_response):
    """Test detailed build and artifacts structure"""
    variables = {
        'organization_id': 'test-org',
        'project_id': 'test-proj',
        'bucket_name': 'my-images',
        'channel_name': 'production',
        'hcp_token': 'test-token'
    }
    
    result = lookup.run([], variables)
    version = result[0]['version']
    
    # Verify first build
    build1 = version['builds'][0]
    assert build1['id'] == 'build_123'
    assert build1['version_id'] == 'ver_123'
    assert build1['packer_run_uuid'] == 'run_123'
    assert len(build1['artifacts']) == 2
    
    # Verify second build
    build2 = version['builds'][1]
    assert build2['id'] == 'build_124'
    assert len(build2['artifacts']) == 1
    assert build2['artifacts'][0]['external_identifier'] == 'ami-abcdef123'
    assert build2['artifacts'][0]['region'] == 'eu-west-1'

def test_run_missing_required_params(lookup):
    """Test error handling for missing parameters"""
    variables = {
        'organization_id': 'test-org',
        'project_id': 'test-proj'
        # Missing bucket_name and channel_name
    }
    
    with pytest.raises(AnsibleError) as exc:
        lookup.run([], variables)
    assert 'Missing required parameter' in str(exc.value)

def test_api_error(lookup):
    """Test handling of API errors"""
    with patch('requests.request') as mock_request:
        # Set up mock to fail the API call
        mock_request.side_effect = Exception('API Error')
        
        variables = {
            'organization_id': 'test-org',
            'project_id': 'test-proj',
            'bucket_name': 'my-images',
            'channel_name': 'production',
            'hcp_token': 'test-token'
        }
        
        with pytest.raises(AnsibleError) as exc:
            lookup.run([], variables)
        assert 'Error getting channel information' in str(exc.value)

def test_api_version(lookup):
    """Test that correct API version is used"""
    assert lookup.api_version == '2023-01-01'