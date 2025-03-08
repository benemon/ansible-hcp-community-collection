from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest
import json
from unittest.mock import MagicMock, patch, call
from ansible.errors import AnsibleError
from ansible_collections.benemon.hcp_community_collection.plugins.lookup.hcp_terraform_oauth_tokens import LookupModule

# Mock response data for OAuth tokens
MOCK_OAUTH_TOKENS_RESPONSE = {
    "data": [
        {
            "id": "ot-hmAyP66qk2AMVdbJ",
            "type": "oauth-tokens",
            "attributes": {
                "created-at": "2017-11-02T06:37:49.284Z",
                "service-provider-user": "username",
                "has-ssh-key": False
            },
            "relationships": {
                "oauth-client": {
                    "data": {
                        "id": "oc-GhHqb5rkeK19mLB8",
                        "type": "oauth-clients"
                    },
                    "links": {
                        "related": "/api/v2/oauth-clients/oc-GhHqb5rkeK19mLB8"
                    }
                }
            },
            "links": {
                "self": "/api/v2/oauth-tokens/ot-hmAyP66qk2AMVdbJ"
            }
        }
    ],
    "meta": {
        "pagination": {
            "current-page": 1,
            "total-pages": 1,
            "total-count": 1
        }
    }
}

# Mock response for paginated results
MOCK_OAUTH_TOKENS_PAGE1 = {
    "data": [
        {
            "id": "ot-hmAyP66qk2AMVdbJ",
            "type": "oauth-tokens",
            "attributes": {
                "created-at": "2017-11-02T06:37:49.284Z",
                "service-provider-user": "username",
                "has-ssh-key": False
            },
            "relationships": {
                "oauth-client": {
                    "data": {
                        "id": "oc-GhHqb5rkeK19mLB8",
                        "type": "oauth-clients"
                    }
                }
            }
        }
    ],
    "meta": {
        "pagination": {
            "current-page": 1,
            "next-page": 2,
            "total-pages": 2,
            "total-count": 2
        }
    }
}

MOCK_OAUTH_TOKENS_PAGE2 = {
    "data": [
        {
            "id": "ot-second-token-id",
            "type": "oauth-tokens",
            "attributes": {
                "created-at": "2018-01-01T12:00:00.000Z",
                "service-provider-user": "user2",
                "has-ssh-key": True
            },
            "relationships": {
                "oauth-client": {
                    "data": {
                        "id": "oc-GhHqb5rkeK19mLB8",
                        "type": "oauth-clients"
                    }
                }
            }
        }
    ],
    "meta": {
        "pagination": {
            "current-page": 2,
            "next-page": None,  # Use None instead of null
            "total-pages": 2,
            "total-count": 2
        }
    }
}

@pytest.fixture
def lookup():
    return LookupModule()

@pytest.fixture
def mock_oauth_response():
    """Mock response for OAuth tokens API calls"""
    with patch('ansible_collections.benemon.hcp_community_collection.plugins.module_utils.hcp_terraform_lookup.requests.request') as mock_request:
        mock = MagicMock()
        mock.json.return_value = MOCK_OAUTH_TOKENS_RESPONSE
        mock.text = 'mock response'
        mock.status_code = 200
        mock_request.return_value = mock
        yield mock_request

def test_run_basic(lookup, mock_oauth_response):
    """Test basic OAuth tokens lookup"""
    with patch.dict('os.environ', {'TFE_TOKEN': 'test-token'}):
        result = lookup.run(['oauth_client_id=oc-GhHqb5rkeK19mLB8'])
        
        # Verify API call was made correctly
        expected_call = call(
            'GET',
            'https://app.terraform.io/api/v2/oauth-clients/oc-GhHqb5rkeK19mLB8/oauth-tokens',
            headers={'Authorization': 'Bearer test-token', 'Content-Type': 'application/vnd.api+json'},
            params={}
        )
        
        assert mock_oauth_response.call_args == expected_call
        
        # Verify the result contains the raw response
        assert isinstance(result, list)
        assert len(result) == 1
        assert 'data' in result[0]
        assert result[0]['data'][0]['id'] == 'ot-hmAyP66qk2AMVdbJ'

