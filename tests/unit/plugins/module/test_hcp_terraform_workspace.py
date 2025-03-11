from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest
from unittest.mock import patch, MagicMock

from ansible_collections.benemon.hcp_community_collection.plugins.modules.hcp_terraform_workspace import TerraformWorkspaceModule
from ansible.module_utils.basic import AnsibleModule

# Mock responses for Workspace API
WORKSPACE_LIST_RESPONSE = {
    "data": [
        {
            "id": "ws-123456",
            "type": "workspaces",
            "attributes": {
                "name": "test-workspace",
                "description": "Test workspace description",
                "execution-mode": "remote",
                "terraform-version": "1.5.0",
                "working-directory": "",
                "auto-apply": False,
                "created-at": "2023-04-16T20:42:53.771Z",
                "updated-at": "2023-04-16T20:42:53.771Z",
                "speculative-enabled": True,
                "global-remote-state": False,
                "vcs-repo": {
                    "identifier": "org/repo",
                    "branch": "main",
                    "oauth-token-id": "ot-123456",
                    "ingress-submodules": False
                }
            },
            "relationships": {
                "organization": {
                    "data": {
                        "id": "my-organization",
                        "type": "organizations"
                    }
                },
                "project": {
                    "data": {
                        "id": "prj-123456",
                        "type": "projects"
                    }
                }
            }
        }
    ]
}

WORKSPACE_DETAILS_RESPONSE = {
    "data": {
        "id": "ws-123456",
        "type": "workspaces",
        "attributes": {
            "name": "test-workspace",
            "description": "Test workspace description",
            "execution-mode": "remote",
            "terraform-version": "1.5.0",
            "working-directory": "",
            "auto-apply": False,
            "created-at": "2023-04-16T20:42:53.771Z",
            "updated-at": "2023-04-16T20:42:53.771Z",
            "speculative-enabled": True,
            "global-remote-state": False,
            "vcs-repo": {
                "identifier": "org/repo",
                "branch": "main",
                "oauth-token-id": "ot-123456",
                "ingress-submodules": False
            }
        },
        "relationships": {
            "organization": {
                "data": {
                    "id": "my-organization",
                    "type": "organizations"
                }
            },
            "project": {
                "data": {
                    "id": "prj-123456",
                    "type": "projects"
                }
            }
        }
    }
}

WORKSPACE_CREATE_RESPONSE = {
    "data": {
        "id": "ws-123456",
        "type": "workspaces",
        "attributes": {
            "name": "test-workspace",
            "description": "New workspace",
            "execution-mode": "remote",
            "terraform-version": "1.5.0",
            "working-directory": "",
            "auto-apply": False,
            "created-at": "2023-04-16T20:42:53.771Z",
            "updated-at": "2023-04-16T20:42:53.771Z",
            "speculative-enabled": True,
            "global-remote-state": False,
            "vcs-repo": {
                "identifier": "org/repo",
                "branch": "main",
                "oauth-token-id": "ot-123456",
                "ingress-submodules": False
            }
        },
        "relationships": {
            "organization": {
                "data": {
                    "id": "my-organization",
                    "type": "organizations"
                }
            },
            "project": {
                "data": {
                    "id": "prj-123456",
                    "type": "projects"
                }
            }
        }
    }
}

# Fixture to create a mock TerraformWorkspaceModule instance
@pytest.fixture
def workspace_module():
    # Create a proper mock for AnsibleModule
    mock_ansible_module = MagicMock()
    mock_ansible_module.params = {
        'token': 'test-token',
        'hostname': 'https://app.terraform.io',
        'organization': 'my-organization',
        'name': 'test-workspace',
        'description': 'New workspace',
        'project_id': 'prj-123456',
        'execution_mode': 'remote',
        'auto_apply': False,
        'terraform_version': '1.5.0',
        'working_directory': '',
        'vcs_repo': {
            'oauth_token_id': 'ot-123456',
            'identifier': 'org/repo',
            'branch': 'main',
            'ingress_submodules': False
        },
        'speculative_enabled': True,
        'global_remote_state': False,
        'state': 'present',
        'wait_for_creation': True,
        'timeout': 300
    }
    mock_ansible_module.check_mode = False
    mock_ansible_module.fail_json = MagicMock()
    mock_ansible_module.exit_json = MagicMock()
    
    # Patch the __init__ of AnsibleModule to return our mock
    with patch.object(AnsibleModule, '__init__', return_value=None):
        with patch.object(TerraformWorkspaceModule, '__init__', return_value=None) as mock_init:
            # Create the module
            module = TerraformWorkspaceModule()
            
            # Set up the module with our mock properties
            module.params = mock_ansible_module.params
            module.check_mode = False
            module.organization = 'my-organization'
            module.name = 'test-workspace'
            module.state = 'present'
            module.wait_for_creation = True
            module.timeout = 300
            module.fail_json = mock_ansible_module.fail_json
            module.exit_json = mock_ansible_module.exit_json
            module.token = 'test-token'
            module.hostname = 'https://app.terraform.io'
            
            yield module

