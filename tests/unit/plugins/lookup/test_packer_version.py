from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest
import json
from unittest.mock import MagicMock, patch, call
from ansible.errors import AnsibleError
from ansible_collections.benemon.hcp_community_collection.plugins.lookup.packer_version import LookupModule

# Mock response data that matches the Swagger specification
MOCK_VERSION_RESPONSE = {
    'version': {
        'id': 'ver_123',
        'bucket_name': 'my-images',
        'name': 'v1.0.0',
        'fingerprint': 'abcd1234',
        'status': 'VERSION_ACTIVE',
        'created_at': '2025-01-29T21:16:38.820489Z',
        'updated_at': '2025-01-29T21:16:38.820489Z',
        'template_type': 'HCL2',
        'has_descendants': True,
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
                'component_type': 'azure-arm',
                'status': 'BUILD_DONE',
                'packer_run_uuid': 'run_123',
                'created_at': '2025-01-29T21:16:38.820489Z',
                'updated_at': '2025-01-29T21:16:38.820489Z',
                'platform': 'azure',
                'artifacts': [
                    {
                        'id': 'art_125',
                        'external_identifier': '/subscriptions/sub123/images/myimage',
                        'region': 'westus',
                        'created_at': '2025-01-29T21:16:38.820489Z'
                    }
                ]
            }
        ]
    }
}

@pytest.fixture
def lookup():
    return LookupModule()

@pytest.fixture
def mock_response():
    with patch('requests.request') as mock_request:
        mock = MagicMock()
        mock.json.return_value = MOCK_VERSION_RESPONSE
        mock.status_code = 200
        mock_request.return_value = mock
        yield mock_request

def test_run_basic(lookup, mock_response):
    """Test basic version retrieval"""
    variables = {
        'organization_id': 'test-org',
        'project_id': 'test-proj',
        'bucket_name': 'my-images',
        'fingerprint': 'abcd1234',
        'hcp_token': 'test-token'
    }
    
    result = lookup.run([], variables)
    
    # Verify API call was made correctly
    expected_calls = [
        call('GET', 
             'https://api.cloud.hashicorp.com/packer/2023-01-01/organizations/test-org/projects/test-proj/buckets/my-images/versions/abcd1234',
             headers={'Authorization': 'Bearer test-token', 'Content-Type': 'application/json'},
             params=None)
    ]
    
    assert mock_response.call_args_list == expected_calls
    
    # Basic version verification
    assert result[0]['id'] == 'ver_123'
    assert result[0]['name'] == 'v1.0.0'
    assert result[0]['fingerprint'] == 'abcd1234'
    assert result[0]['status'] == 'VERSION_ACTIVE'
    assert result[0]['template_type'] == 'HCL2'
    assert result[0]['has_descendants'] is True

def test_builds_and_artifacts(lookup, mock_response):
    """Test detailed build and artifacts structure"""
    variables = {
        'organization_id': 'test-org',
        'project_id': 'test-proj',
        'bucket_name': 'my-images',
        'fingerprint': 'abcd1234',
        'hcp_token': 'test-token'
    }
    
    result = lookup.run([], variables)
    version = result[0]
    
    # Verify builds exist
    assert len(version['builds']) == 2
    
    # Verify first build (AWS)
    build1 = version['builds'][0]
    assert build1['id'] == 'build_123'
    assert build1['component_type'] == 'amazon-ebs'
    assert build1['platform'] == 'aws'
    assert build1['status'] == 'BUILD_DONE'
    assert len(build1['artifacts']) == 2
    
    # Verify AWS artifacts
    aws_artifacts = build1['artifacts']
    assert aws_artifacts[0]['external_identifier'] == 'ami-123456789'
    assert aws_artifacts[0]['region'] == 'us-west-1'
    assert aws_artifacts[1]['external_identifier'] == 'ami-987654321'
    assert aws_artifacts[1]['region'] == 'us-east-1'
    
    # Verify second build (Azure)
    build2 = version['builds'][1]
    assert build2['id'] == 'build_124'
    assert build2['component_type'] == 'azure-arm'
    assert build2['platform'] == 'azure'
    assert len(build2['artifacts']) == 1
    
    # Verify Azure artifact
    azure_artifact = build2['artifacts'][0]
    assert azure_artifact['external_identifier'] == '/subscriptions/sub123/images/myimage'
    assert azure_artifact['region'] == 'westus'

def test_run_missing_required_params(lookup):
    """Test error handling for missing parameters"""
    variables = {
        'organization_id': 'test-org',
        'project_id': 'test-proj'
        # Missing bucket_name and fingerprint
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
            'fingerprint': 'abcd1234',
            'hcp_token': 'test-token'
        }
        
        with pytest.raises(AnsibleError) as exc:
            lookup.run([], variables)
        assert 'Error getting version information' in str(exc.value)

def test_api_version(lookup):
    """Test that correct API version is used"""
    assert lookup.api_version == '2023-01-01'