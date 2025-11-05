# imports from ../odin_sdk/__init__.py
# main wrapper to make the SDK more elegant

import sys
import os

# Add parent directory to path to import odin_sdk
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import odin_sdk
from odin_sdk.rest import ApiException
from typing import Optional, Dict, Any, List, Union
import json


class OdinWrapper:
    """
    Elegant wrapper for the Odin SDK that provides clean, intuitive API access.
    
    Features:
    - Normalized method names (no more ugly auto-generated names)
    - Automatic authentication handling
    - Domain-specific managers for organization
    - Direct method access with *args/**kwargs for future-proofing
    - Consistent error handling
    """
    
    def __init__(self, api_key: str, api_secret: str, host: str = "http://localhost:8001"):
        """Initialize the wrapper with credentials and host."""
        self.api_key = api_key
        self.api_secret = api_secret
        self.host = host
        
        # Initialize configuration
        self.configuration = odin_sdk.Configuration(host=host)
        self.api_client = odin_sdk.ApiClient(self.configuration)
        
        # Set authentication headers
        self.api_client.default_headers["x-api-key"] = api_key
        self.api_client.default_headers["x-api-secret"] = api_secret
        
        # Initialize all API instances
        self._agents_api = odin_sdk.AgentsApi(self.api_client)
        self._chat_api = odin_sdk.ChatApi(self.api_client)
        self._data_types_api = odin_sdk.DataTypesApi(self.api_client)
        self._jsons_api = odin_sdk.JsonsApi(self.api_client)
        self._kb_api = odin_sdk.KnowledgeBaseApi(self.api_client)
        self._projects_api = odin_sdk.ProjectsApi(self.api_client)
        self._roles_api = odin_sdk.RolesApi(self.api_client)
        
        # Method mapping for clean names
        self._method_map = {
            # Projects API
            'project_create': ('_projects_api', 'create_project_project_create_post'),
            'project_delete': ('_projects_api', 'delete_project_project_delete_delete'),
            'project_update': ('_projects_api', 'update_project_project_update_post'),
            'project_list': ('_projects_api', 'get_projects_projects_get'),
            'project_get_members': ('_projects_api', 'get_project_members_project_project_id_members_get'),
            'project_add_user': ('_projects_api', 'add_user_to_project_project_user_add_post'),
            'project_edit_user': ('_projects_api', 'edit_project_user_project_user_edit_post'),
            
            # Agents API
            'agent_create': ('_agents_api', 'save_new_custom_agent_agents_new_post'),
            'agent_edit': ('_agents_api', 'edit_existing_custom_agent_agents_edit_post'),
            'agent_activate': ('_agents_api', 'activate_custom_agent_agents_activate_post'),
            'agent_list': ('_agents_api', 'list_agents_for_project_agents_project_id_list_get'),
            
            # Chat API
            'chat_create': ('_chat_api', 'create_chat_chat_create_post'),
            'chat_delete': ('_chat_api', 'delete_chat_chat_delete_delete'),
            'chat_get': ('_chat_api', 'get_chat_project_project_id_chat_chat_id_get'),
            'chat_list': ('_chat_api', 'get_chats_project_project_id_chat_get'),
            'chat_send_message': ('_chat_api', 'send_message_v3_v3_chat_message_post'),
            'chat_get_models': ('_chat_api', 'get_default_models_chat_models_get'),
            
            # Data Types API
            'data_create': ('_data_types_api', 'create_data_type_project_project_id_data_types_post'),
            'data_delete': ('_data_types_api', 'delete_data_type_by_id_project_project_id_data_types_data_type_id_delete'),
            'data_get': ('_data_types_api', 'get_data_type_by_id_project_project_id_data_types_data_type_id_get'),
            'data_list': ('_data_types_api', 'get_data_types_project_project_id_data_types_get'),
            'data_import_table': ('_data_types_api', 'import_table_project_project_id_import_table_post'),
            'data_create_view': ('_data_types_api', 'create_data_type_view_project_project_id_data_type_data_type_id_view_post'),
            'data_get_view': ('_data_types_api', 'get_data_type_view_by_id_project_project_id_data_types_data_type_id_view_get'),
            'data_get_grouped_view': ('_data_types_api', 'get_grouped_data_type_view_by_id_project_project_id_data_types_data_type_id_view_grouped_get'),
            'data_update_view': ('_data_types_api', 'update_data_type_view_project_project_id_data_type_data_type_id_view_view_id_put'),
            'data_compute_column': ('_data_types_api', 'compute_column_values_async_project_project_id_data_type_data_type_id_compute_column_async_post'),
            'data_cancel_compute': ('_data_types_api', 'cancel_compute_column_job_project_project_id_data_type_data_type_id_compute_column_cancel_execution_id_post'),
            'data_get_compute_status': ('_data_types_api', 'get_compute_column_status_project_project_id_data_type_data_type_id_compute_column_status_execution_id_get'),
            'data_get_compute_jobs': ('_data_types_api', 'get_compute_column_jobs_project_project_id_data_type_data_type_id_compute_column_jobs_get'),
            'data_get_templates': ('_data_types_api', 'get_templates_project_project_id_data_type_templates_get'),
            'data_get_template_details': ('_data_types_api', 'get_template_details_project_project_id_data_type_templates_template_name_get'),
            'data_use_template': ('_data_types_api', 'use_template_project_project_id_data_type_templates_use_post'),
            
            # Knowledge Base API
            'kb_add_file': ('_kb_api', 'add_file_to_knowledge_base_v3_v3_project_knowledge_add_file_post'),
            'kb_sync_file': ('_kb_api', 'sync_kb_file_v2_v2_project_knowledge_sync_file_post'),
            'kb_batch_delete': ('_kb_api', 'batch_delete_project_knowledge_delete_delete'),
            
            # JSON API
            'json_get': ('_jsons_api', 'get_json_json_post'),
            'json_get_multiple': ('_jsons_api', 'get_jsons_jsons_post'),
            'json_edit': ('_jsons_api', 'edit_json_json_put'),
            'json_delete': ('_jsons_api', 'delete_json_json_delete'),
            
            # Roles API
            'role_create': ('_roles_api', 'create_role_project_project_id_roles_post'),
            'role_list': ('_roles_api', 'get_all_role_ids_project_project_id_roles_get'),
        }
    
    def __getattr__(self, name: str):
        """Dynamic method resolution for clean API access."""
        if name in self._method_map:
            api_name, method_name = self._method_map[name]
            api_instance = getattr(self, api_name)
            original_method = getattr(api_instance, method_name)
            
            def wrapper(*args, **kwargs):
                try:
                    return original_method(*args, **kwargs)
                except ApiException as e:
                    raise OdinError(f"API call failed: {e}")
                except Exception as e:
                    raise OdinError(f"Unexpected error: {e}")
            
            return wrapper
        
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
    
    def call(self, operation: str, *args, **kwargs):
        """
        Direct operation calling with path-style access.
        
        Example:
            wrapper.call("project_create", create_project_request=request)
        """
        if hasattr(self, operation):
            return getattr(self, operation)(*args, **kwargs)
        else:
            raise OdinError(f"Unknown operation: {operation}")
    
    # Domain-specific managers for organized access
    def projects(self) -> 'ProjectManager':
        """Get the project management interface."""
        return ProjectManager(self)
    
    def agents(self) -> 'AgentManager':
        """Get the agent management interface."""
        return AgentManager(self)
    
    def chats(self) -> 'ChatManager':
        """Get the chat management interface."""
        return ChatManager(self)
    
    def data(self) -> 'DataManager':
        """Get the data management interface."""
        return DataManager(self)
    
    def knowledge(self) -> 'KnowledgeManager':
        """Get the knowledge base management interface."""
        return KnowledgeManager(self)
    
    def roles(self) -> 'RoleManager':
        """Get the role management interface."""
        return RoleManager(self)
    
    def json_store(self) -> 'JsonManager':
        """Get the JSON store management interface."""
        return JsonManager(self)


