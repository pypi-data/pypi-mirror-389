"""
Odin SDK v3 - Enhanced wrapper with improved resource objects and convenience methods.

This wrapper improves upon v2 by:
- Flattening nested response objects (no more project.project.id)
- Adding convenience methods to resources (project.delete() instead of client.projects().delete(id))
- Maintaining full compatibility with v2 manager patterns
- Providing better developer experience while keeping the same API surface
"""

from typing import Dict, List, Union, Optional, Any
import json
from ..v2 import OdinWrapper as V2Wrapper, OdinError


class ResourceBase:
    """Base class for all resource objects with enhanced convenience methods."""
    
    def __init__(self, client: 'OdinClient', raw_response: Any):
        self._client = client
        self._raw = raw_response
        self._extract_attributes()
    
    def _extract_attributes(self):
        """Extract and flatten attributes from nested response objects."""
        if hasattr(self._raw, '__dict__'):
            for key, value in self._raw.__dict__.items():
                if hasattr(value, '__dict__') and not key.startswith('_'):
                    # Flatten nested objects (e.g., project.project -> project)
                    nested_attrs = value.__dict__
                    for nested_key, nested_value in nested_attrs.items():
                        if not nested_key.startswith('_'):
                            setattr(self, nested_key, nested_value)
                else:
                    if not key.startswith('_'):
                        setattr(self, key, value)


class Project(ResourceBase):
    """Enhanced project resource with convenience methods."""
    
    def delete(self):
        """Delete this project."""
        return self._client.projects().delete(self.id)
    
    def update(self, name: str = None, description: str = None, **kwargs):
        """Update this project."""
        return self._client.projects().update(self.id, name=name, description=description, **kwargs)
    
    def get_members(self):
        """Get members of this project."""
        return self._client.projects().get_members(self.id)
    
    def add_user(self, user_email: str, role: str = "viewer", **kwargs):
        """Add a user to this project."""
        return self._client.projects().add_user(self.id, user_email, role, **kwargs)
    
    @property
    def agents(self):
        """Get agent manager scoped to this project."""
        return ProjectScopedAgentManager(self._client, self.id)
    
    @property
    def chats(self):
        """Get chat manager scoped to this project."""
        return ProjectScopedChatManager(self._client, self.id)
    
    @property
    def data(self):
        """Get data manager scoped to this project."""
        return ProjectScopedDataManager(self._client, self.id)
    
    @property
    def knowledge(self):
        """Get knowledge manager scoped to this project."""
        return ProjectScopedKnowledgeManager(self._client, self.id)


class Agent(ResourceBase):
    """Enhanced agent resource with convenience methods."""
    
    def activate(self):
        """Activate this agent."""
        if hasattr(self, 'project_id'):
            return self._client.agents().activate(self.project_id, self.agent_id)
        else:
            raise ValueError("Agent must have project_id to activate")
    
    def edit(self, name: str = None, personality: str = None, building_blocks: List[Dict] = None, 
             temperature: float = None, **kwargs):
        """Edit this agent."""
        if hasattr(self, 'project_id'):
            return self._client.agents().edit(
                self.agent_id, self.project_id, name=name, personality=personality,
                building_blocks=building_blocks, temperature=temperature, **kwargs
            )
        else:
            raise ValueError("Agent must have project_id to edit")


class Chat(ResourceBase):
    """Enhanced chat resource with convenience methods."""
    
    def delete(self):
        """Delete this chat."""
        if hasattr(self, 'project_id'):
            return self._client.chats().delete(self.chat_id, self.project_id)
        else:
            raise ValueError("Chat must have project_id to delete")
    
    def send_message(self, message: str, skip_stream: bool = True, **kwargs):
        """Send a message to this chat."""
        if hasattr(self, 'project_id'):
            return self._client.chats().send_message(
                message, self.project_id, chat_id=self.chat_id, 
                skip_stream=skip_stream, **kwargs
            )
        else:
            raise ValueError("Chat must have project_id to send message")
    
    def get_details(self, prompt_debug: bool = False, **kwargs):
        """Get detailed information about this chat."""
        if hasattr(self, 'project_id'):
            return self._client.chats().get(self.chat_id, self.project_id, prompt_debug=prompt_debug, **kwargs)
        else:
            raise ValueError("Chat must have project_id to get details")


