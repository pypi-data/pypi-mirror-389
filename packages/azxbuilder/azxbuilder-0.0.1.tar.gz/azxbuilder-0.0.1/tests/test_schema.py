
# This is a dummy schema file for testing purposes.

from datetime import datetime

# We need to add the src directory to the path to find our models
# This is a common pattern in testing non-installed packages
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from azxbuilder.models import App, Model, Field

app = App("MyBlog")

@app.model
class User(Model):
    name: str
    email: str = Field(unique=True)
    signup_date: datetime = Field(auto_now_add=True)

@app.model
class Post(Model):
    title: str
    content: str
    author: User = Field(relation="many-to-one")

# A second app instance to test error handling
# app2 = App("MyOtherBlog")
