from enum import Enum

class Action(Enum):
    """
    Enum representing the action requested by the client.

    Attributes:
        READ (int): Get data (used by DataTables).
        CREATE (int): Create a row.
        EDIT (int): Edit one or more rows.
        DELETE (int): Delete one or more rows.
        UPLOAD (int): Upload a file.
        UNKNOWN (int): Unknown action.
    """
    READ = 1
    CREATE = 2
    EDIT = 3
    DELETE = 4
    UPLOAD = 5
    UNKNOWN = -1
