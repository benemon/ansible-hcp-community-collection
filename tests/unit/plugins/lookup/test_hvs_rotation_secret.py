from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest
import json
from unittest.mock import MagicMock, patch, call
from ansible.errors import AnsibleError
from ansible_collections.benemon.hcp_community_collection.plugins.lookup.hvs_rotating_secret import LookupModule

MOCK_METADATA_RESPONSE = {
    'secret': {
        'name': 'test-secret',
        'type': 'rotating'
    }
}

MOCK_ROTATING_SECRET_RESPONSE = {
    'secret': {
        'name': 'test-secret',
        'type': 'rotating',
        'rotating_version': {
            'version': 1,
            'values': {
                'username': 'test-user',
                'password': 'test-pass'
            },
            'created_at': '2025-01-29T21:16:38.820489Z',
            'expires_at': '2025-01-30T21:16:38.820489Z',
            'revoked_at': None,
            'keys': ['username', 'password']
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
            MOCK_ROTATING_SECRET_RESPONSE
        ]
        mock.status_code = 200
        mock_request.return_value = mock
        yield mock_request

def test_run_basic(lookup, mock_response):
    """Test basic rotating secret lookup"""
    variables = {
        'organization_id': 'test-org',
        'project_id': 'test-project',
        'app_name': 'test-app',
        'secret_name': 'test-secret',
        'hcp_token': 'test-token'
    }
    
    result = lookup.run([], variables)
    
    expected_calls = [
        call('GET', 
             'https://api.cloud.hashicorp.com/secrets/2023-11-28/organizations/test-org/projects/test-project/apps/test-app/secrets/test-secret',
             headers={'Authorization': 'Bearer test-token', 'Content-Type': 'application/json'},
             params=None),
        call('GET',
             'https://api.cloud.hashicorp.com/secrets/2023-11-28/organizations/test-org/projects/test-project/apps/test-app/secrets/test-secret:open',
             headers={'Authorization': 'Bearer test-token', 'Content-Type': 'application/json'},
             params={})
    ]
    
    assert mock_response.call_args_list == expected_calls
    assert result[0]['rotating_version']['values']['username'] == 'test-user'
    assert result[0]['rotating_version']['values']['password'] == 'test-pass'

def test_run_wrong_secret_type(lookup):
    """Test error handling for wrong secret type"""
    with patch('requests.request') as mock_request:
        mock = MagicMock()
        mock.json.return_value = {
            'secret': {
                'type': 'static'
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
        assert "not a rotating secret" in str(exc.value)