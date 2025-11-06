
import pytest
from pathlib import Path

# Add src to path to allow importing azxbuilder
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from azxbuilder.models import App
from azxbuilder.generator import generate_main_py

def test_generate_main_py():
    """
    Tests that the main.py file content is generated correctly.
    """
    # 1. Create a dummy App object
    test_app = App(name="MyTestApp")

    # 2. Generate the code
    generated_code = generate_main_py(test_app)

    # 3. Assert the output is correct
    assert 'app = FastAPI(title="MyTestApp")' in generated_code
    assert 'return {"message": "Welcome to MyTestApp"}' in generated_code
    assert "from fastapi import FastAPI" in generated_code