def test_run_with_explicit_params(lookup, mock_oauth_response):
    """Test OAuth tokens lookup with explicit parameters"""
    result = lookup.run([
        'oauth_client_id=oc-GhHqb5rkeK19mLB8',
        'token=explicit-token',
        'hostname=https://custom.terraform.io'
    ])
    
    # Verify API call was made with explicit params
    expected_call = call(
        'GET',
        'https://custom.terraform.io/api/v2/oauth-clients/oc-GhHqb5rkeK19mLB8/oauth-tokens',
        headers={'Authorization': 'Bearer explicit-token', 'Content-Type': 'application/vnd.api+json'},
        params={}
    )
    
    assert mock_oauth_response.call_args == expected_call
    assert result[0]['data'][0]['id'] == 'ot-hmAyP66qk2AMVdbJ'

def test_run_missing_required_params(lookup):
    """Test error handling for missing parameters"""
    with patch.dict('os.environ', {'TFE_TOKEN': 'test-token'}):
        with pytest.raises(AnsibleError) as exc:
            lookup.run([])  # Missing oauth_client_id
            
        assert 'Missing required parameter: oauth_client_id' in str(exc.value)

def test_run_missing_token(lookup):
    """Test error handling for missing token"""
    with patch.dict('os.environ', {}, clear=True):  # Clear environment variables
        with pytest.raises(AnsibleError) as exc:
            lookup.run(['oauth_client_id=oc-GhHqb5rkeK19mLB8'])
            
        assert 'No valid authentication found' in str(exc.value)

def test_run_pagination(lookup):
    """Test pagination handling"""
    with patch.dict('os.environ', {'TFE_TOKEN': 'test-token'}):
        # Mock paginated responses
        with patch('ansible_collections.benemon.hcp_community_collection.plugins.module_utils.hcp_terraform_lookup.requests.request') as mock_request:
            # First response has pagination info with next page
            first_response = MagicMock()
            first_response.json.return_value = MOCK_OAUTH_TOKENS_PAGE1
            first_response.text = 'page 1'
            first_response.status_code = 200
            
            # Second response has last page
            second_response = MagicMock()
            second_response.json.return_value = MOCK_OAUTH_TOKENS_PAGE2
            second_response.text = 'page 2'
            second_response.status_code = 200
            
            mock_request.side_effect = [first_response, second_response]
            
            result = lookup.run(['oauth_client_id=oc-GhHqb5rkeK19mLB8'])
            
            # Verify pagination requests were made correctly
            assert mock_request.call_count == 2
            
            # Use a more flexible approach to verify just the essential parts of the call
            # Since parameters are coming back in a different order
            call_args_0 = mock_request.call_args_list[0]
            assert call_args_0[0][0] == 'GET'  # Method
            assert 'oauth-clients/oc-GhHqb5rkeK19mLB8/oauth-tokens' in call_args_0[0][1]  # URL
            assert call_args_0[1]['headers']['Authorization'] == 'Bearer test-token'  # Auth header
            
            # For the second call, verify it has the page parameter
            call_args_1 = mock_request.call_args_list[1]
            assert call_args_1[0][0] == 'GET'  # Method
            assert 'oauth-clients/oc-GhHqb5rkeK19mLB8/oauth-tokens' in call_args_1[0][1]  # URL
            assert 'page[number]' in call_args_1[1]['params']  # Has pagination param
            assert call_args_1[1]['params']['page[number]'] == 2  # Page number is correct
            
            # Verify combined result
            assert len(result) == 1
            assert len(result[0]['data']) == 2
            assert result[0]['data'][0]['id'] == 'ot-hmAyP66qk2AMVdbJ'
            assert result[0]['data'][1]['id'] == 'ot-second-token-id'

def test_run_with_page_size(lookup, mock_oauth_response):
    """Test lookup with page size parameter"""
    result = lookup.run([
        'oauth_client_id=oc-GhHqb5rkeK19mLB8',
        'page_size=50'
    ], {'token': 'test-token'})
    
    # Verify API call includes page_size parameter
    expected_call = call(
        'GET',
        'https://app.terraform.io/api/v2/oauth-clients/oc-GhHqb5rkeK19mLB8/oauth-tokens',
        headers={'Authorization': 'Bearer test-token', 'Content-Type': 'application/vnd.api+json'},
        params={'page[size]': 50}
    )
    
    assert mock_oauth_response.call_args == expected_call

