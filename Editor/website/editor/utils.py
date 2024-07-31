from typing import List

def split_table_column(full_name: str) -> List:
    """
    Split the column and table name from a string in the format "table.column".

    :param str full_name: The full name string in the format "table.column"
    :return: A list containing the column name and the table name
    :rtype: list
    """
    if '.' in full_name:
        parts = full_name.split('.')
        return [parts[1], parts[0]]
    
    return [full_name, None]