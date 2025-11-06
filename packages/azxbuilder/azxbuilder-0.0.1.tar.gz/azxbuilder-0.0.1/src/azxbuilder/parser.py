
import importlib.util
import inspect
from pathlib import Path
from typing import Type

from .models import App

class SchemaError(Exception):
    """Custom exception for schema loading errors."""
    pass

def load_app_from_schema(schema_path: Path) -> App:
    """
    Loads a schema file and finds the user-defined App instance.

    Args:
        schema_path: The path to the user's schema.py file.

    Returns:
        The configured App instance found in the schema file.

    Raises:
        SchemaError: If the file doesn't exist, can't be loaded, or
                     if exactly one App instance is not found.
    """
    if not schema_path.exists() or not schema_path.is_file():
        raise SchemaError(f"Schema file not found at: {schema_path}")

    # Create a module spec from the file path
    spec = importlib.util.spec_from_file_location(name=schema_path.stem, location=str(schema_path))
    if spec is None or spec.loader is None:
        raise SchemaError(f"Could not create module spec for: {schema_path}")

    # Create a new module based on the spec
    schema_module = importlib.util.module_from_spec(spec)
    
    # Execute the module in its own namespace
    try:
        spec.loader.exec_module(schema_module)
    except Exception as e:
        raise SchemaError(f"Failed to execute schema file: {e}") from e

    # Find all instances of 'App' in the loaded module
    app_instances = []
    for _, obj in inspect.getmembers(schema_module):
        if isinstance(obj, App):
            app_instances.append(obj)

    if len(app_instances) == 0:
        raise SchemaError("No 'App' instance found in the schema file.")
    
    if len(app_instances) > 1:
        raise SchemaError("More than one 'App' instance found. Please define only one.")

    return app_instances[0]
