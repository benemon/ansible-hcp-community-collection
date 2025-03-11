from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest
from unittest.mock import patch, MagicMock

from ansible_collections.benemon.hcp_community_collection.plugins.modules.hcp_terraform_project import TerraformProjectModule
from ansible.module_utils.basic import AnsibleModule

# Mock responses for Project API
PROJECT_DETAILS = {
    "id": "prj-abc123",
    "type": "projects",
    "attributes": {
        "name": "Test Project",
        "description": "Test project description",
        "created-at": "2023-04-16T20:42:53.771Z",
        "updated-at": "2023-04-16T20:42:53.771Z",
        "auto-destroy-activity-duration": "14d"
    }
}

PROJECT_LIST_RESPONSE = {
    "data": [
        PROJECT_DETAILS
    ]
}

PROJECT_DETAILS_RESPONSE = {
    "data": PROJECT_DETAILS
}

PROJECT_CREATE_RESPONSE = {
    "data": {
        "id": "prj-xyz789",
        "type": "projects",
        "attributes": {
            "name": "New Project",
            "description": "New project description",
            "created-at": "2023-04-16T20:42:53.771Z",
            "updated-at": "2023-04-16T20:42:53.771Z",
            "auto-destroy-activity-duration": "7d"
        }
    }
}

PROJECT_TAGS_RESPONSE = {
    "data": [
        {
            "type": "tag-bindings",
            "attributes": {
                "key": "environment",
                "value": "production",
                "created-at": "2023-04-16T20:42:53.771Z"
            }
        },
        {
            "type": "tag-bindings",
            "attributes": {
                "key": "department",
                "value": "infrastructure",
                "created-at": "2023-04-16T20:42:53.771Z"
            }
        }
    ]
}

# Fixture to create a mock TerraformProjectModule instance
@pytest.fixture
def project_module():
    # Create a proper mock for AnsibleModule
    mock_ansible_module = MagicMock()
    mock_ansible_module.params = {
        'token': 'test-token',
        'hostname': 'https://app.terraform.io',
        'organization': 'my-organization',
        'name': 'Test Project',
        'description': 'Test project description',
        'auto_destroy_activity_duration': '14d',
        'project_id': None,
        'tags': [
            {'key': 'environment', 'value': 'production'},
            {'key': 'department', 'value': 'infrastructure'}
        ],
        'state': 'present'
    }
    mock_ansible_module.check_mode = False
    mock_ansible_module.fail_json = MagicMock()
    mock_ansible_module.exit_json = MagicMock()
    
    # Patch the __init__ of AnsibleModule to return our mock
    with patch.object(AnsibleModule, '__init__', return_value=None):
        with patch.object(TerraformProjectModule, '__init__', return_value=None) as mock_init:
            # Create the module
            module = TerraformProjectModule()
            
            # Set up the module with our mock properties
            module.params = mock_ansible_module.params
            module.check_mode = False
            module.organization = 'my-organization'
            module.name = 'Test Project'
            module.project_id = None
            module.state = 'present'
            module.fail_json = mock_ansible_module.fail_json
            module.exit_json = mock_ansible_module.exit_json
            module.token = 'test-token'
            module.hostname = 'https://app.terraform.io'
            
            yield module

# Test project creation
def test_create_project(project_module):
    # Update params for a new project
    project_module.name = 'New Project'
    project_module.params['name'] = 'New Project'
    project_module.params['description'] = 'New project description'
    project_module.params['auto_destroy_activity_duration'] = '7d'
    
    # Mock the API requests
    with patch.object(project_module, '_get_project', return_value=None):
        with patch.object(project_module, '_create_project', return_value=PROJECT_CREATE_RESPONSE):
            with patch.object(project_module, '_get_project_tags', return_value=PROJECT_TAGS_RESPONSE['data']):
                # Run the module
                project_module.run()
                
                # Verify exit_json was called with the right parameters
                project_module.exit_json.assert_called_once()
                call_args = project_module.exit_json.call_args[1]
                assert call_args['changed'] is True
                assert call_args['msg'] == "Project 'New Project' created successfully"
                assert 'project' in call_args
                assert call_args['project']['name'] == 'New Project'

# Test project update
def test_update_project(project_module):
    # Set up a parameter that will trigger an update
    project_module.params['description'] = "Updated project description"
    
    # Mock the API requests
    with patch.object(project_module, '_get_project', return_value=PROJECT_DETAILS):
        with patch.object(project_module, '_update_project', return_value=PROJECT_DETAILS_RESPONSE):
            with patch.object(project_module, '_get_project_tags', return_value=PROJECT_TAGS_RESPONSE['data']):
                # Run the module
                project_module.run()
                
                # Verify exit_json was called with the right parameters
                project_module.exit_json.assert_called_once()
                call_args = project_module.exit_json.call_args[1]
                assert call_args['changed'] is True
                assert call_args['msg'] == "Project 'Test Project' updated successfully"
                assert 'project' in call_args

