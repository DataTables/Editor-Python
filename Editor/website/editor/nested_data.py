from typing import Callable, Dict, Optional

class NestedData:
    """
    Class that provides methods to read and write from nested JSON objects,
    using dot notation strings for the nesting. This class should be extended
    by any wishing to use these abilities.    
    """

    @staticmethod
    def _prop_exists(name: str, data: Dict) -> bool:
        """
        Check if a nested property exists in a data set.

        :param str name: Property name, with nested properties separated by dots.
        :param dict data: Data set to check.
        :return: `True` if the property exists, `False` otherwise.
        :rtype: bool
        """

        if data == None:
            return False

        if '.' not in name:
            return True if name in data else False

        names = name.split('.')
        inner = data

        for i in range(len(names) - 1):
            if names[i] not in inner:
                return False

            inner = inner[names[i]]

        return True if names[len(names) - 1] in inner else False

    @staticmethod
    def _read_prop(name: str, data: Dict) -> str:
        """
        Get a nested property value from a data set.

        :param str name: Property name, with nested properties separated by dots.
        :param dict data: Data set to check.
        :return: Value of the nested property, or `None` if the property does not exist.
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

    @staticmethod
    def _write_prop(out: dict, name: str, value: str) -> None:
        """
        Write a value to a nested data object.

        :param dict out: Data object to write value into.
        :param str name: Property name, with nested properties separated by dots.
        :param str value: Value to write.
        :return: None
        """

        if '.' not in name:
            out[name] = value
            return

        names = name.split('.')
        inner = out

        for i in range(len(names) - 1):
            loop_name = names[i]
            if loop_name not in inner:
                inner[loop_name] = {}
            elif not isinstance(inner[loop_name], dict):
                raise Exception(
                    'A property with the name `' + name + '` already exists. ' +
                    'This can occur if you have properties which share a prefix - ' +
                    'for example `name` and `name.first`.'
                )

            inner = inner[loop_name]

        idx = names[len(names) - 1]

        if idx in inner:
            raise Exception(
                'Duplicate field detected - a field with the name ' +
                '`' + name + '` already exists'
            )

        inner[idx] = value
