
import inspect
from jinja2 import Environment, FileSystemLoader
from pathlib import Path

from .models import App, Model, Field

def get_model_fields(model: Model):
    """Extracts fields from a model class."""
    return [(name, type) for name, type in inspect.getmembers(model) if isinstance(type, Field)]

def generate_main_py(app: App) -> str:
    """
    Generates the content of the main.py file for the FastAPI backend.

    Args:
        app: The user's App instance containing all model information.

    Returns:
        A string containing the generated Python code for main.py.
    """
    # Set up Jinja2 environment
    template_dir = Path(__file__).parent / "templates"
    env = Environment(loader=FileSystemLoader(template_dir), trim_blocks=True, lstrip_blocks=True)
    
    # Load the template
    template = env.get_template("main_py.jinja2")

    # Prepare data for the template
    template_data = {
        "app_name": app.name,
        "models": [],
    }

    for model_class in app.models:
        model_data = {
            "name": model_class.__name__,
            "fields": get_model_fields(model_class),
        }
        template_data["models"].append(model_data)
    
    # Render the template with the app name and models
    rendered_code = template.render(template_data)
    
    return rendered_code
