
import pytest
from pathlib import Path

# Add src to path to allow importing azxbuilder
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from azxbuilder.parser import load_app_from_schema, SchemaError
from azxbuilder.models import App

# Get the path to the test schema file
TEST_SCHEMA_PATH = Path(__file__).parent / "test_schema.py"

def test_load_valid_schema():
    """Tests that a valid schema.py file is loaded correctly."""
    # To make this test independent, we create a specific valid schema file here
    valid_content = """
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
from azxbuilder.models import App, Model, Field
app = App("MyBlog")
@app.model
class User(Model):
    name: str
"""
    valid_schema_path = Path(__file__).parent / "valid_schema.py"
    valid_schema_path.write_text(valid_content)

    app = load_app_from_schema(valid_schema_path)

    assert isinstance(app, App)
    assert app.name == "MyBlog"
    assert len(app.models) == 1
    assert app.models[0].__name__ == "User"

    valid_schema_path.unlink()

def test_schema_not_found():
    """Tests that a SchemaError is raised if the file doesn't exist."""
    with pytest.raises(SchemaError, match="Schema file not found"):
        load_app_from_schema(Path("non_existent_file.py"))

def test_no_app_instance():
    """Tests that a SchemaError is raised if no App instance is found."""
    dummy_schema_content = "class A:\n  pass"
    dummy_schema_path = Path(__file__).parent / "dummy_no_app.py"
    dummy_schema_path.write_text(dummy_schema_content)

    with pytest.raises(SchemaError, match="No 'App' instance found"):
        load_app_from_schema(dummy_schema_path)
    
    dummy_schema_path.unlink() # Clean up the dummy file

def test_multiple_app_instances():
    """Tests that a SchemaError is raised if multiple App instances are found."""
    # Create a dummy schema with multiple App instances
    dummy_content = """
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
from azxbuilder.models import App
app1 = App('App1')
app2 = App('App2')
"""
    dummy_schema_path = Path(__file__).parent / "dummy_multiple_apps.py"
    dummy_schema_path.write_text(dummy_content)

    with pytest.raises(SchemaError, match="More than one 'App' instance found"):
        load_app_from_schema(dummy_schema_path)
        
    dummy_schema_path.unlink() # Clean up

