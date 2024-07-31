import sqlalchemy

from .utils import split_table_column
from typing import Union, List, Optional


class Table:
    """
    A class to represent a database table using SQLAlchemy.

    Attributes:
        engine (sqlalchemy.engine.Engine): The SQLAlchemy engine to connect to the database.
        table (str): The name of the table.
        columns (list): The list of columns in the table.
        sqla (sqlalchemy.Table): The SQLAlchemy Table object.
        created (bool): Flag to indicate if the table has been created in the database.
    """

    def __init__(self, engine: sqlalchemy.engine.Engine, table: str, init: Optional[bool] = True, columns:  Optional[List] = None):
        """
        Initialize the Table instance.

        :param engine: The SQLAlchemy engine to connect to the database.
        :type engine: sqlalchemy.engine.Engine
        :param table: The name of the table.
        :type table: str
        :param init: Whether to initialize the table metadata, defaults to True.
        :type init: bool, optional
        :param columns: Optional list of columns to add to the table.
        :type columns: list, optional
        """
        self._engine = engine
        self._table = table
        self._columns = []
        self._sqla = None
        self._created = False

        if init:
            self.__init_table()

        if columns is not None:
            columns_to_add = [columns] if isinstance(columns, str) else columns
            self.columns(columns_to_add)

    def __init_table(self) -> 'Table':
        """
        Initialize the table metadata.

        :return: Self for chaining.
        :rtype: Table
        """
        self._metadata = sqlalchemy.MetaData()
        self._sqla = sqlalchemy.Table(self._table, self._metadata)

        return self

    def columns(self, columns: Optional[List] = None, pkey: Optional[bool] = False) -> Union[list, 'Table']:
        """
        Get or set columns for the table.

        :param columns: If absent, get current columns; else, a string or a list of strings for columns to add.
        :type columns: list or str, optional
        :param pkey: True if the column to add is a primary key.
        :type pkey: bool, optional
        :return: Either list of columns or self for chaining.
        :rtype: list or Table
        """
        if columns is None:
            return self._columns

        columns_to_add = [columns] if isinstance(columns, str) else columns

        for column in columns_to_add:
            # Skip columns if we've seen them before
            if column in self._columns:
                continue

            c, t = split_table_column(column)

            # Skip columns that don't belong to this table
            if t is not None and t != self._table:
                continue

            # Yep, we're good to go, so add this column
            self._columns.append(column)

            if pkey:
                self._sqla.append_column(sqlalchemy.Column(
                    c, sqlalchemy.Integer, primary_key=True))
            else:
                self._sqla.append_column(sqlalchemy.Column(c))

        return self

    def create(self) -> 'Table':
        # TK COLIN create all may actually create the table
        """
        Create the table in the database if it has not been created already.

        :return: Self for chaining.
        :rtype: Table
        """
        if not self._created:
            self._metadata.create_all(self._engine)
            self._created = True

        return self

    def get(self) -> sqlalchemy.Table:
        """
        Get the SQLAlchemy Table object.

        :return: The SQLAlchemy Table object.
        :rtype: sqlalchemy.Table
        """
        return self._sqla

    def alias(self, alias_table: str) -> 'Table':
        """
        Create an alias for the table.

        :param alias_table: The alias name for the table.
        :type alias_table: str
        :return: A new Table object with the alias.
        :rtype: Table
        """
        alias = Table(self._engine, alias_table, False)
        alias._sqla = self._sqla.alias(alias_table)

        # Adjust the alias for the table and columns (used in error handling)
        alias._table = alias_table
        alias._columns = [s.replace(self._table, alias._table)
                          for s in self._columns]

        return alias