# Test workspace creation
def test_create_workspace(workspace_module):
    # Mock the API requests
    with patch.object(workspace_module, '_get_workspace', return_value=None):
        with patch.object(workspace_module, '_create_workspace', return_value=WORKSPACE_CREATE_RESPONSE):
            with patch.object(workspace_module, '_wait_for_workspace', return_value=WORKSPACE_CREATE_RESPONSE):
                # Run the module
                workspace_module.run()
                
                # Verify exit_json was called with the right parameters
                workspace_module.exit_json.assert_called_once()
                call_args = workspace_module.exit_json.call_args[1]
                assert call_args['changed'] is True
                assert call_args['msg'] == "Workspace 'test-workspace' created successfully"
                assert 'workspace' in call_args
                assert call_args['workspace']['name'] == 'test-workspace'

# Test workspace update
def test_update_workspace(workspace_module):
    # Set up a parameter that will trigger an update
    workspace_module.params['description'] = "Updated workspace description"
    
    # Mock the API requests
    with patch.object(workspace_module, '_get_workspace', return_value=WORKSPACE_DETAILS_RESPONSE):
        with patch.object(workspace_module, '_update_workspace', return_value=WORKSPACE_CREATE_RESPONSE):
            # Run the module
            workspace_module.run()
            
            # Verify exit_json was called with the right parameters
            workspace_module.exit_json.assert_called_once()
            call_args = workspace_module.exit_json.call_args[1]
            assert call_args['changed'] is True
            assert call_args['msg'] == "Workspace 'test-workspace' updated successfully"
            assert 'workspace' in call_args

# Test workspace deletion
def test_delete_workspace(workspace_module):
    # Set state to absent
    workspace_module.state = 'absent'
    
    # Mock the API requests
    with patch.object(workspace_module, '_get_workspace', return_value=WORKSPACE_DETAILS_RESPONSE):
        with patch.object(workspace_module, '_delete_workspace', return_value={"changed": True, "msg": "Workspace 'test-workspace' deleted successfully"}):
            # Run the module
            workspace_module.run()
            
            # Verify exit_json was called with the right parameters
            workspace_module.exit_json.assert_called_once()
            call_args = workspace_module.exit_json.call_args[1]
            assert call_args['changed'] is True
            assert call_args['msg'] == "Workspace 'test-workspace' deleted successfully"

# Test check mode for creation
def test_check_mode_create(workspace_module):
    # Set check mode to True
    workspace_module.check_mode = True
    
    # Mock the API request
    with patch.object(workspace_module, '_get_workspace', return_value=None):
        # Run the module
        workspace_module.run()
        
        # Verify exit_json was called with the right parameters
        workspace_module.exit_json.assert_called_once()
        call_args = workspace_module.exit_json.call_args[1]
        assert call_args['changed'] is True
        assert call_args['msg'] == "Would create workspace 'test-workspace'"

# Test check mode for update
def test_check_mode_update(workspace_module):
    # Set check mode to True
    workspace_module.check_mode = True
    
    # Mock the API request
    with patch.object(workspace_module, '_get_workspace', return_value=WORKSPACE_DETAILS_RESPONSE):
        # Run the module
        workspace_module.run()
        
        # Verify exit_json was called with the right parameters
        workspace_module.exit_json.assert_called_once()
        call_args = workspace_module.exit_json.call_args[1]
        assert call_args['changed'] is True
        assert call_args['msg'] == "Would update workspace 'test-workspace'"

