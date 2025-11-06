"""Type definitions for PyHiveLMS."""

from __future__ import annotations

# Import the implementation from the `pyhive` package (implementation
# lives there) and expose the client at package level.
from pyhive.src.types.assignment import Assignment  # re-export
from pyhive.src.types.assignment_response import AssignmentResponse  # re-export
from pyhive.src.types.user import User  # re-export
from pyhive.src.types.module import Module  # re-export
from pyhive.src.types.exercise import Exercise  # re-export
from pyhive.src.types.class_ import Class
from pyhive.src.types.form_field import FormField

__all__ = [
    "Assignment",
    "AssignmentResponse",
    "User",
    "Module",
    "Exercise",
    "Class",
    "FormField",
]
