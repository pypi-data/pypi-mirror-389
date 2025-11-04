"""
ToDoWrite: Hierarchical Task Management System

A sophisticated hierarchical task management system designed for complex project planning and execution.
Built with a 12-layer declarative framework, it provides both standalone CLI capabilities and Python module integration.
"""

# Core version information
from .version import get_version

__version__ = get_version()
__title__ = "ToDoWrite"
__description__ = "Hierarchical task management system with 12-layer declarative planning framework"


# Core application components
# Custom exceptions
# Core types
from .core import (
    TODOWRITE_SCHEMA,
    CLIError,
    Command,
    ConfigurationError,
    DatabaseError,
    InvalidNodeError,
    LayerType,
    Link,
    Metadata,
    Node,
    NodeError,
    NodeNotFoundError,
    NodeUpdater,
    ProjectManager,
    SchemaError,
    StatusType,
    StorageError,
    ToDoWrite,
    ToDoWriteError,
    TokenOptimizationError,
    YAMLError,
    create_node,
    delete_node,
    export_nodes,
    generate_node_id,
    get_node,
    import_nodes,
    link_nodes,
    list_nodes,
    search_nodes,
    unlink_nodes,
    update_node,
)

# Database components (commented out until needed)
# from .database import (
#     StoragePreference,
#     StorageType,
#     determine_storage_backend,
#     get_storage_info,
#     set_storage_preference,
# )
# Project utilities - will be added when functions are available in core module
# Schema management
# YAML management
from .storage import YAMLManager
from .storage import validate_database_schema as validate_schema
from .storage import validate_node_data as validate_node

# Core application components
__all__ = [
    "TODOWRITE_SCHEMA",
    "CLIError",
    "Command",
    "ConfigurationError",
    "DatabaseError",
    "InvalidNodeError",
    "LayerType",
    "Link",
    "Metadata",
    "Node",
    "NodeError",
    "NodeNotFoundError",
    "NodeUpdater",
    "ProjectManager",
    "SchemaError",
    "StatusType",
    "StorageError",
    "ToDoWrite",
    "ToDoWriteError",
    "TokenOptimizationError",
    "YAMLError",
    "YAMLManager",
    "__description__",
    "__title__",
    "__version__",
    "create_node",
    "delete_node",
    "export_nodes",
    "generate_node_id",
    "get_node",
    "import_nodes",
    "link_nodes",
    "list_nodes",
    "search_nodes",
    "unlink_nodes",
    "update_node",
    "validate_node",
    "validate_schema",
]


# Convenience function for quick initialization
def init_project(_project_path: str = ".", _db_type: str = "postgres") -> bool:
    """
    Quick project initialization.

    Args:
        project_path: Path to the project directory (default: current directory)
        db_type: Database type ('postgres' or 'sqlite')

    Returns:
        True if initialization was successful
    """
    # Placeholder for project initialization
    # This will be expanded when project structure functions are available
    return True