class OdinError(Exception):
    """Custom exception for Odin wrapper errors."""
    pass


class BaseManager:
    """Base class for all domain managers."""
    
    def __init__(self, wrapper: OdinWrapper):
        self.wrapper = wrapper


class ProjectManager(BaseManager):
    """Project management operations."""
    
    def create(self, name: str, description: str = "", project_type: str = "kb_chat", *args, **kwargs):
        """Create a new project."""
        request = odin_sdk.CreateProjectRequest(
            project_name=name,
            project_description=description,
            project_type=project_type
        )
        return self.wrapper.project_create(create_project_request=request, *args, **kwargs)
    
    def delete(self, project_id: str, *args, **kwargs):
        """Delete a project."""
        request = odin_sdk.DeleteProjectRequest(project_id=project_id)
        return self.wrapper.project_delete(delete_project_request=request, *args, **kwargs)
    
    def update(self, project_id: str, name: str = None, description: str = None, *args, **kwargs):
        """Update a project."""
        request = odin_sdk.UpdateProjectRequest(project_id=project_id)
        if name:
            request.project_name = name
        if description:
            request.project_description = description
        return self.wrapper.project_update(update_project_request=request, *args, **kwargs)
    
    def list(self, limit: int = None, offset: int = None, *args, **kwargs):
        """List all projects."""
        return self.wrapper.project_list(limit=limit, offset=offset, *args, **kwargs)
    
    def get_members(self, project_id: str, *args, **kwargs):
        """Get project members."""
        return self.wrapper.project_get_members(project_id=project_id, *args, **kwargs)
    
    def add_user(self, project_id: str, user_email: str, role: str = "viewer", *args, **kwargs):
        """Add user to project."""
        request = odin_sdk.AddUserToProjectRequest(
            project_id=project_id,
            user_email=user_email,
            role=role
        )
        return self.wrapper.project_add_user(add_user_to_project_request=request, *args, **kwargs)