class DataType(ResourceBase):
    """Enhanced data type resource with convenience methods."""
    
    def delete(self):
        """Delete this data type."""
        if hasattr(self, 'project_id'):
            return self._client.data().delete(self.project_id, self.id)
        else:
            raise ValueError("DataType must have project_id to delete")
    
    def get_view(self, **kwargs):
        """Get view for this data type."""
        if hasattr(self, 'project_id'):
            return self._client.data().get_view(self.project_id, self.id, **kwargs)
        else:
            raise ValueError("DataType must have project_id to get view")
    
    def create_view(self, view_config: Dict, **kwargs):
        """Create a view for this data type."""
        if hasattr(self, 'project_id'):
            return self._client.data().create_view(self.project_id, self.id, view_config, **kwargs)
        else:
            raise ValueError("DataType must have project_id to create view")


# Project-scoped managers for cleaner API
class ProjectScopedAgentManager:
    """Agent manager scoped to a specific project."""
    
    def __init__(self, client: 'OdinClient', project_id: str):
        self._client = client
        self._project_id = project_id
    
    def create(self, name: str = "Untitled Agent", personality: str = "You are a helpful assistant.",
               building_blocks: List[Dict] = None, temperature: float = 0.0, **kwargs):
        """Create an agent in this project."""
        result = self._client.agents().create(
            self._project_id, name=name, personality=personality,
            building_blocks=building_blocks, temperature=temperature, **kwargs
        )
        # Inject project_id into the agent for convenience methods
        if hasattr(result, 'agent_id'):
            result.project_id = self._project_id
        return result
    
    def list(self, **kwargs):
        """List agents in this project."""
        return self._client.agents().list(self._project_id, **kwargs)
    
    def activate(self, agent_id: str, **kwargs):
        """Activate an agent in this project."""
        return self._client.agents().activate(self._project_id, agent_id, **kwargs)


class ProjectScopedChatManager:
    """Chat manager scoped to a specific project."""
    
    def __init__(self, client: 'OdinClient', project_id: str):
        self._client = client
        self._project_id = project_id
    
    def create(self, name: str, context: str = "", **kwargs):
        """Create a chat in this project."""
        result = self._client.chats().create(self._project_id, name, context=context, **kwargs)
        # Inject project_id into the chat for convenience methods
        if hasattr(result, 'chat_id'):
            result.project_id = self._project_id
        return result
    
    def list(self, cursor: float = None, limit: int = 30, user_id: str = None, **kwargs):
        """List chats in this project."""
        return self._client.chats().list(self._project_id, cursor=cursor, limit=limit, user_id=user_id, **kwargs)
    
    def get(self, chat_id: str, prompt_debug: bool = False, **kwargs):
        """Get a chat in this project."""
        result = self._client.chats().get(chat_id, self._project_id, prompt_debug=prompt_debug, **kwargs)
        if hasattr(result, 'chat_id'):
            result.project_id = self._project_id
        return result


class ProjectScopedDataManager:
    """Data manager scoped to a specific project."""
    
    def __init__(self, client: 'OdinClient', project_id: str):
        self._client = client
        self._project_id = project_id
    
    def create(self, title: str, description: str = "", schema: List[Dict] = None, **kwargs):
        """Create a data type in this project."""
        result = self._client.data().create(self._project_id, title, description=description, schema=schema, **kwargs)
        # Inject project_id into the data type for convenience methods
        if hasattr(result, 'id'):
            result.project_id = self._project_id
        return result
    
    def list(self, sent_internally: bool = None, **kwargs):
        """List data types in this project."""
        return self._client.data().list(self._project_id, sent_internally=sent_internally, **kwargs)
    
    def import_table(self, title: str, description: str, file_path: str, 
                     column_mappings: Union[Dict, str], delimiter: str = ",", **kwargs):
        """Import a table in this project."""
        result = self._client.data().import_table(
            self._project_id, title, description, file_path, 
            column_mappings, delimiter=delimiter, **kwargs
        )
        if hasattr(result, 'data_type') and hasattr(result.data_type, 'id'):
            result.data_type.project_id = self._project_id
        return result
    
    def get_view(self, data_type_id: str, **kwargs):
        """Get a view for a data type in this project."""
        return self._client.data().get_view(self._project_id, data_type_id, **kwargs)
    
    def create_view(self, data_type_id: str, view_config: Dict, **kwargs):
        """Create a view for a data type in this project."""
        return self._client.data().create_view(self._project_id, data_type_id, view_config, **kwargs)


class ProjectScopedKnowledgeManager:
    """Knowledge manager scoped to a specific project."""
    
    def __init__(self, client: 'OdinClient', project_id: str):
        self._client = client
        self._project_id = project_id
    
    def add_file(self, file_path: str, metadata: Dict = None, file_type: str = None,
                 force: bool = None, path: str = "/", **kwargs):
        """Add a file to this project's knowledge base."""
        return self._client.knowledge().add_file(
            self._project_id, file_path, metadata=metadata, file_type=file_type,
            force=force, path=path, **kwargs
        )


