
import dataclasses
from typing import Any, List, Type
from datetime import datetime

@dataclasses.dataclass
class Field:
    """Represents a field in a data model."""
    # Default attributes for a field
    unique: bool = False
    max_length: int | None = None
    default: Any = None
    relation: str | None = None
    gt: int | None = None # for greater than validation
    auto_now_add: bool = False

    def get_type_hint(self) -> str:
        return "Any"

class StringField(Field):
    def get_type_hint(self) -> str:
        return "str"

class IntegerField(Field):
    def get_type_hint(self) -> str:
        return "int"

class DateTimeField(Field):
    def get_type_hint(self) -> str:
        return "datetime"

# This is a placeholder for now. The real magic will happen in the decorator.
class Model:
    """Base class for user-defined data models."""
    pass

@dataclasses.dataclass
class App:
    """Represents the user's application and holds all registered models."""
    name: str
    models: List[Type[Model]] = dataclasses.field(default_factory=list)

    def model(self, cls: Type[Model]) -> Type[Model]:
        """
        A decorator to register a class as a model for this app.

        Example:
            app = App("MyApp")

            @app.model
            class User(Model):
                ...
        """
        self.models.append(cls)
        # Here we could add logic to inspect the model, validate it, etc.
        return cls