# Test project deletion
def test_delete_project(project_module):
    # Set state to absent
    project_module.state = 'absent'
    project_module.params['state'] = 'absent'
    
    # Mock the API requests
    with patch.object(project_module, '_get_project', return_value=PROJECT_DETAILS):
        with patch.object(project_module, '_delete_project', return_value={"changed": True, "msg": "Project 'Test Project' deleted successfully"}):
            # Run the module
            project_module.run()
            
            # Verify exit_json was called with the right parameters
            project_module.exit_json.assert_called_once()
            call_args = project_module.exit_json.call_args[1]
            assert call_args['changed'] is True
            assert call_args['msg'] == "Project 'Test Project' deleted successfully"

# Test check mode for creation
def test_check_mode_create(project_module):
    # Set check mode to True
    project_module.check_mode = True
    
    # Mock the API request
    with patch.object(project_module, '_get_project', return_value=None):
        # Run the module
        project_module.run()
        
        # Verify exit_json was called with the right parameters
        project_module.exit_json.assert_called_once()
        call_args = project_module.exit_json.call_args[1]
        assert call_args['changed'] is True
        assert call_args['msg'] == "Would create project 'Test Project'"

# Test check mode for update
def test_check_mode_update(project_module):
    # Set check mode to True
    project_module.check_mode = True
    
    # Mock the API request
    with patch.object(project_module, '_get_project', return_value=PROJECT_DETAILS):
        # Run the module
        project_module.run()
        
        # Verify exit_json was called with the right parameters
        project_module.exit_json.assert_called_once()
        call_args = project_module.exit_json.call_args[1]
        assert call_args['changed'] is True
        assert call_args['msg'] == "Would update project 'Test Project'"

# Test check mode for deletion
def test_check_mode_delete(project_module):
    # Set check mode to True and state to absent
    project_module.check_mode = True
    project_module.state = 'absent'
    project_module.params['state'] = 'absent'
    
    # Mock the API request
    with patch.object(project_module, '_get_project', return_value=PROJECT_DETAILS):
        # Run the module
        project_module.run()
        
        # Verify exit_json was called with the right parameters
        project_module.exit_json.assert_called_once()
        call_args = project_module.exit_json.call_args[1]
        assert call_args['changed'] is True
        assert call_args['msg'] == "Would delete project 'Test Project'"

# Test project already exists (no op)
def test_project_already_exists(project_module):
    # Set state to absent for a non-existent project
    project_module.state = 'absent'
    project_module.params['state'] = 'absent'
    
    # Mock the API request
    with patch.object(project_module, '_get_project', return_value=None):
        # Run the module
        project_module.run()
        
        # Verify exit_json was called with the right parameters
        project_module.exit_json.assert_called_once()
        call_args = project_module.exit_json.call_args[1]
        assert call_args['changed'] is False
        assert call_args['msg'] == "Project 'Test Project' already does not exist"

# Test getting project by ID
def test_get_project_by_id(project_module):
    # Set up project_id
    project_module.project_id = 'prj-abc123'
    project_module.params['project_id'] = 'prj-abc123'
    project_module.name = None
    project_module.params['name'] = None
    
    # Mock the API requests
    with patch.object(project_module, '_get_project_by_id', return_value=PROJECT_DETAILS) as mock_get_by_id:
        project = project_module._get_project()
        
        # Verify that _get_project_by_id was called and returned the project
        mock_get_by_id.assert_called_once()
        assert project == PROJECT_DETAILS

# Test getting project by name
def test_get_project_by_name(project_module):
    # Ensure project_id is None
    project_module.project_id = None
    project_module.params['project_id'] = None
    
    # Mock the API requests
    with patch.object(project_module, '_get_project_by_name', return_value=PROJECT_DETAILS) as mock_get_by_name:
        project = project_module._get_project()
        
        # Verify that _get_project_by_name was called and returned the project
        mock_get_by_name.assert_called_once()
        assert project == PROJECT_DETAILS

# Test error handling
def test_error_handling(project_module):
    # Define a custom function that would be called by run() to handle errors properly
    def fail_json_side_effect(**kwargs):
        assert "Error managing project: API Error" in kwargs.get('msg', '')
        raise Exception(kwargs.get('msg', 'API Error'))
    
    # Set up the fail_json mock to have a side effect
    project_module.fail_json.side_effect = fail_json_side_effect
    
    # Mock the API request to raise an exception
    with patch.object(project_module, '_get_project', side_effect=Exception("API Error")):
        # Run the module
        with pytest.raises(Exception) as excinfo:
            project_module.run()
        
        # Verify the error message contains our API error
        assert "Error managing project" in str(excinfo.value)