from enum import Enum
import bleach
from typing import Union, Callable, Dict, Optional, List

from .validation_host import ValidationHost
from .action import Action
from .set_type import SetType
from .nested_data import NestedData

from .options import Options


class Field(NestedData):
    """
    Field definitions for the DataTables Editor.

    Each Database column that is used with Editor can be described with this
    Field method (both for Editor and Join instances). It basically tells
    Editor what table column to use, how to format the data and if you want
    to read and/or write this column.

    Field instances are used with the "Editor.field" and
    "Mjoin.field" methods to describe what fields should be interacted
    with by the editable table.
    """

    def __init__(self, db_field: str, name: Optional[str] = None):
        """
        Creates an instance of Field.

        :param db_field: Name of the database column
        :type db_field: str
        :param name: Optional name to use in the JSON output from Editor and the
                     HTTP submit from the client-side when editing. If not given then the
                     `db_field` name is used.
        :type name: str, optional
        :rtype: None
        """

        self._db_field = db_field
        self._name = db_field if name == None else name

        # Internal variables
        self._validator = []
        self._set_formatter = None
        self._get_formatter = None
        self._set_value = None
        self._get_value = None
        self._http = True
        self._opts = None
        self._get = True
        self._set = SetType.BOTH

    ###################
    # Public functions
    ###################

    def db_field(self, db_field: Optional[str] = None) -> Union[str, 'Field']:
        """
        Getter/setter for the database column name.

        :param str db_field: Optional. The database column name to set. If None, the current database column name is returned.
        :return: The database column name if getting, or self if setting.
        :rtype: str or Field (self)
        """
        if db_field is None:
            return self._db_field

        self._db_field = db_field

        return self

    def get(self, flag: bool = None) -> Union[bool, 'Field']:
        """
        Get the "get" flag for the field,  (i.e. if the field should be read from the database).

        :param flag: True to mark as readable, False otherwise
        :type flag: bool, optional
        :return: Self for chaining if setter, otherwise current values
        :rtype: bool or Field
        """

        if flag is None:
            return self._get

        self._get = flag

        return self

    def get_formatter(self, formatter: Optional[Callable[[str, Dict], str]] = None) -> Union[Callable[[str, Dict], str], 'Field']:
        """
        Set the get formatter.

        When the data has been retrieved from the server, it can be passed through
        a formatter here, which will manipulate (format) the data as required. This
        can be useful when, for example, working with dates and a particular format
        is required on the client-side.

        :param formatter: Formatter to use
        :type formatter: callable, optional
        :return: Self for chaining
        :rtype: Field or callable
        """

        if formatter is None:
            return self._get_formatter

        self._get_formatter = formatter

        return self

    def xss(self, flag: Optional[Union[bool, Callable[[str], str]]] = None) -> Union['Field', Callable[[str], str]]:
        """
        Set a formatting method that will be used for XSS checking / removal.
        This should be a function that takes a single argument (the value to be
        cleaned) and returns the cleaned value.

        Editor will use `bleach` by default for this operation, which is built
        into the software and no additional configuration is required, but a
        custom function can be used if you wish to use a different formatter.

        If you wish to disable this option (which you would only do if you are
        absolutely confident that your validation will pick up on any XSS inputs)
        simply provide a closure function that returns the value given to the
        function. This is _not_ recommended.   

        :param flag:
            None: return current XSS validation function
            True: use default XSS validation function
            False: disable XSS validation
            function: use that function for XSS validation
        :type flag: any, optional
        :return: Current XSS validation function or self for chaining
        :rtype: Field or callable
        """

        # Getter if nothing passed
        if flag == None:
            return self._xss

        if flag == True:
            # Use default
            self._xss = bleach.clean
        elif flag == False:
            # No XSS validation
            self._xss = None
        else:
            # Use supplied function
            self._xss = flag

        return self

    def _xss_safety(self, val: any) -> Union[Callable, str]:
        """
        Protected function to perform XSS validation of a string

        :param val: String (or array) to cleanse
        :type val: any
        :return: Cleansed string (or array of strings)
        :rtype: callable or str
        """

        if self._xss is None:
            return val

        # An array of strings
        if isinstance(val, list):
            out = []

            for i in range(len(val)):
                out.append(self._xss(val[i]))

            return out

        # Single string
        return self._xss(val)

    def validator(self, val: Optional[Callable[[str, Dict, ValidationHost], bool]] = None, set_formatted: bool = False) -> Union['Field', list]:
        """
        Set the 'validator' of the field.

        The validator can be used to check if any abstract piece of data is valid
        or not according to the given rules of the validation function used.

        Multiple validation options can be applied to a field instance by calling
        this method multiple times. For example, it would be possible to have a
        'required' validation and a 'maxLength' validation with multiple calls.

        Editor has a number of validation available with the {@link Validate} class
        which can be used directly with this method.

        :param val: Validation function
        :type val: callable, optional
        :param set_formatted: Use formatted value for validation
        :type set_formatted: bool
        :return: Self for chaining or current validators
        :rtype: Field or list
        """

        # If no validation function supplied, return the current validators
        if val is None:
            return self._validator

        self._validator.append(
            {'set_formatted': set_formatted, 'validator': val})
        return self

    def set(self, flag: Union[bool, SetType] = None) -> Union['Field', 'SetType']:
        """
        Get or set the `set` property for this field.

        A field can be marked as read only using this option, to be set only
        during an create or edit action or to be set during both actions. This
        provides the ability to have fields that are only set when a new row is
        created (for example a "created" time stamp).        

        :param flag: None if getter, otherwise set value
        :type flag: bool or SetType, optional
        :return: Self for chaining if setter, otherwise current value
        :rtype: Field or SetType
        """

        if flag is None:
            return self._set

        if flag == True:
            self._set = SetType.BOTH
        elif flag == False:
            self._set = SetType.NONE
        else:
            self._set = flag

        return self

    def set_formatter(self, formatter: Optional[Callable[[str, Dict], str]] = None) -> Union['Field', Callable[[str, Dict], str]]:
        """
        Set the set formatter.

        When the data has been retrieved from the server, it can be passed through
        a formatter here, which will manipulate (format) the data as required. This
        can be useful when, for example, working with dates and a particular format
        is required on the client-side.

        Editor has a number of formatters available with the {@link Format} class
        which can be used directly with this method.        

        :param formatter: Formatter to use
        :type formatter: callable, optional
        :return: Self for chaining
        :rtype: Field or callable
        """

        if formatter is None:
            return self._set_formatter

        self._set_formatter = formatter

        return self

    def set_value(self, val: Union[str, Optional[Callable[[], str]]] = None) -> Union['Field', str, Callable[[], str]]:
        """
        Set the set value for the field.

        If given, then this value is used to write to the database regardless
        of what data is sent from the client-side.

        :param val: Value to set
        :type val: str or callable, optional
        :return: Self for chaining or current set value
        :rtype: Field or str
        """

        if val is None:
            return self._set_value

        self._set_value = val

        return self

    def get_value(self, val: Union[str, Optional[Callable[[], str]], None] = None) -> Union['Field', Optional[Callable[[], str]], 'Field']:
        """
        Set the get value for the field.

        If given, then this value is used to send to the client-side, regardless
        of what value is held by the database.

        :param val: Value to set
        :type val: str or callable, optional
        :return: Self for chaining or current get value
        :rtype: Field or any
        """

        if val is None:
            return self._get_value

        self._get_value = val

        return self

    def http(self, set: Optional[bool] = None) -> Union[bool, 'Field']:
        """
        Getter/setter for the http property.

        Indicator to say if this field can be read over http (i.e. externally)

        :param set: Value to set
        :type set: bool, optional
        :return: HTTP status or self for chaining
        :rtype: bool or Field
        """
        if set is None:
            return self._http

        self._http = set

        return self

    def name(self, name: Optional[str] = None) -> Union[str, 'Field']:
        """
        Getter/setter for the name.

        The name is typically the same as the dbField name, since it makes things
        less confusing(!), but it is possible to set a different name for the data
        which is used in the JSON returned to DataTables in a 'get' operation and
        the field name used in a 'set' operation.

        :param name: Name to set
        :type name: str, optional
        :return: Name or self for chaining
        :rtype: str or Field
        """
        if name is None:
            return self._name

        self._name = name
        return self

    def options(self, opts: Optional[Options] = None) -> Union[Options, 'Field']:
        """
        Get/Set how a list of options (values and labels) will be retrieved for the field.

        Gets a list of values that can be used for the options list in radio,
        select and checkbox inputs from the database for this field.

        Note that this is for simple 'label / value' pairs only. For more complex
        data, including pairs that require joins and where conditions, use a
        closure to provide a query

        :param opts: Options configuration
        :type opts: any, optional
        :return: Options or self for chaining
        :rtype: Options or Field
        """
        if opts is None:
            return self._opts

        self._opts = opts
        return self

    def __read_prop(self, name: str, data: Dict) -> str:
        """
        Get a nested property value.

        :param name: Property name
        :type name: str
        :param data: Data set to check
        :type data: dict
        :return: Property value or None
        :rtype: str
        """
        if '.' not in name:
            return data[name] if name in data else None

        names = name.split('.')
        inner = data

        for i in range(len(names) - 1):
            if names[i] not in inner:
                return False

            inner = inner[names[i]]

        idx = names[len(names) - 1]

        return inner[idx] if idx in inner else None

    def __format(self, val: str, data: Dict, formatter: Callable[[str, Dict], str]) -> str:
        """
        Format a value using the given formatter.

        :param val: Value to format
        :type val: str
        :param data: Data set
        :type data: dict
        :param formatter: Formatter function
        :type formatter: callable
        :return: Formatted value
        :rtype: str
        """
        return val if formatter is None else formatter(val, data)

    def val(self, direction: str, data: Dict) -> str:
        """
        Protected function to apply callback functions

        :param direction: The direction of the operation, either 'get' or 'set'.
        :type direction: str
        :param data: The data set to be used for the operation.
        :type data: dict
        :return: The formatted field value.
        :rtype: str
        """
        if direction == 'get':
            if self._get_value != None:
                val = self._get_value() if callable(self._get_value) else self._get_value
            else:
                db_field = self.db_field()
                val = data[db_field] if db_field in data else None

            return self.__format(val, data, self._get_formatter)

        if self._set_value != None:
            val = self._set_value() if callable(self._set_value) else self._set_value
        else:
            val = self.__read_prop(self.name(), data)

        return self.__format(val, data, self._set_formatter)

    ################################
    # Protected methods, used by Editor class and not generally for public use
    ################################

    def _write(self, out: Dict, src_data: Dict) -> None:
        """
        Protected function to write data into an object.

        :param out: Output dictionary
        :type out: dict
        :param src_data: Source data
        :type src_data: dict
        :rtype: None
        """
        self._write_prop(out, self.name(), self.val('get', src_data))

    def _validate(self, data: Dict, editor, id: str, action: str) -> Union[bool, str]:
        """
        Protected function to execute the configured validators.

        :param data: Data set
        :type data: dict
        :param editor: Editor instance
        :param id: Row ID
        :param action: Action being performed
        :type action: str
        :return: `True` if successful, or string containing the error
        :rtype: bool or str
        """

        # See if any validators for this field
        if len(self._validator) == 0:
            return True

        val = self.__read_prop(self.name(), data)
        host = ValidationHost(action, id, self, editor)

        # Iterate through all the validators
        for v in self._validator:
            validator = v['validator']
            test_val = self.val('set', data) if v['set_formatted'] else val

            res = validator(test_val, data, host)
            if res != True:
                return res

        # No validation errors, so must be valid
        return True

    def _apply(self, action: str, data: dict = None) -> bool:
        """
        Protected function to determine if a field is required.

        :param action: 'get' | 'create' | 'edit'
        :type action: str
        :param data: Data set, optional
        :type data: dict, optional
        :return: True if the field is required, otherwise False
        :rtype: bool
        """
        if action == 'get':
            return self.get()

        set_value = self.set()

        if action == 'create':
            if set_value == SetType.NONE or set_value == SetType.EDIT:
                return False

        if action == 'edit':
            if set_value == SetType.NONE or set_value == SetType.CREATE:
                return False

        # Check it was in the submitted data
        if self.set_value() == None and not self._prop_exists(self.name(), data):
            return False

        # In the data set, so use it
        return True

    def _options_exec(self, db) -> any:
        """
        Execute options for the field.

        :param db: Database instance
        :return: Executed options
        :rtype: any
        """
        # TK COLIN not sure what the instanceOf Options is for here
        if self._opts:
            return self._opts._exec(db)

        return None