class AgentManager(BaseManager):
    """Agent management operations."""
    
    def create(self, project_id: str, name: str = "Untitled Agent", 
               personality: str = "You are a helpful assistant.", 
               building_blocks: List[Dict] = None, temperature: float = 0.0,
               *args, **kwargs):
        """
        Create a new agent - completely thin wrapper.
        
        Args:
            project_id: The project ID
            name: Agent name  
            personality: Agent personality/instructions
            building_blocks: Complete building blocks configuration (pass whatever you want)
            temperature: Model temperature
            *args, **kwargs: Future-proof parameter passing
        """
        
        request = odin_sdk.SaveNewCustomAgent(
            project_id=project_id,
            agent_name=name,
            personality=personality,
            building_blocks=building_blocks,
            temperature=temperature,
            mask_urls=True
        )
        return self.wrapper.agent_create(request, *args, **kwargs)
    
    def edit(self, agent_id: str, project_id: str, name: str = None, 
             personality: str = None, building_blocks: List[Dict] = None,
             temperature: float = None, *args, **kwargs):
        """Edit an existing agent."""
        request = odin_sdk.EditExistingCustomAgent(
            agent_id=agent_id,
            project_id=project_id
        )
        if name:
            request.agent_name = name
        if personality:
            request.personality = personality
        if building_blocks:
            request.building_blocks = building_blocks
        if temperature is not None:
            request.temperature = temperature
            
        return self.wrapper.agent_edit(request, *args, **kwargs)
    
    def activate(self, project_id: str, agent_id: str, *args, **kwargs):
        """Activate an agent."""
        request = odin_sdk.RoutesProjectsActivateCustomAgentRequest(
            project_id=project_id,
            agent_id=agent_id
        )
        return self.wrapper.agent_activate(request, *args, **kwargs)
    
    def list(self, project_id: str, *args, **kwargs):
        """List agents for a project."""
        return self.wrapper.agent_list(project_id=project_id, *args, **kwargs)