class EnhancedProjectManager:
    """Enhanced project manager that returns rich Project objects."""
    
    def __init__(self, client: 'OdinClient'):
        self._client = client
        self._v2_manager = client._v2_client.projects()
    
    def create(self, name: str, description: str = "", project_type: str = "kb_chat", **kwargs):
        """Create a project and return enhanced Project object."""
        result = self._v2_manager.create(name, description, project_type, **kwargs)
        return Project(self._client, result)
    
    def delete(self, project_id: str, **kwargs):
        """Delete a project."""
        return self._v2_manager.delete(project_id, **kwargs)
    
    def update(self, project_id: str, name: str = None, description: str = None, **kwargs):
        """Update a project."""
        return self._v2_manager.update(project_id, name=name, description=description, **kwargs)
    
    def list(self, limit: int = None, offset: int = None, **kwargs):
        """List projects and return enhanced Project objects."""
        result = self._v2_manager.list(limit=limit, offset=offset, **kwargs)
        # Create enhanced projects without modifying the original response to avoid Pydantic validation
        if hasattr(result, 'projects') and result.projects:
            # Create a simple wrapper that behaves like the original response
            class ProjectListWrapper:
                def __init__(self, original_result, enhanced_projects):
                    # Copy all attributes from original result
                    for attr in dir(original_result):
                        if not attr.startswith('_'):
                            try:
                                setattr(self, attr, getattr(original_result, attr))
                            except:
                                pass
                    # Override projects with enhanced ones
                    self.projects = enhanced_projects
            
            enhanced_projects = [Project(self._client, project_data) for project_data in result.projects]
            return ProjectListWrapper(result, enhanced_projects)
        return result
    
    def get_members(self, project_id: str, **kwargs):
        """Get project members."""
        return self._v2_manager.get_members(project_id, **kwargs)
    
    def add_user(self, project_id: str, user_email: str, role: str = "viewer", **kwargs):
        """Add user to project."""
        return self._v2_manager.add_user(project_id, user_email, role, **kwargs)


class EnhancedAgentManager:
    """Enhanced agent manager that returns rich Agent objects."""
    
    def __init__(self, client: 'OdinClient'):
        self._client = client
        self._v2_manager = client._v2_client.agents()
    
    def create(self, project_id: str, name: str = "Untitled Agent",
               personality: str = "You are a helpful assistant.",
               building_blocks: List[Dict] = None, temperature: float = 0.0, **kwargs):
        """Create an agent and return enhanced Agent object."""
        result = self._v2_manager.create(
            project_id, name=name, personality=personality,
            building_blocks=building_blocks, temperature=temperature, **kwargs
        )
        agent = Agent(self._client, result)
        agent.project_id = project_id  # Inject project_id for convenience methods
        return agent
    
    def edit(self, agent_id: str, project_id: str, name: str = None,
             personality: str = None, building_blocks: List[Dict] = None,
             temperature: float = None, **kwargs):
        """Edit an agent."""
        return self._v2_manager.edit(
            agent_id, project_id, name=name, personality=personality,
            building_blocks=building_blocks, temperature=temperature, **kwargs
        )
    
    def activate(self, project_id: str, agent_id: str, **kwargs):
        """Activate an agent."""
        return self._v2_manager.activate(project_id, agent_id, **kwargs)
    
    def list(self, project_id: str, **kwargs):
        """List agents."""
        return self._v2_manager.list(project_id, **kwargs)


class EnhancedChatManager:
    """Enhanced chat manager that returns rich Chat objects."""
    
    def __init__(self, client: 'OdinClient'):
        self._client = client
        self._v2_manager = client._v2_client.chats()
    
    def create(self, project_id: str, name: str, context: str = "", **kwargs):
        """Create a chat and return enhanced Chat object."""
        result = self._v2_manager.create(project_id, name, context=context, **kwargs)
        chat = Chat(self._client, result)
        chat.project_id = project_id  # Inject project_id for convenience methods
        return chat
    
    def delete(self, chat_id: str, project_id: str, **kwargs):
        """Delete a chat."""
        return self._v2_manager.delete(chat_id, project_id, **kwargs)
    
    def get(self, chat_id: str, project_id: str, prompt_debug: bool = False, **kwargs):
        """Get a chat and return enhanced Chat object."""
        result = self._v2_manager.get(chat_id, project_id, prompt_debug=prompt_debug, **kwargs)
        chat = Chat(self._client, result)
        chat.project_id = project_id  # Inject project_id for convenience methods
        return chat
    
    def list(self, project_id: str, cursor: float = None, limit: int = 30,
             user_id: str = None, **kwargs):
        """List chats."""
        return self._v2_manager.list(project_id, cursor=cursor, limit=limit, user_id=user_id, **kwargs)
    
    def send_message(self, message: str, project_id: str, chat_id: str = None,
                     skip_stream: bool = True, **kwargs):
        """Send a message."""
        return self._v2_manager.send_message(message, project_id, chat_id=chat_id, skip_stream=skip_stream, **kwargs)
    
    def get_models(self, **kwargs):
        """Get available models."""
        return self._v2_manager.get_models(**kwargs)


