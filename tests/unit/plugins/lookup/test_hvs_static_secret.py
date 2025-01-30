from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest
import json
from unittest.mock import MagicMock, patch
from ansible.errors import AnsibleError
from ansible_collections.benemon.hcp_community_collection.plugins.lookup.hvs_static_secret import LookupModule

MOCK_METADATA_RESPONSE = {
    'secret': {
        'name': 'test-secret',
        'type': 'kv'
    }
}

MOCK_STATIC_SECRET_RESPONSE = {
    'secret': {
        'name': 'test-secret',
        'type': 'static',
        'static_version': {
            'version': 1,
            'value': 'test-value',
            'created_at': '2025-01-29T21:16:38.820489Z',
            'created_by_id': 'user-123'
        }
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
    with patch('requests.request') as mock_request:
        mock = MagicMock()
        mock.json.return_value = MOCK_STATIC_SECRET_RESPONSE
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
    
    mock_response.assert_called_once()
    call_args = mock_response.call_args
    assert 'headers' in call_args[1]
    assert call_args[1]['headers']['Authorization'] == 'Bearer test-token'
    
    assert isinstance(result, list)
    assert len(result) == 1
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
    
    mock_response.assert_called_once()
    assert '/versions/2:open' in mock_response.call_args[0][1]

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
                'rotating_version': {  # Wrong type
                    'version': 1
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
        assert 'Retrieved rotating secret' in str(exc.value)