class ChatManager(BaseManager):
    """Chat management operations."""
    
    def create(self, project_id: str, name: str, context: str = "", *args, **kwargs):
        """Create a new chat."""
        request = odin_sdk.CreateChatPromptRequest(
            project_id=project_id,
            name=name,
            context=context
        )
        return self.wrapper.chat_create(request, *args, **kwargs)
    
    def delete(self, chat_id: str, project_id: str, *args, **kwargs):
        """Delete a chat."""
        request = odin_sdk.DeleteChatRequest(chat_id=chat_id, project_id=project_id)
        return self.wrapper.chat_delete(request, *args, **kwargs)
    
    def get(self, chat_id: str, project_id: str, prompt_debug: bool = False, *args, **kwargs):
        """Get a specific chat."""
        return self.wrapper.chat_get(
            chat_id=chat_id, 
            project_id=project_id, 
            prompt_debug=prompt_debug, 
            *args, **kwargs
        )
    
    def list(self, project_id: str, cursor: float = None, limit: int = 30, 
             user_id: str = None, *args, **kwargs):
        """List chats for a project."""
        return self.wrapper.chat_list(
            project_id=project_id,
            cursor=cursor,
            limit=limit,
            user_id=user_id,
            *args, **kwargs
        )
    
    def send_message(self, message: str, project_id: str, chat_id: str = None,
                     skip_stream: bool = True, *args, **kwargs):
        """Send a message to a chat."""
        return self.wrapper.chat_send_message(
            message=message,
            project_id=project_id,
            chat_id=chat_id,
            skip_stream=skip_stream,
            *args, **kwargs
        )
    
    def get_models(self, *args, **kwargs):
        """Get available chat models."""
        return self.wrapper.chat_get_models(*args, **kwargs)


class DataManager(BaseManager):
    """Data management operations."""
    
    def create(self, project_id: str, title: str, description: str = "", 
               schema: List[Dict] = None, *args, **kwargs):
        """Create a new data type."""
        request = odin_sdk.RoutesDataTypesAddDataTypeRequest(
            project_id=project_id,
            title=title,
            description=description
        )
        if schema:
            request.schema = schema
        return self.wrapper.data_create(project_id=project_id, 
                                      routes_data_types_add_data_type_request=request, 
                                      *args, **kwargs)
    
    def delete(self, project_id: str, data_type_id: str, *args, **kwargs):
        """Delete a data type."""
        return self.wrapper.data_delete(project_id=project_id, 
                                      data_type_id=data_type_id, 
                                      *args, **kwargs)
    
    def get(self, project_id: str, data_type_id: str, *args, **kwargs):
        """Get a specific data type."""
        return self.wrapper.data_get(project_id=project_id, 
                                   data_type_id=data_type_id, 
                                   *args, **kwargs)
    
    def list(self, project_id: str, sent_internally: bool = None, *args, **kwargs):
        """List data types for a project."""
        return self.wrapper.data_list(project_id=project_id, 
                                    sent_internally=sent_internally, 
                                    *args, **kwargs)
    
    def import_table(self, project_id: str, title: str, description: str,
                     file_path: str, column_mappings: Union[Dict, str],
                     delimiter: str = ",", *args, **kwargs):
        """Import a table from CSV/Excel file."""
        with open(file_path, 'rb') as f:
            file_content = f.read()
            
        if isinstance(column_mappings, dict):
            column_mappings = json.dumps(column_mappings)
            
        return self.wrapper.data_import_table(
            project_id=project_id,
            title=title,
            description=description,
            column_mappings=column_mappings,
            file=(file_path.split("/")[-1], file_content),
            delimiter=delimiter,
            *args, **kwargs
        )
    
    def create_view(self, project_id: str, data_type_id: str, view_config: Dict,
                    *args, **kwargs):
        """Create a view for a data type."""
        request = odin_sdk.CreateViewRequest(**view_config)
        return self.wrapper.data_create_view(
            project_id=project_id,
            data_type_id=data_type_id,
            create_view_request=request,
            *args, **kwargs
        )
    
    def get_view(self, project_id: str, data_type_id: str, *args, **kwargs):
        """Get a data type view."""
        return self.wrapper.data_get_view(
            project_id=project_id,
            data_type_id=data_type_id,
            *args, **kwargs
        )


