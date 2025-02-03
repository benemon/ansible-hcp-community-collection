from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest
import json
from unittest.mock import MagicMock, patch, call
from ansible.errors import AnsibleError
from ansible_collections.benemon.hcp_community_collection.plugins.lookup.hvs_apps import LookupModule

# Mock response data for successful token response
MOCK_TOKEN_RESPONSE = {
    'access_token': 'test-token-123',
    'expires_in': 3600
}

# Mock response data for apps - reused from your test
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
def mock_apps_response():
    """Mock response for apps API calls"""
    with patch('requests.request') as mock_request:
        mock = MagicMock()
        mock.json.return_value = MOCK_APPS_RESPONSE
        mock.status_code = 200
        mock_request.return_value = mock
        yield mock_request

def test_auth_token_basic(lookup):
    """Test basic token acquisition"""
    with patch('requests.post') as mock_auth_request:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = MOCK_TOKEN_RESPONSE
        mock_auth_request.return_value = mock_response

        variables = {
            'organization_id': 'test-org',
            'project_id': 'test-proj',
            'hcp_client_id': 'test-client',
            'hcp_client_secret': 'test-secret'
        }

        token = lookup._get_auth_token(variables)
        
        # Verify correct token returned
        assert token == MOCK_TOKEN_RESPONSE['access_token']
        
        # Verify request made correctly
        expected_data = {
            'client_id': 'test-client',
            'client_secret': 'test-secret',
            'grant_type': 'client_credentials',
            'audience': 'https://api.hashicorp.cloud'
        }
        
        mock_auth_request.assert_called_once_with(
            'https://auth.idp.hashicorp.com/oauth2/token',
            data=expected_data,
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )

def test_auth_token_rate_limit_with_retry_after(lookup):
    """Test rate limit handling with Retry-After header"""
    with patch('requests.post') as mock_auth_request:
        # Create rate limit response
        rate_limit = MagicMock()
        rate_limit.status_code = 429
        rate_limit.headers = {'Retry-After': '2'}
        
        # Create success response
        success = MagicMock()
        success.status_code = 200
        success.json.return_value = MOCK_TOKEN_RESPONSE
        
        # Sequence responses
        mock_auth_request.side_effect = [rate_limit, success]
        
        variables = {
            'organization_id': 'test-org',
            'project_id': 'test-proj',
            'hcp_client_id': 'test-client',
            'hcp_client_secret': 'test-secret'
        }
        
        with patch('time.sleep') as mock_sleep:
            token = lookup._get_auth_token(variables)
            
            # Verify sleep was called with Retry-After value
            mock_sleep.assert_called_once_with(2.0)
        
        assert token == MOCK_TOKEN_RESPONSE['access_token']
        assert mock_auth_request.call_count == 2

def test_auth_token_rate_limit_backoff(lookup):
    """Test rate limit handling with exponential backoff"""
    with patch('requests.post') as mock_auth_request:
        # Create rate limit response
        rate_limit = MagicMock()
        rate_limit.status_code = 429
        rate_limit.headers = {}  # No Retry-After header
        
        # Create success response
        success = MagicMock()
        success.status_code = 200
        success.json.return_value = MOCK_TOKEN_RESPONSE
        
        # Sequence: two rate limits then success
        mock_auth_request.side_effect = [rate_limit, rate_limit, success]
        
        variables = {
            'organization_id': 'test-org',
            'project_id': 'test-proj',
            'hcp_client_id': 'test-client',
            'hcp_client_secret': 'test-secret'
        }
        
        with patch('time.sleep') as mock_sleep:
            token = lookup._get_auth_token(variables)
            
            # Verify exponential backoff pattern
            assert mock_sleep.call_count == 2
            # Second delay should be longer than first
            assert mock_sleep.call_args_list[1][0][0] > mock_sleep.call_args_list[0][0][0]
        
        assert token == MOCK_TOKEN_RESPONSE['access_token']
        assert mock_auth_request.call_count == 3

def test_auth_token_max_retries(lookup):
    """Test maximum retry limit"""
    with patch('requests.post') as mock_auth_request:
        # Always return rate limit
        rate_limit = MagicMock()
        rate_limit.status_code = 429
        rate_limit.headers = {}
        mock_auth_request.return_value = rate_limit
        
        variables = {
            'organization_id': 'test-org',
            'project_id': 'test-proj',
            'hcp_client_id': 'test-client',
            'hcp_client_secret': 'test-secret'
        }
        
        with patch('time.sleep'), pytest.raises(AnsibleError) as exc:
            lookup._get_auth_token(variables)
        
        assert 'Maximum retry attempts reached for rate limit' in str(exc.value)
        assert mock_auth_request.call_count == 5  # Max retries

def test_auth_token_env_vars(lookup):
    """Test token acquisition using environment variables"""
    with patch('requests.post') as mock_auth_request, \
         patch.dict('os.environ', {'HCP_CLIENT_ID': 'env-client', 'HCP_CLIENT_SECRET': 'env-secret'}):
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = MOCK_TOKEN_RESPONSE
        mock_auth_request.return_value = mock_response

        variables = {
            'organization_id': 'test-org',
            'project_id': 'test-proj'
        }

        token = lookup._get_auth_token(variables)
        
        expected_data = {
            'client_id': 'env-client',
            'client_secret': 'env-secret',
            'grant_type': 'client_credentials',
            'audience': 'https://api.hashicorp.cloud'
        }
        
        mock_auth_request.assert_called_once_with(
            'https://auth.idp.hashicorp.com/oauth2/token',
            data=expected_data,
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )
        assert token == MOCK_TOKEN_RESPONSE['access_token']

def test_auth_token_invalid_response(lookup):
    """Test handling of invalid token response"""
    with patch('requests.post') as mock_auth_request:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'invalid': 'response'}  # Missing required fields
        mock_auth_request.return_value = mock_response

        variables = {
            'organization_id': 'test-org',
            'project_id': 'test-proj',
            'hcp_client_id': 'test-client',
            'hcp_client_secret': 'test-secret'
        }

        with pytest.raises(AnsibleError) as exc:
            lookup._get_auth_token(variables)
        
        assert 'Response missing required fields' in str(exc.value)

# Include your existing tests here

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

def test_api_version(lookup):
    """Test that correct API version is used"""
    assert lookup.api_version == '2023-11-28'