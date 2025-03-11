from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest
import json
from unittest.mock import MagicMock, patch, call
from ansible.errors import AnsibleError
from ansible_collections.benemon.hcp_community_collection.plugins.lookup.hcp_terraform_oauth_clients import LookupModule

# Mock response data for OAuth clients
MOCK_OAUTH_CLIENTS_RESPONSE = {
    "data": [
        {
            "id": "oc-XKFwG6ggfA9n7t1K",
            "type": "oauth-clients",
            "attributes": {
                "created-at": "2018-04-16T20:42:53.771Z",
                "callback-url": "https://app.terraform.io/auth/35936d44-842c-4ddd-b4d4-7c7413",
                "connect-path": "/auth/35936d44-842c-4ddd-b4d4-7c741383dc3a?organization_id=1",
                "service-provider": "github",
                "service-provider-display-name": "GitHub",
                "name": "GitHub Provider",
                "http-url": "https://github.com",
                "api-url": "https://api.github.com",
                "key": None,
                "rsa-public-key": None,
                "organization-scoped": True
            },
            "relationships": {
                "organization": {
                    "data": {
                        "id": "my-organization",
                        "type": "organizations"
                    },
                    "links": {
                        "related": "/api/v2/organizations/my-organization"
                    }
                },
                "projects": {
                    "data": []
                },
                "oauth-tokens": {
                    "data": [],
                    "links": {
                        "related": "/api/v2/oauth-tokens/ot-KaeqH4cy72VPXFQT"
                    }
                },
                "agent-pool": {
                    "data": {
                        "id": "apool-VsmjEMcYkShrckpK",
                        "type": "agent-pools"
                    },
                    "links": {
                        "related": "/api/v2/agent-pools/apool-VsmjEMcYkShrckpK"
                    }
                }
            },
            "links": {
                "self": "/api/v2/oauth-clients/oc-XKFwG6ggfA9n7t1K"
            }
        },
        {
            "id": "oc-FfwXdCaTuyEhZcVp",
            "type": "oauth-clients",
            "attributes": {
                "created-at": "2019-05-20T15:30:22.123Z",
                "callback-url": "https://app.terraform.io/auth/abcdef12345",
                "connect-path": "/auth/abcdef12345?organization_id=1",
                "service-provider": "gitlab_hosted",
                "service-provider-display-name": "GitLab",
                "name": "GitLab Provider",
                "http-url": "https://gitlab.com",
                "api-url": "https://gitlab.com/api/v4",
                "key": None,
                "rsa-public-key": None,
                "organization-scoped": False
            },
            "relationships": {
                "organization": {
                    "data": {
                        "id": "my-organization",
                        "type": "organizations"
                    },
                    "links": {
                        "related": "/api/v2/organizations/my-organization"
                    }
                },
                "projects": {
                    "data": [
                        {"id": "prj-AwfuCJTkdai4xj9w", "type": "projects"}
                    ]
                },
                "oauth-tokens": {
                    "data": [],
                    "links": {
                        "related": "/api/v2/oauth-tokens/ot-SomETokenID"
                    }
                },
                "agent-pool": {
                    "data": None
                }
            },
            "links": {
                "self": "/api/v2/oauth-clients/oc-FfwXdCaTuyEhZcVp"
            }
        }
    ],
    "meta": {
        "pagination": {
            "current-page": 1,
            "total-pages": 1,
            "total-count": 2
        }
    }
}

