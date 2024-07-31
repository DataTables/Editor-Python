from enum import Enum

class SetType(Enum):
    """
    Action requested by the client.

    Attributes:
        NONE (int): Do not set data.
        BOTH (int): Write to the database on both create and edit.
        CREATE (int): Write to the database only on create.
        EDIT (int): Write to the database only on edit.
    """
    NONE = 1
    BOTH = 2
    CREATE = 3
    EDIT = 4