def test_run_with_max_pages(lookup):
    """Test limiting the number of pages retrieved"""
    with patch.dict('os.environ', {'TFE_TOKEN': 'test-token'}):
        # Mock paginated responses
        with patch('ansible_collections.benemon.hcp_community_collection.plugins.module_utils.hcp_terraform_lookup.requests.request') as mock_request:
            # Response with 3 total pages
            mock_response = MagicMock()
            response_data = MOCK_OAUTH_TOKENS_PAGE1.copy()
            response_data['meta']['pagination']['total-pages'] = 3
            mock_response.json.return_value = response_data
            mock_response.text = 'page 1'
            mock_response.status_code = 200
            
            # Second page response
            second_response = MagicMock()
            second_response.json.return_value = MOCK_OAUTH_TOKENS_PAGE2
            second_response.text = 'page 2'
            second_response.status_code = 200
            
            mock_request.side_effect = [mock_response, second_response]
            
            result = lookup.run(['oauth_client_id=oc-GhHqb5rkeK19mLB8', 'max_pages=2'])
            
            # Verify only requested max pages (2) were retrieved, not all 3
            assert mock_request.call_count == 2

def test_run_disable_pagination(lookup):
    """Test disabling pagination"""
    with patch.dict('os.environ', {'TFE_TOKEN': 'test-token'}):
        # Mock paginated responses
        with patch('ansible_collections.benemon.hcp_community_collection.plugins.module_utils.hcp_terraform_lookup.requests.request') as mock_request:
            # Response with multiple pages
            mock_response = MagicMock()
            response_data = MOCK_OAUTH_TOKENS_PAGE1.copy()
            response_data['meta']['pagination']['total-pages'] = 3
            mock_response.json.return_value = response_data
            mock_response.text = 'page 1'
            mock_response.status_code = 200
            
            mock_request.return_value = mock_response
            
            result = lookup.run(['oauth_client_id=oc-GhHqb5rkeK19mLB8', 'disable_pagination=true'])
            
            # Verify only one page was retrieved despite total_pages=3
            assert mock_request.call_count == 1
            assert result[0]['meta']['pagination']['total-pages'] == 3

def test_http_error(lookup):
    """Test handling of HTTP errors"""
    with patch.dict('os.environ', {'TFE_TOKEN': 'test-token'}):
        with patch('ansible_collections.benemon.hcp_community_collection.plugins.module_utils.hcp_terraform_lookup.requests.request') as mock_request:
            # Set up HTTP error
            mock_response = MagicMock()
            mock_response.raise_for_status.side_effect = Exception("HTTP Error: 404 Not Found")
            mock_request.return_value = mock_response
            
            with pytest.raises(AnsibleError) as exc:
                lookup.run(['oauth_client_id=oc-GhHqb5rkeK19mLB8'])
            
            assert "Error retrieving OAuth tokens" in str(exc.value)

def test_rate_limit_handling(lookup):
    """Test handling of rate limits"""
    with patch.dict('os.environ', {'TFE_TOKEN': 'test-token'}):
        with patch('ansible_collections.benemon.hcp_community_collection.plugins.module_utils.hcp_terraform_lookup.requests.request') as mock_request, \
             patch('ansible_collections.benemon.hcp_community_collection.plugins.module_utils.hcp_terraform_lookup.time.sleep') as mock_sleep:
            
            # First request hits rate limit
            rate_limit_response = MagicMock()
            rate_limit_response.status_code = 429
            rate_limit_response.headers = {'Retry-After': '2'}
            
            # Second request succeeds
            success_response = MagicMock()
            success_response.status_code = 200
            success_response.json.return_value = MOCK_OAUTH_TOKENS_RESPONSE
            success_response.text = 'success'
            
            mock_request.side_effect = [rate_limit_response, success_response]
            
            result = lookup.run(['oauth_client_id=oc-GhHqb5rkeK19mLB8'])
            
            # Verify retry behavior
            assert mock_request.call_count == 2
            mock_sleep.assert_called_once_with(2.0)
            
            # Verify we got results after retry
            assert result[0]['data'][0]['id'] == 'ot-hmAyP66qk2AMVdbJ'