class KnowledgeManager(BaseManager):
    """Knowledge base management operations."""
    
    def add_file(self, project_id: str, file_path: str, metadata: Dict = None,
                 file_type: str = None, force: bool = None, path: str = "/",
                 *args, **kwargs):
        """Add a file to the knowledge base."""
        with open(file_path, 'rb') as f:
            file_content = f.read()
            
        if metadata is None:
            metadata = {}
            
        return self.wrapper.kb_add_file(
            file=(file_path.split("/")[-1], file_content),
            project_id=project_id,
            metadata=metadata,
            file_type=file_type,
            force=force,
            path=path,
            *args, **kwargs
        )
    
    def sync_file(self, request_data: Dict, *args, **kwargs):
        """Sync a file to the knowledge base."""
        request = odin_sdk.SyncFileRequest(**request_data)
        return self.wrapper.kb_sync_file(sync_file_request=request, *args, **kwargs)
    
    def batch_delete(self, delete_data: Dict, *args, **kwargs):
        """Batch delete knowledge base items."""
        request = odin_sdk.BatchDeleteRequest(**delete_data)
        return self.wrapper.kb_batch_delete(batch_delete_request=request, *args, **kwargs)


class RoleManager(BaseManager):
    """Role management operations."""
    
    def create(self, project_id: str, role_name: str, permissions: List[str] = None,
               sent_internally: bool = False, *args, **kwargs):
        """Create a new role."""
        request = odin_sdk.CreateRoleRequest(
            project_id=project_id,
            role_name=role_name
        )
        if permissions:
            request.permissions = permissions
            
        return self.wrapper.role_create(
            project_id=project_id,
            create_role_request=request,
            sent_internally=sent_internally,
            *args, **kwargs
        )
    
    def list(self, project_id: str, *args, **kwargs):
        """List all roles for a project."""
        return self.wrapper.role_list(project_id=project_id, *args, **kwargs)


class JsonManager(BaseManager):
    """JSON store management operations."""
    
    def get(self, request_data: Dict, *args, **kwargs):
        """Get JSON data."""
        request = odin_sdk.GetJsonRequest(**request_data)
        return self.wrapper.json_get(get_json_request=request, *args, **kwargs)
    
    def get_multiple(self, request_data: Dict, *args, **kwargs):
        """Get multiple JSON items."""
        request = odin_sdk.GetJsonsRequest(**request_data)
        return self.wrapper.json_get_multiple(get_jsons_request=request, *args, **kwargs)
    
    def edit(self, request_data: Dict, *args, **kwargs):
        """Edit JSON data."""
        request = odin_sdk.UpdateJsonRequest(**request_data)
        return self.wrapper.json_edit(update_json_request=request, *args, **kwargs)
    
    def delete(self, request_data: Dict, *args, **kwargs):
        """Delete JSON data."""
        request = odin_sdk.DeleteJsonRequest(**request_data)
        return self.wrapper.json_delete(delete_json_request=request, *args, **kwargs)



# Convenience factory function
def create_client(api_key: str, api_secret: str, host: str = "http://localhost:8001") -> OdinWrapper:
    """
    Create an OdinWrapper client instance.
    
    Args:
        api_key: Your Odin API key
        api_secret: Your Odin API secret  
        host: API host URL (default: http://localhost:8001)
        
    Returns:
        OdinWrapper instance ready for use
        
    Example:
        client = create_client("your-key", "your-secret")
        
        # Domain-specific access
        project = client.projects().create("My Project", "Description")
        
        # Direct method access  
        response = client.project_create(create_project_request=request)
        
        # Dynamic operation calling
        result = client.call("project_create", create_project_request=request)
    """
    return OdinWrapper(api_key, api_secret, host)


# Export main classes and factory
__all__ = [
    'OdinWrapper',
    'OdinError', 
    'ProjectManager',
    'AgentManager',
    'ChatManager', 
    'DataManager',
    'KnowledgeManager',
    'RoleManager',
    'JsonManager',
    'create_client'
]