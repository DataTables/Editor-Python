from datetime import datetime
from typing import Callable, Dict, Optional, Union


class Formatter:
    """
    Formatter methods which can be used with `Field.getFormatter` and
    `Field.setFormatter`.

    The methods in this class return a function for use with the formatter
    methods. Each method may define its own parameters that configure how
    the formatter operates. For example the date / time formatters take
    information on the formatting to be used.    
    """
    @staticmethod
    def sql_date_to_format(format: str) -> Callable[[str, Dict], str]:
        """
        Convert from SQL date / date time format (ISO8601) to a format given
        by the options parameter. Typically used with a get formatter.

        Uses datetime - formats are defined by datetime.
        :param str format: datetime format to apply to date
        :return: Configured formatter function  
        :rtype: function      
        """

        def func(val: Union[str, datetime], data: Dict):
            if val is None:
                return None

            # Parse the date string assuming it's in 'YYYY-MM-DD' format
            date_obj = datetime.strptime(
                val, '%Y-%m-%d') if isinstance(val, str) else val

            # Format the date object to the desired format
            return date_obj.strftime(format)

        return func

    @staticmethod
    def format_to_sql_date(format: str) -> Callable[[str, Dict], str]:
        """
        Convert to SQL date / date time format (ISO8601) from a format given
        by the options parameter. Typically used with a set formatter.

        Uses datetime - formats are defined by datetime.
        :param str format: datetime format to apply to date
        :return: Configured formatter function      
        :rtype: function      
        """

        def func(val: str, data: Dict):
            if val is None or val == '':
                return None

            # Parse the date string using the provided format
            date_obj = datetime.strptime(val, format)
            # Format the date object to the desired SQL date format (YYYY-MM-DD)
            return date_obj.strftime('%Y-%m-%d')

        return func

    @staticmethod
    def date_time(from_format: str, to_format: str) -> Callable[[str, Dict], str]:
        """
        Convert one datetime format to another

        Uses datetime - formats are defined by datetime.
        :param str from: From format
        :param str to: To format
        :return: Configured formatter function    
        :rtype: function      
        """
        def func(val: str, data: Dict):
            if val is None:
                return None

            # Parse the date string using the provided 'from' format
            try:
                date_obj = datetime.strptime(val, from_format)
            except ValueError:
                return None  # Handle the case where parsing fails

            # Format the date object to the desired 'to' format
            return date_obj.strftime(to_format)

        return func

    @staticmethod
    def explode(delimiter: Optional[str] = '|') -> Callable[[str, Dict], str]:
        """
        Convert a string of values into an array for use with checkboxes.

        :param str delimiter: Delimiter 
        :return: Configured formatter function   
        :rtype: function      
        """
        def func(val: str, data: Dict):
            # Ensure the value is a string before splitting
            return str(val).split(delimiter)

        return func

    @staticmethod
    def implode(delimiter: Optional[str] = '|') -> Callable[[str, Dict], str]:
        """
        Convert an array of values from a checkbox into a string which can be
            used to store in a text field in a database.

        :param str delimiter: Delimiter 
        :return: Configured formatter function            
        :rtype: function      
        """
        def func(val: str, data: Dict):
            # Ensure the value is a list before joining
            return delimiter.join(val)

        return func

    @staticmethod
    def if_empty(empty_value: Optional[str] = None) -> Callable[[str, Dict], str]:
        """
        Convert an empty string to a predefined value.

        :param str empty_value: Value to use if an empty value is submitted.
        :return: Configured formatter function
        :rtype: function
        """
        def func(val: str, data: Dict):
            return empty_value if val == '' else val

        return func

    @staticmethod
    def from_decimal_char(char: Optional[str] = ',') -> Callable[[str, Dict], str]:
        """
        Convert a number from using any character other than a period (dot) to
        one which does use a period. This is useful for allowing numeric user
        input in regions where a comma is used as the decimal character. Use with
        a set formatter.

        :param str char: Decimal place character
        :return: Configured formatter function
        :rtype: function      
        """
        def func(val: str, data: Dict):
            # Ensure val is a string before replacing
            return str(val).replace(char, '.')

        return func

    @staticmethod
    def to_decimal_char(char: Optional[str] = ',') -> Callable[[str, Dict], str]:
        """
        Convert a number with a period (dot) as the decimal character to use
        a different character (typically a comma). Use with a get formatter.

        :param str char: Decimal place character
        :return: Configured formatter function
        :rtype: function      
        """
        def formatter(val: str, data: Dict):
            # Ensure val is a string before replacing
            return str(val).replace('.', char)

        return formatter
