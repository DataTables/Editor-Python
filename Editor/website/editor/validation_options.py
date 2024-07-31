from typing import Optional, Dict

class ValidationOptions:
    """
    Common validation options that can be specified for all validation methods.

    Attributes:
        message (str): Error message should the validation fail.
        empty (bool): Allow a field to be empty, i.e., a zero-length string (default is True).
                      Set to False to require it to be non-zero length.
        optional (bool): Require the field to be submitted or not (default is True).
                         When set to True, the field does not need to be included in the list of
                         parameters sent by the client. If set to False, then it must be included.
                         This option can be particularly useful in Editor as Editor will not set a
                         value for fields which have not been submitted, allowing the ability to
                         submit just a partial list of options.
    """

    # Defaults
    message: str = "Input not valid"
    empty: bool = True
    optional: bool = True

    @staticmethod
    def select(user: Optional['ValidationOptions'] = None) -> 'ValidationOptions':
        """
        Select the provided user options or return default validation options.

        :param user: User-specified validation options.
        :type user: ValidationOptions, optional
        :return: Selected validation options.
        :rtype: ValidationOptions
        """
        if user:
            return user

        return ValidationOptions()

    def __init__(self, options: Optional[Dict] = None):
        """
        Constructor to initialize validation options.

        :param options: Dictionary of user-specified options.
        :type options: dict, optional
        """
        if options is None:
            options = {}

        self.message = options.get('message', self.message)
        self.empty = options.get('empty', self.empty)
        self.optional = options.get('optional', self.optional)