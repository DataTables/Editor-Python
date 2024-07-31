from typing import Optional, Any


class ValidationHost:
    """
    Information container about the Field and Editor instances
    for the item being validated.
    """

    def __init__(self, action: Optional[str] = None, id: Optional[str] = None, field: Optional[str] = None, editor: Optional[Any] = None):
        """
        Creates an instance of ValidationHost.

        :param action: Action being performed (edit, create, or remove)
        :type action: str, optional
        :param id: Id of the row being edited or removed. Will be undefined for create
        :type id: str, optional
        :param field: Field instance
        :type field: object, optional
        :param editor: Editor instance
        :type editor: object, optional
        :rtype: None
        """
        self.action = action
        self.id = id
        self.field = field
        self.editor = editor
