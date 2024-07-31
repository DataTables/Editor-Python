import re
import datetime
import validators

from sqlalchemy import text

from typing import Callable, Optional, Dict, List

from .validation_options import ValidationOptions
from .validation_host import ValidationHost


class Validate:
    """
    Validation methods for DataTables Editor fields. All of the methods
    defined in this class return a function that can be used by
    `Field` instance's `Field.Validator` method.

    Each method may define its own parameters that configure how the
    formatter operates. For example the `minLen` validator takes information
    on the minimum length of value to accept.

    Additionally each method can optionally take a `ValidationOptions`
    instance that controls common validation options and error messages.

    The validation functions return `true` for valid data and a string for
    invalid data, with the string being the error message.
    """

    Options = ValidationOptions

    def __common(val: str, opts: ValidationOptions):
        if not opts.optional and val == None:
            return False

        if not opts.empty and val != None and val == "":
            return False

        if opts.optional and val == None:
            return True

        if opts.empty and val == "":
            return True

        # Have the specific validation function perform its tests
        return None

    # Built-in validators
    @staticmethod
    def basic(cfg: Optional[ValidationOptions] = {}) -> Callable[[str, dict, ValidationHost], bool]:
        """
        Basic validation - this is used to perform the validation provided by the
            validation options only. If the validation options pass (e.g. `required`,
            `empty` and `optional`) then the validation will pass regardless of the
            actual value.
        :param dict cfg: Optional `ValidationOptions` object
        :return: Configured validation function
        :rtype: function
        """
        opts = ValidationOptions.select(cfg)

        def func(val: str, data: dict, host: ValidationHost) -> bool:
            common = Validate.__common(val, opts)
            return opts.message if common == False else True

        return func

    @staticmethod
    def required(cfg: Optional[Dict] = {}) -> Callable[[str, dict, ValidationHost], bool]:
        """
        Required field - there must be a value and it must be a non-empty value.
        :param dict cfg: Optional `ValidationOptions` object
        :return: Configured validation function
        :rtype: function
        """
        opts = ValidationOptions.select(cfg)
        opts.empty = False
        opts.optional = False

        def func(val: str, data: dict, host: ValidationHost) -> bool:
            common = Validate.__common(val, opts)
            return opts.message if common == False else True

        return func

    @staticmethod
    def not_empty(cfg: Optional[Dict] = {}) -> Callable[[str, dict, ValidationHost], bool]:
        """
        Optional field, but if given there must be a non-empty value.
        :param dict cfg: Optional `ValidationOptions` object
        :return: Configured validation function
        :rtype: function
        """
        opts = ValidationOptions.select(cfg)
        opts.empty = False

        def func(val: str, data: dict, host: ValidationHost) -> bool:
            common = Validate.__common(val, opts)
            return opts.message if common == False else True

        return func

    @staticmethod
    def boolean(cfg: Optional[Dict] = {}) -> Callable[[str, dict, ValidationHost], bool]:
        """
        Validate an input as a boolean value.
        :param dict cfg: Optional `ValidationOptions` object
        :return: Configured validation function
        :rtype: function
        """
        opts = ValidationOptions.select(cfg)

        def func(val: str, data: dict, host: ValidationHost) -> bool:
            common = Validate.__common(val, opts)
            if common != None:
                return opts.message if common == False else True

            b = val.lower() if type(val) is str else val

            if b == True or b == 1 or b == '1' or b == 'true' or b == 't' or b == 'on' or b == 'yes' or b == '✓':
                return True

            if b == False or b == 0 or b == '0' or b == 'false' or b == 'f' or b == 'off' or b == 'no' or b == 'x':
                return True

            return opts.message

        return func

    #################################################################
    #
    # Number validation methods
    #
    #################################################################

    @staticmethod
    def numeric(decimal: Optional[str] = '.', cfg: Optional[Dict] = {}) -> Callable[[str, dict, ValidationHost], bool]:
        """
        Check that any input is numeric.
        :param str decimal: Option character to use as the decimal place
        :param dict cfg: Optional `ValidationOptions` object
        :return: Configured validation function
        :rtype: function
        """
        opts = ValidationOptions.select(cfg)

        def func(val: str, data: dict, host: ValidationHost) -> bool:
            common = Validate.__common(val, opts)
            if common != None:
                return opts.message if common == False else True

            typ = type(val)
            if typ is int or typ is float:
                return True

            num = str(val).replace(decimal, '').strip()
            if num == '' or not num.isnumeric():
                return opts.message

            return True

        return func

    @staticmethod
    def min_num(min: float, decimal: Optional[str] = '.', cfg: Optional[Dict] = {}) -> Callable[[str, dict, ValidationHost], bool]:
        """
        Check for a numeric input and that it is greater than a given value.
        :param float min: Minimum value
        :param str decimal: Optional character to use as the decimal place
        :param dict cfg: Optional `ValidationOptions` object
        :return: Configured validation function
        :rtype: function
        """
        opts = ValidationOptions.select(cfg)

        def func(val: str, data: dict, host: ValidationHost) -> bool:
            numeric = Validate.numeric(decimal, cfg)(val, data, host)
            if numeric != True:
                return opts.message

            if decimal != '.':
                num = str(val).replace(decimal, '.')
            else:
                num = val

            return opts.message if float(val) < min else True

        return func

    @staticmethod
    def max_num(max: float, decimal: Optional[str] ='.', cfg: Optional[Dict] = {}) -> Callable[[str, dict, ValidationHost], bool]:
        """
        Check for a numeric input and that it is greater than a given value.
        :param float max: Maximum value
        :param str decimal: Optional character to use as the decimal place
        :param dict cfg: Optional `ValidationOptions` object
        :return: Configured validation function
        :rtype: function
        """
        opts = ValidationOptions.select(cfg)

        def func(val: str, data: dict, host: ValidationHost) -> bool:
            numeric = Validate.numeric(decimal, cfg)(val, data, host)
            if numeric != True:
                return opts.message

            if decimal != '.':
                num = str(val).replace(decimal, '.')
            else:
                num = val

            return opts.message if float(val) > max else True

        return func

    @staticmethod
    def min_max_num(min: float, max: float, decimal: Optional[str] = '.', cfg: Optional[Dict] = {}) -> Callable[[str, dict, ValidationHost], bool]:
        """
        Check for a numeric input and that it is greater than a given value.
        :param float min: Minimum value
        :param float max: Maximum value
        :param str decimal: Optional character to use as the decimal place
        :param dict cfg: Optional `ValidationOptions` object
        :return: Configured validation function
        :rtype: function
        """
        opts = ValidationOptions.select(cfg)

        def func(val: str, data: dict, host: ValidationHost) -> bool:
            numeric = Validate.numeric(decimal, cfg)(val, data, host)
            if numeric != True:
                return opts.message

            if decimal != '.':
                num = str(val).replace(decimal, '.')
            else:
                num = val

            num = float(num)

            if num < min or num > max:
                return opts.message

            return True

        return func

    #################################################################
    #
    # String validation methods
    #
    #################################################################

    @staticmethod
    def min_len(min: int, cfg: Optional[Dict] = {}) -> Callable[[str, dict, ValidationHost], bool]:
        """
        Check for a numeric input and that it is greater than a given value.
        :param int min: Minimum length
        :param dict cfg: Optional `ValidationOptions` object
        :return: Configured validation function
        :rtype: function
        """
        opts = ValidationOptions.select(cfg)

        def func(val: str, data: dict, host: ValidationHost) -> bool:
            common = Validate.__common(val, opts)
            if common != None:
                return opts.message if common == False else True

            return opts.message if len(val) < min else True

        return func

    @staticmethod
    def max_len(min: int, cfg: Optional[Dict] = {}) -> Callable[[str, dict, ValidationHost], bool]:
        """
        Check for a numeric input and that it is greater than a given value.
        :param int max: Maximum length
        :param dict cfg: Optional `ValidationOptions` object
        :return: Configured validation function
        :rtype: function
        """
        opts = ValidationOptions.select(cfg)

        def func(val: str, data: dict, host: ValidationHost) -> bool:
            common = Validate.__common(val, opts)
            if common != None:
                return opts.message if common == False else True

            return opts.message if len(val) > max else True

        return func

    @staticmethod
    def min_max_len(min: int, max: int, cfg: Optional[Dict] = {}) -> Callable[[str, dict, ValidationHost], bool]:
        """
        Check for a numeric input and that it is greater than a given value.
        :param int min: Minimum length
        :param int max: Maximum length
        :param dict cfg: Optional `ValidationOptions` object
        :return: Configured validation function
        :rtype: function
        """
        opts = ValidationOptions.select(cfg)

        def func(val: str, data: dict, host: ValidationHost) -> bool:
            common = Validate.__common(val, opts)
            if common != None:
                return opts.message if common == False else True

            length = len(val)
            return opts.message if length < min or length > max else True

        return func

    @staticmethod
    def email(cfg: Optional[Dict] = {}) -> Callable[[str, dict, ValidationHost], bool]:
        """
        Validate an input as an e-mail address.
        :param dict cfg: Optional `ValidationOptions` object
        :return: Configured validation function
        :rtype: function
        """
        opts = ValidationOptions.select(cfg)

        def func(val: str, data: dict, host: ValidationHost) -> bool:
            common = Validate.__common(val, opts)
            if common != None:
                return opts.message if common == False else True

            res = re.match(
                r'^(([^<>()\[\]\.,;:\s@\"]+(\.[^<>()\[\]\.,;:\s@\"]+)*)|(\".+\"))@(([^<>()[\]\.,;:\s@\"]+\.)+[^<>()[\]\.,;:\s@\"]{2,})$',
                val)

            return True if res else opts.message

        return func

    @staticmethod
    def ip(cfg: Optional[Dict] = {}) -> Callable[[str, dict, ValidationHost], bool]:
        """
        Validate an input as an IP address.
        :param dict cfg: Optional `ValidationOptions` object
        :return: Configured validation function
        :rtype: function
        """
        opts = ValidationOptions.select(cfg)

        def func(val: str, data: dict, host: ValidationHost) -> bool:
            common = Validate.__common(val, opts)
            if common != None:
                return opts.message if common == False else True

            ipaddr = val.split('.')
            if len(ipaddr) != 4:
                return opts.message

            for ip in ipaddr:
                if not ip.isdigit():
                    return opts.message

                i = int(ip)
                if i < 0 or i > 255:
                    return opts.message

            return True

        return func

    @staticmethod
    def url(cfg: Optional[Dict] = {}) -> Callable[[str, dict, ValidationHost], bool]:
        """
        Validate an input as a URL.
        :param dict cfg: Optional `ValidationOptions` object
        :return: Configured validation function
        :rtype: function
        """
        opts = ValidationOptions.select(cfg)

        def func(val: str, data: dict, host: ValidationHost) -> bool:
            common = Validate.__common(val, opts)
            if common != None:
                return opts.message if common == False else True

            try:
                if validators.url(val) != True:
                    return opts.message
            except:
                return opts.message

            return True

        return func

    @staticmethod
    def xss(cfg: Optional[Dict] = {}) -> Callable[[str, dict, ValidationHost], bool]:
        """
        Check if string could contain an XSS attack string.
        :param dict cfg: Optional `ValidationOptions` object
        :return: Configured validation function
        :rtype: function
        """
        opts = ValidationOptions.select(cfg)

        def func(val: str, data: dict, host: ValidationHost) -> bool:
            common = Validate.__common(val, opts)
            if common != None:
                return opts.message if common == False else True

            return True if host.field._xss_safety(val) == val else opts.message

        return func

    @staticmethod
    def values(arr: List, cfg: Optional[Dict] = {}) -> Callable[[str, dict, ValidationHost], bool]:
        """
        Confirm that the value submitted is in a list of allowable values.
        :param list arr: List of allowable values.
        :param dict cfg: Optional `ValidationOptions` object
        :return: Configured validation function
        :rtype: function
        """
        opts = ValidationOptions.select(cfg)

        def func(val: str, data: dict, host: ValidationHost) -> bool:
            common = Validate.__common(val, opts)
            if common != None:
                return opts.message if common == False else True

            return True if val in arr else opts.message

        return func

    @staticmethod
    def no_tags(cfg: Optional[Dict] = {}) -> Callable[[str, dict, ValidationHost], bool]:
        """
        Confirm that the value submitted is in a list of allowable values.
        :param dict cfg: Optional `ValidationOptions` object
        :return: Configured validation function
        :rtype: function
        """
        opts = ValidationOptions.select(cfg)

        def func(val: str, data: dict, host: ValidationHost) -> bool:
            common = Validate.__common(val, opts)
            if common != None:
                return opts.message if common == False else True

            return opts.message if re.search(r'<.*>', val) else True

        return func

    @staticmethod
    def date_format(format: str, cfg: Optional[Dict] = {}) -> Callable[[str, dict, ValidationHost], bool]:
        """
        Confirm that the value submitted is in a list of allowable values.
        :param str format: datetime format that the value must comply with
        :param dict cfg: Optional `ValidationOptions` object
        :return: Configured validation function
        :rtype: function
        """
        opts = ValidationOptions.select(cfg)

        def func(val: str, data: dict, host: ValidationHost) -> bool:
            common = Validate.__common(val, opts)
            if common != None:
                return opts.message if common == False else True

            try:
                # If reformatting doesn't match, means not right
                df = datetime.datetime.strptime(val, format)
                dfs = df.strftime(format)
                if dfs != val:
                    return opts.message
            except:
                return opts.message

            return True

        return func

    #############################
    # Database validation
    ###

    @staticmethod
    def db_values(cfg: Optional[Dict] = {}, column: Optional[str] = None, table: Optional[str] = None, db: Optional[str] = None, values: Optional[List] = []) -> Callable[[str, dict, ValidationHost], bool]:
        """
        Confirm that the value submitted is in a list of allowable values.
        :param str column: Optional column to use to check for unique value. If not given the host field's database column name is used
        :param str table: Optional table to check that this value is uniquely. If not given the host Editor's table name is used
        :param str db: Optional database connection. If not given the host Editor's database connection is used
        :param list values: Optional list of values to use instead of querying the database
        :param dict cfg: Optional `ValidationOptions` object
        :return: Configured validation function
        :rtype: function
        """
        opts = ValidationOptions.select(cfg)

        def func(val: str, data: dict, host: ValidationHost) -> bool:
            nonlocal db, table, column
            common = Validate.__common(val, opts)
            options = host.field.options()

            if common != None:
                return opts.message if common == False else True

            if val in values:
                return True

            if db == None:
                db = host.editor._engine

            if table == None:
                table = options.table()

            if column == None:
                column = options.value()

            if table == None or column == None:
                raise Exception(
                    "Table or column for database value check is not defined for field "
                    + host.field.name())

            with db.connect() as connection:
                sql = text(
                    f"SELECT {column} FROM {table} WHERE {column} = :val")

                res = connection.execute(sql, {"val": val}).fetchall()

                return True if len(res) else opts.message

        return func

    # TK COLIN
    # TK COLIN db_unique
    # db ops
    # mjoin
