from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest
from unittest.mock import patch, MagicMock

from ansible_collections.benemon.hcp_community_collection.plugins.modules.hcp_terraform_agent_pool import TerraformAgentPoolModule
from ansible.module_utils.basic import AnsibleModule

# Mock responses for Agent Pool API
AGENT_POOL_DETAILS_RESPONSE = {
    "data": {
        "id": "apool-yoGUFz5zcRMMz53i",
        "type": "agent-pools",
        "attributes": {
            "name": "example-pool",
            "created-at": "2020-08-05T18:10:26.964Z",
            "organization-scoped": False
        },
        "relationships": {
            "agents": {
                "links": {
                    "related": "/api/v2/agent-pools/apool-yoGUFz5zcRMMz53i/agents"
                }
            },
            "authentication-tokens": {
                "links": {
                    "related": "/api/v2/agent-pools/apool-yoGUFz5zcRMMz53i/authentication-tokens"
                }
            },
            "workspaces": {
                "data": [
                    {
                        "id": "ws-9EEkcEQSA3XgWyGe",
                        "type": "workspaces"
                    }
                ]
            },
            "allowed-workspaces": {
                "data": [
                    {
                        "id": "ws-x9taqV23mxrGcDrn",
                        "type": "workspaces"
                    }
                ]
            }
        },
        "links": {
            "self": "/api/v2/agent-pools/apool-yoGUFz5zcRMMz53i"
        }
    }
}

AGENT_POOL_CREATE_RESPONSE = {
    "data": {
        "id": "apool-55jZekR57npjHHYQ",
        "type": "agent-pools",
        "attributes": {
            "name": "my-pool",
            "created-at": "2020-10-13T16:32:45.165Z",
            "organization-scoped": False
        },
        "relationships": {
            "agents": {
                "links": {
                    "related": "/api/v2/agent-pools/apool-55jZekR57npjHHYQ/agents"
                }
            },
            "authentication-tokens": {
                "links": {
                    "related": "/api/v2/agent-pools/apool-55jZekR57npjHHYQ/authentication-tokens"
                }
            },
            "workspaces": {
                "data": []
            },
            "allowed-workspaces": {
                "data": [
                    {
                        "id": "ws-x9taqV23mxrGcDrn",
                        "type": "workspaces"
                    }
                ]
            }
        },
        "links": {
            "self": "/api/v2/agent-pools/apool-55jZekR57npjHHYQ"
        }
    }
}

# Fixture to create a mock TerraformAgentPoolModule instance
@pytest.fixture
def agent_pool_module():
    # Create a proper mock for AnsibleModule
    mock_ansible_module = MagicMock()
    mock_ansible_module.params = {
        'token': 'test-token',
        'hostname': 'https://app.terraform.io',
        'organization': 'my-organization',
        'name': 'my-pool',
        'organization_scoped': False,
        'allowed_workspaces': ['ws-x9taqV23mxrGcDrn'],
        'id': None,
        'state': 'present'
    }
    mock_ansible_module.check_mode = False
    mock_ansible_module.fail_json = MagicMock()
    mock_ansible_module.exit_json = MagicMock()
    
    # Patch the __init__ of AnsibleModule to return our mock
    with patch.object(AnsibleModule, '__init__', return_value=None):
        with patch.object(TerraformAgentPoolModule, '__init__', return_value=None) as mock_init:
            # Create the module
            module = TerraformAgentPoolModule()
            
            # Set up the module with our mock properties
            module.params = mock_ansible_module.params
            module.check_mode = False
            module.organization = 'my-organization'
            module.name = 'my-pool'
            module.id = None
            module.state = 'present'
            module.organization_scoped = False
            module.allowed_workspaces = ['ws-x9taqV23mxrGcDrn']
            module.fail_json = mock_ansible_module.fail_json
            module.exit_json = mock_ansible_module.exit_json
            module.token = 'test-token'
            module.hostname = 'https://app.terraform.io'
            
            yield module

# Test agent pool creation
def test_create_agent_pool(agent_pool_module):
    # Mock the API requests
    with patch.object(agent_pool_module, '_get_agent_pool', return_value=None):
        with patch.object(agent_pool_module, '_create_agent_pool', return_value=AGENT_POOL_CREATE_RESPONSE):
            # Run the module
            agent_pool_module.run()
            
            # Verify exit_json was called with the right parameters
            agent_pool_module.exit_json.assert_called_once()
            call_args = agent_pool_module.exit_json.call_args[1]
            assert call_args['changed'] is True
            assert call_args['msg'] == "Agent pool 'my-pool' created successfully"
            assert 'agent_pool' in call_args
            assert call_args['agent_pool']['name'] == 'my-pool'
            assert call_args['agent_pool']['id'] == 'apool-55jZekR57npjHHYQ'

# Test agent pool update
def test_update_agent_pool(agent_pool_module):
    # Set up an agent pool that exists to be updated
    with patch.object(agent_pool_module, '_get_agent_pool', return_value=AGENT_POOL_DETAILS_RESPONSE):
        with patch.object(agent_pool_module, '_update_agent_pool', return_value=AGENT_POOL_CREATE_RESPONSE):
            # Run the module
            agent_pool_module.run()
            
            # Verify exit_json was called with the right parameters
            agent_pool_module.exit_json.assert_called_once()
            call_args = agent_pool_module.exit_json.call_args[1]
            assert call_args['changed'] is True
            assert call_args['msg'] == "Agent pool 'my-pool' updated successfully"
            assert 'agent_pool' in call_args