# Test check mode for deletion
def test_check_mode_delete(workspace_module):
    # Set check mode to True and state to absent
    workspace_module.check_mode = True
    workspace_module.state = 'absent'
    
    # Mock the API request
    with patch.object(workspace_module, '_get_workspace', return_value=WORKSPACE_DETAILS_RESPONSE):
        # Run the module
        workspace_module.run()
        
        # Verify exit_json was called with the right parameters
        workspace_module.exit_json.assert_called_once()
        call_args = workspace_module.exit_json.call_args[1]
        assert call_args['changed'] is True
        assert call_args['msg'] == "Would delete workspace 'test-workspace'"

# Test workspace already exists (no op)
def test_workspace_already_exists(workspace_module):
    # Set state to absent for a non-existent workspace
    workspace_module.state = 'absent'
    
    # Mock the API request
    with patch.object(workspace_module, '_get_workspace', return_value=None):
        # Run the module
        workspace_module.run()
        
        # Verify exit_json was called with the right parameters
        workspace_module.exit_json.assert_called_once()
        call_args = workspace_module.exit_json.call_args[1]
        assert call_args['changed'] is False
        assert call_args['msg'] == "Workspace 'test-workspace' already does not exist"

# Test error handling
def test_error_handling(workspace_module):
    # Define a custom function that would be called by run() to handle errors properly
    def fail_json_side_effect(**kwargs):
        assert "Error managing workspace: API Error" in kwargs.get('msg', '')
        raise Exception(kwargs.get('msg', 'API Error'))
    
    # Set up the fail_json mock to have a side effect
    workspace_module.fail_json.side_effect = fail_json_side_effect
    
    # Mock the API request to raise an exception
    with patch.object(workspace_module, '_get_workspace', side_effect=Exception("API Error")):
        # Run the module
        with pytest.raises(Exception) as excinfo:
            workspace_module.run()
        
        # Verify the error message contains our API error
        assert "Error managing workspace" in str(excinfo.value)

# Test VCS repository handling
def test_workspace_with_vcs_repo(workspace_module):
    # Set vcs_repo parameters
    workspace_module.params['vcs_repo'] = {
        'oauth_token_id': 'ot-newtoken',
        'identifier': 'org/new-repo',
        'branch': 'develop',
        'ingress_submodules': True
    }
    
    # Create a mock response with the new VCS settings
    updated_response = WORKSPACE_CREATE_RESPONSE.copy()
    updated_response['data']['attributes']['vcs-repo'] = {
        'identifier': 'org/new-repo',
        'branch': 'develop',
        'oauth-token-id': 'ot-newtoken',
        'ingress-submodules': True
    }
    
    # Mock the API requests
    with patch.object(workspace_module, '_get_workspace', return_value=None):
        with patch.object(workspace_module, '_create_workspace', return_value=updated_response):
            with patch.object(workspace_module, '_wait_for_workspace', return_value=updated_response):
                # Run the module
                workspace_module.run()
                
                # Verify exit_json was called and VCS repo details are in the response
                workspace_module.exit_json.assert_called_once()
                call_args = workspace_module.exit_json.call_args[1]
                assert 'workspace' in call_args
                assert 'vcs_repo' in call_args['workspace']
                assert call_args['workspace']['vcs_repo']['identifier'] == 'org/new-repo'
                assert call_args['workspace']['vcs_repo']['branch'] == 'develop'

# Test agent execution mode
def test_workspace_with_agent_execution(workspace_module):
    # Set execution mode to agent and provide an agent pool ID
    workspace_module.params['execution_mode'] = 'agent'
    workspace_module.params['agent_pool_id'] = 'apool-123456'
    
    # Create a mock response with agent settings
    agent_response = WORKSPACE_CREATE_RESPONSE.copy()
    agent_response['data']['attributes']['execution-mode'] = 'agent'
    agent_response['data']['attributes']['agent-pool-id'] = 'apool-123456'
    
    # Mock the API requests
    with patch.object(workspace_module, '_get_workspace', return_value=None):
        with patch.object(workspace_module, '_create_workspace', return_value=agent_response):
            with patch.object(workspace_module, '_wait_for_workspace', return_value=agent_response):
                # Run the module
                workspace_module.run()
                
                # Verify exit_json was called and execution mode is set to agent
                workspace_module.exit_json.assert_called_once()
                call_args = workspace_module.exit_json.call_args[1]
                assert 'workspace' in call_args
                assert call_args['workspace']['execution_mode'] == 'agent'