# Mock response for paginated results
MOCK_OAUTH_CLIENTS_PAGE1 = {
    "data": [
        {
            "id": "oc-XKFwG6ggfA9n7t1K",
            "type": "oauth-clients",
            "attributes": {
                "created-at": "2018-04-16T20:42:53.771Z",
                "service-provider": "github",
                "service-provider-display-name": "GitHub",
                "name": "GitHub Provider",
                "http-url": "https://github.com",
                "organization-scoped": True
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

MOCK_OAUTH_CLIENTS_PAGE2 = {
    "data": [
        {
            "id": "oc-FfwXdCaTuyEhZcVp",
            "type": "oauth-clients",
            "attributes": {
                "created-at": "2019-05-20T15:30:22.123Z",
                "service-provider": "gitlab_hosted",
                "service-provider-display-name": "GitLab",
                "name": "GitLab Provider",
                "http-url": "https://gitlab.com",
                "organization-scoped": False
            }
        }
    ],
    "meta": {
        "pagination": {
            "current-page": 2,
            "next-page": None,
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
    """Mock response for OAuth clients API calls"""
    with patch('ansible_collections.benemon.hcp_community_collection.plugins.module_utils.hcp_terraform_lookup.requests.request') as mock_request:
        mock = MagicMock()
        mock.json.return_value = MOCK_OAUTH_CLIENTS_RESPONSE
        mock.text = 'mock response'
        mock.status_code = 200
        mock_request.return_value = mock
        yield mock_request

def test_run_basic(lookup, mock_oauth_response):
    """Test basic OAuth clients lookup"""
    with patch.dict('os.environ', {'TFE_TOKEN': 'test-token'}):
        result = lookup.run(['organization=my-organization'])
        
        # Verify API call was made correctly
        expected_call = call(
            'GET',
            'https://app.terraform.io/api/v2/organizations/my-organization/oauth-clients',
            headers={'Authorization': 'Bearer test-token', 'Content-Type': 'application/vnd.api+json'},
            params={}
        )
        
        assert mock_oauth_response.call_args == expected_call
        
        # Verify the result contains the raw response
        assert isinstance(result, list)
        assert len(result) == 1
        assert 'data' in result[0]
        assert len(result[0]['data']) == 2
        assert result[0]['data'][0]['id'] == 'oc-XKFwG6ggfA9n7t1K'
        assert result[0]['data'][1]['id'] == 'oc-FfwXdCaTuyEhZcVp'

def test_run_with_explicit_params(lookup, mock_oauth_response):
    """Test OAuth clients lookup with explicit parameters"""
    result = lookup.run([
        'organization=my-organization',
        'token=explicit-token',
        'hostname=https://custom.terraform.io'
    ])
    
    # Verify API call was made with explicit params
    expected_call = call(
        'GET',
        'https://custom.terraform.io/api/v2/organizations/my-organization/oauth-clients',
        headers={'Authorization': 'Bearer explicit-token', 'Content-Type': 'application/vnd.api+json'},
        params={}
    )
    
    assert mock_oauth_response.call_args == expected_call
    assert result[0]['data'][0]['id'] == 'oc-XKFwG6ggfA9n7t1K'

def test_run_missing_required_params(lookup):
    """Test error handling for missing parameters"""
    with patch.dict('os.environ', {'TFE_TOKEN': 'test-token'}):
        with pytest.raises(AnsibleError) as exc:
            lookup.run([])  # Missing organization
            
        assert 'Missing required parameter: organization' in str(exc.value)

def test_run_missing_token(lookup):
    """Test error handling for missing token"""
    with patch.dict('os.environ', {}, clear=True):  # Clear environment variables
        with pytest.raises(AnsibleError) as exc:
            lookup.run(['organization=my-organization'])
            
        assert 'No valid authentication found' in str(exc.value)


# --- Fixtures ---
@pytest.fixture
def lookup():
    return LookupModule()

@pytest.fixture
def mock_oauth_response():
    with patch('ansible_collections.benemon.hcp_community_collection.plugins.module_utils.hcp_terraform_lookup.requests.request') as mock_request:
        mock = MagicMock()
        # Ensure a fresh copy is returned on every call
        mock.json.return_value = MOCK_OAUTH_CLIENTS_RESPONSE.copy()
        mock.text = 'mock response'
        mock.status_code = 200
        mock_request.return_value = mock
        yield mock_request

# --- Split Filter Tests ---

# Filter by name tests
def test_filter_by_name_github(lookup, mock_oauth_response):
    with patch.dict('os.environ', {'TFE_TOKEN': 'test-token'}):
        result = lookup.run(['organization=my-organization', 'name=GitHub'])
        assert len(result[0]['data']) == 1
        assert result[0]['data'][0]['id'] == 'oc-XKFwG6ggfA9n7t1K'
        assert result[0]['data'][0]['attributes']['name'] == 'GitHub Provider'

def test_filter_by_name_gitlab(lookup, mock_oauth_response):
    with patch.dict('os.environ', {'TFE_TOKEN': 'test-token'}):
        result = lookup.run(['organization=my-organization', 'name=GitLab'])
        assert len(result[0]['data']) == 1
        assert result[0]['data'][0]['id'] == 'oc-FfwXdCaTuyEhZcVp'
        assert result[0]['data'][0]['attributes']['name'] == 'GitLab Provider'

def test_filter_by_name_partial_match(lookup, mock_oauth_response):
    with patch.dict('os.environ', {'TFE_TOKEN': 'test-token'}):
        result = lookup.run(['organization=my-organization', 'name=Git'])
        # Expecting both providers to match
        assert len(result[0]['data']) == 2

# Filter by service provider tests
def test_filter_by_service_provider_github(lookup, mock_oauth_response):
    with patch.dict('os.environ', {'TFE_TOKEN': 'test-token'}):
        result = lookup.run(['organization=my-organization', 'service_provider=github'])
        assert len(result[0]['data']) == 1
        assert result[0]['data'][0]['id'] == 'oc-XKFwG6ggfA9n7t1K'
        assert result[0]['data'][0]['attributes']['service-provider'] == 'github'

def test_filter_by_service_provider_gitlab(lookup, mock_oauth_response):
    with patch.dict('os.environ', {'TFE_TOKEN': 'test-token'}):
        result = lookup.run(['organization=my-organization', 'service_provider=gitlab_hosted'])
        assert len(result[0]['data']) == 1
        assert result[0]['data'][0]['id'] == 'oc-FfwXdCaTuyEhZcVp'
        assert result[0]['data'][0]['attributes']['service-provider'] == 'gitlab_hosted'

# Filter by organization scope tests
def test_filter_by_organization_scope_true(lookup, mock_oauth_response):
    with patch.dict('os.environ', {'TFE_TOKEN': 'test-token'}):
        result = lookup.run(['organization=my-organization', 'organization_scoped=true'])
        assert len(result[0]['data']) == 1
        assert result[0]['data'][0]['id'] == 'oc-XKFwG6ggfA9n7t1K'
        assert result[0]['data'][0]['attributes']['organization-scoped'] is True

def test_filter_by_organization_scope_false(lookup, mock_oauth_response):
    with patch.dict('os.environ', {'TFE_TOKEN': 'test-token'}):
        result = lookup.run(['organization=my-organization', 'organization_scoped=false'])
        assert len(result[0]['data']) == 1
        assert result[0]['data'][0]['id'] == 'oc-FfwXdCaTuyEhZcVp'
        assert result[0]['data'][0]['attributes']['organization-scoped'] is False

# Multiple filters tests
def test_multiple_filters_github(lookup, mock_oauth_response):
    with patch.dict('os.environ', {'TFE_TOKEN': 'test-token'}):
        result = lookup.run([
            'organization=my-organization',
            'name=GitHub',
            'service_provider=github'
        ])
        assert len(result[0]['data']) == 1
        assert result[0]['data'][0]['id'] == 'oc-XKFwG6ggfA9n7t1K'

def test_multiple_filters_gitlab(lookup, mock_oauth_response):
    with patch.dict('os.environ', {'TFE_TOKEN': 'test-token'}):
        result = lookup.run([
            'organization=my-organization',
            'name=GitLab',
            'service_provider=gitlab_hosted',
            'organization_scoped=false'
        ])
        assert len(result[0]['data']) == 1
        assert result[0]['data'][0]['id'] == 'oc-FfwXdCaTuyEhZcVp'

def test_multiple_filters_contradictory(lookup, mock_oauth_response):
    with patch.dict('os.environ', {'TFE_TOKEN': 'test-token'}):
        result = lookup.run([
            'organization=my-organization',
            'name=GitHub',
            'service_provider=gitlab_hosted'
        ])
        # No client should match contradictory filters
        assert len(result[0]['data']) == 0

def test_run_pagination(lookup):
    """Test pagination handling"""
    with patch.dict('os.environ', {'TFE_TOKEN': 'test-token'}):
        # Mock paginated responses
        with patch('ansible_collections.benemon.hcp_community_collection.plugins.module_utils.hcp_terraform_lookup.requests.request') as mock_request:
            # First response has pagination info with next page
            first_response = MagicMock()
            first_response.json.return_value = MOCK_OAUTH_CLIENTS_PAGE1
            first_response.text = 'page 1'
            first_response.status_code = 200
            
            # Second response has last page
            second_response = MagicMock()
            second_response.json.return_value = MOCK_OAUTH_CLIENTS_PAGE2
            second_response.text = 'page 2'
            second_response.status_code = 200
            
            mock_request.side_effect = [first_response, second_response]
            
            result = lookup.run(['organization=my-organization'])
            
            # Verify pagination requests were made correctly
            assert mock_request.call_count == 2
            
            # Use a more flexible approach to verify just the essential parts of the call
            call_args_0 = mock_request.call_args_list[0]
            assert call_args_0[0][0] == 'GET'  # Method
            assert 'organizations/my-organization/oauth-clients' in call_args_0[0][1]  # URL
            assert call_args_0[1]['headers']['Authorization'] == 'Bearer test-token'  # Auth header
            
            # For the second call, verify it has the page parameter
            call_args_1 = mock_request.call_args_list[1]
            assert call_args_1[0][0] == 'GET'  # Method
            assert 'organizations/my-organization/oauth-clients' in call_args_1[0][1]  # URL
            assert 'page[number]' in call_args_1[1]['params']  # Has pagination param
            assert call_args_1[1]['params']['page[number]'] == 2  # Page number is correct
            
            # Verify combined result
            assert len(result) == 1
            assert len(result[0]['data']) == 2
            assert result[0]['data'][0]['id'] == 'oc-XKFwG6ggfA9n7t1K'
            assert result[0]['data'][1]['id'] == 'oc-FfwXdCaTuyEhZcVp'

def test_http_error(lookup):
    """Test handling of HTTP errors"""
    with patch.dict('os.environ', {'TFE_TOKEN': 'test-token'}):
        with patch('ansible_collections.benemon.hcp_community_collection.plugins.module_utils.hcp_terraform_lookup.requests.request') as mock_request:
            # Set up HTTP error
            mock_response = MagicMock()
            mock_response.raise_for_status.side_effect = Exception("HTTP Error: 404 Not Found")
            mock_request.return_value = mock_response
            
            with pytest.raises(AnsibleError) as exc:
                lookup.run(['organization=my-organization'])
            
            assert "Error retrieving OAuth clients" in str(exc.value)

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
            success_response.json.return_value = MOCK_OAUTH_CLIENTS_RESPONSE
            success_response.text = 'success'
            
            mock_request.side_effect = [rate_limit_response, success_response]
            
            result = lookup.run(['organization=my-organization'])
            
            # Verify retry behavior
            assert mock_request.call_count == 2
            mock_sleep.assert_called_once_with(2.0)
            
            # Verify we got results after retry
            assert result[0]['data'][0]['id'] == 'oc-XKFwG6ggfA9n7t1K'

def test_empty_results(lookup):
    """Test handling of empty results"""
    with patch.dict('os.environ', {'TFE_TOKEN': 'test-token'}):
        with patch('ansible_collections.benemon.hcp_community_collection.plugins.module_utils.hcp_terraform_lookup.requests.request') as mock_request:
            # Create an empty response
            empty_response = MagicMock()
            empty_response.status_code = 200
            empty_response.json.return_value = {"data": []}
            empty_response.text = 'empty'
            
            mock_request.return_value = empty_response
            
            result = lookup.run(['organization=my-organization'])
            
            # Verify the result is an empty list
            assert len(result[0]['data']) == 0
            
            # Try with filters that won't match anything
            result = lookup.run([
                'organization=my-organization',
                'name=NonExistentProvider'
            ])
            
            assert len(result[0]['data']) == 0