# Test agent pool deletion
def test_delete_agent_pool(agent_pool_module):
    # Set state to absent
    agent_pool_module.state = 'absent'
    agent_pool_module.id = 'apool-yoGUFz5zcRMMz53i'
    
    # Mock the API requests
    with patch.object(agent_pool_module, '_get_agent_pool', return_value=AGENT_POOL_DETAILS_RESPONSE):
        with patch.object(agent_pool_module, '_delete_agent_pool', return_value={"changed": True, "msg": "Agent pool 'my-pool' deleted successfully"}):
            # Run the module
            agent_pool_module.run()
            
            # Verify exit_json was called with the right parameters
            agent_pool_module.exit_json.assert_called_once()
            call_args = agent_pool_module.exit_json.call_args[1]
            assert call_args['changed'] is True
            assert call_args['msg'] == "Agent pool 'my-pool' deleted successfully"

# Test check mode for creation
def test_check_mode_create(agent_pool_module):
    # Set check mode to True
    agent_pool_module.check_mode = True
    
    # Mock the API request
    with patch.object(agent_pool_module, '_get_agent_pool', return_value=None):
        # Run the module
        agent_pool_module.run()
        
        # Verify exit_json was called with the right parameters
        agent_pool_module.exit_json.assert_called_once()
        call_args = agent_pool_module.exit_json.call_args[1]
        assert call_args['changed'] is True
        assert call_args['msg'] == "Would create agent pool 'my-pool'"

# Test check mode for update
def test_check_mode_update(agent_pool_module):
    # Set check mode to True
    agent_pool_module.check_mode = True
    
    # Mock the API request
    with patch.object(agent_pool_module, '_get_agent_pool', return_value=AGENT_POOL_DETAILS_RESPONSE):
        # Run the module
        agent_pool_module.run()
        
        # Verify exit_json was called with the right parameters
        agent_pool_module.exit_json.assert_called_once()
        call_args = agent_pool_module.exit_json.call_args[1]
        assert call_args['changed'] is True
        assert call_args['msg'] == "Would update agent pool 'my-pool'"

# Test check mode for deletion
def test_check_mode_delete(agent_pool_module):
    # Set check mode to True and state to absent
    agent_pool_module.check_mode = True
    agent_pool_module.state = 'absent'
    agent_pool_module.id = 'apool-yoGUFz5zcRMMz53i'
    
    # Mock the API request
    with patch.object(agent_pool_module, '_get_agent_pool', return_value=AGENT_POOL_DETAILS_RESPONSE):
        # Run the module
        agent_pool_module.run()
        
        # Verify exit_json was called with the right parameters
        agent_pool_module.exit_json.assert_called_once()
        call_args = agent_pool_module.exit_json.call_args[1]
        assert call_args['changed'] is True
        assert call_args['msg'] == "Would delete agent pool 'my-pool'"

# Test agent pool already exists (no op for deletion)
def test_agent_pool_already_gone(agent_pool_module):
    # Set state to absent for a non-existent agent pool
    agent_pool_module.state = 'absent'
    agent_pool_module.id = 'apool-nonexistent'
    
    # Mock the API request
    with patch.object(agent_pool_module, '_get_agent_pool', return_value=None):
        # Run the module
        agent_pool_module.run()
        
        # Verify exit_json was called with the right parameters
        agent_pool_module.exit_json.assert_called_once()
        call_args = agent_pool_module.exit_json.call_args[1]
        assert call_args['changed'] is False
        assert call_args['msg'] == "Agent pool 'my-pool' already does not exist"

# Test error handling
def test_error_handling(agent_pool_module):
    # Define a custom function that would be called by run() to handle errors properly
    def fail_json_side_effect(**kwargs):
        assert "Error managing agent pool: API Error" in kwargs.get('msg', '')
        raise Exception(kwargs.get('msg', 'API Error'))
    
    # Set up the fail_json mock to have a side effect
    agent_pool_module.fail_json.side_effect = fail_json_side_effect
    
    # Mock the API request to raise an exception
    with patch.object(agent_pool_module, '_get_agent_pool', side_effect=Exception("API Error")):
        # Run the module
        with pytest.raises(Exception) as excinfo:
            agent_pool_module.run()
        
        # Verify the error message contains our API error
        assert "Error managing agent pool" in str(excinfo.value)

# Test organization-scoped agent pool creation
def test_org_scoped_agent_pool(agent_pool_module):
    # Change to organization scoped
    agent_pool_module.organization_scoped = True
    agent_pool_module.allowed_workspaces = None
    
    # Create a modified response for an org-scoped pool
    org_scoped_response = AGENT_POOL_CREATE_RESPONSE.copy()
    org_scoped_response['data']['attributes']['organization-scoped'] = True
    
    # Remove the allowed-workspaces relationship since it's org-scoped
    if 'allowed-workspaces' in org_scoped_response['data']['relationships']:
        org_scoped_response['data']['relationships']['allowed-workspaces']['data'] = []
    
    # Mock the API requests
    with patch.object(agent_pool_module, '_get_agent_pool', return_value=None):
        with patch.object(agent_pool_module, '_create_agent_pool', return_value=org_scoped_response):
            # Run the module
            agent_pool_module.run()
            
            # Verify exit_json was called with the right parameters
            agent_pool_module.exit_json.assert_called_once()
            call_args = agent_pool_module.exit_json.call_args[1]
            assert call_args['changed'] is True
            assert 'agent_pool' in call_args
            assert call_args['agent_pool']['organization_scoped'] is True