class EnhancedDataManager:
    """Enhanced data manager that returns rich DataType objects."""
    
    def __init__(self, client: 'OdinClient'):
        self._client = client
        self._v2_manager = client._v2_client.data()
    
    def create(self, project_id: str, title: str, description: str = "",
               schema: List[Dict] = None, **kwargs):
        """Create a data type and return enhanced DataType object."""
        result = self._v2_manager.create(project_id, title, description=description, schema=schema, **kwargs)
        data_type = DataType(self._client, result)
        data_type.project_id = project_id  # Inject project_id for convenience methods
        return data_type
    
    def delete(self, project_id: str, data_type_id: str, **kwargs):
        """Delete a data type."""
        return self._v2_manager.delete(project_id, data_type_id, **kwargs)
    
    def get(self, project_id: str, data_type_id: str, **kwargs):
        """Get a data type."""
        return self._v2_manager.get(project_id, data_type_id, **kwargs)
    
    def list(self, project_id: str, sent_internally: bool = None, **kwargs):
        """List data types."""
        return self._v2_manager.list(project_id, sent_internally=sent_internally, **kwargs)
    
    def import_table(self, project_id: str, title: str, description: str,
                     file_path: str, column_mappings: Union[Dict, str],
                     delimiter: str = ",", **kwargs):
        """Import a table."""
        return self._v2_manager.import_table(
            project_id, title, description, file_path, column_mappings, delimiter=delimiter, **kwargs
        )
    
    def create_view(self, project_id: str, data_type_id: str, view_config: Dict, **kwargs):
        """Create a view."""
        return self._v2_manager.create_view(project_id, data_type_id, view_config, **kwargs)
    
    def get_view(self, project_id: str, data_type_id: str, **kwargs):
        """Get a view."""
        return self._v2_manager.get_view(project_id, data_type_id, **kwargs)


class OdinClient:
    """
    Enhanced Odin SDK client v3 with improved resource objects and convenience methods.
    
    This wrapper improves upon v2 by:
    - Flattening response objects (project.id instead of project.project.id)
    - Adding convenience methods to resources (project.delete())
    - Providing project-scoped managers (project.agents.create())
    - Maintaining full backward compatibility with v2 API
    """
    
    def __init__(self, api_key: str, api_secret: str, host: str = "http://localhost:8001"):
        """Initialize the enhanced Odin client."""
        self._v2_client = V2Wrapper(api_key, api_secret, host)
        
        # Enhanced managers that return rich objects
        self._projects = EnhancedProjectManager(self)
        self._agents = EnhancedAgentManager(self)
        self._chats = EnhancedChatManager(self)
        self._data = EnhancedDataManager(self)
        
        # Pass through managers that don't need enhancement yet
        self._knowledge = self._v2_client.knowledge()
        self._roles = self._v2_client.roles()
        self._json_store = self._v2_client.json_store()
    
    def projects(self):
        """Access project operations."""
        return self._projects
    
    def agents(self):
        """Access agent operations."""
        return self._agents
    
    def chats(self):
        """Access chat operations."""
        return self._chats
    
    def data(self):
        """Access data operations."""
        return self._data
    
    def knowledge(self):
        """Access knowledge base operations."""
        return self._knowledge
    
    def roles(self):
        """Access role operations."""
        return self._roles
    
    def json_store(self):
        """Access JSON store operations."""
        return self._json_store
    
    def call(self, operation: str, *args, **kwargs):
        """Direct SDK operation call (escape hatch)."""
        return self._v2_client.call(operation, *args, **kwargs)


def create_client(api_key: str, api_secret: str, host: str = "http://localhost:8001") -> OdinClient:
    """
    Create an enhanced Odin client with improved resource objects.
    
    Args:
        api_key: Your Odin API key
        api_secret: Your Odin API secret  
        host: API host URL (default: http://localhost:8001)
        
    Returns:
        Enhanced OdinClient with flattened response objects and convenience methods
    """
    return OdinClient(api_key, api_secret, host)


# Re-export the error class for compatibility
__all__ = ['OdinClient', 'create_client', 'OdinError', 'Project', 'Agent', 'Chat', 'DataType'] 