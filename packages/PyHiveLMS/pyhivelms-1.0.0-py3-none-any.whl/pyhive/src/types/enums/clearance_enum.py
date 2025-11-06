"""Enumeration for user clearance levels."""

from enum import IntEnum


class ClearanceEnum(IntEnum):
    """Enumeration of user clearance levels in the Hive system."""

    # TODO: Replace VALUE_X with actual clearance level names
    VALUE_1 = 1
    VALUE_2 = 2
    VALUE_3 = 3
    VALUE_5 = 5

    def __str__(self) -> str:
        return str(self.value)
