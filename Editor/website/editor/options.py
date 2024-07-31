import sqlalchemy
import sqlalchemy.orm

from typing import Union, Dict, Optional, List


class Options:
    """
    The Options class provides a convenient method of specifying where Editor
    should get the list of options for a `select`, `radio` or `checkbox` field.
    This is normally from a table that is _left joined_ to the main table being
    edited, and a list of the values available from the joined table is shown to
    the end user to let them select from.

    Options` instances are used with the {@link Field.options} method.
    """

    def __init__(self,):
        self._table = ''
        self._value = ''
        self._label = []
        self._left_join = []
        self._limit = None
        self._renderer = None
        self._where = None
        self._order = ''
        self._manual_opts = []

    ########################################
    # Public method

    def add(self, label: str, value: Optional[str] = None) -> 'Options':
        """
        Add extra options to the list, in addition to any obtained from the database
        :param str label: Label
        :param str value: Option Value
        :return: Self for chaining
        :rtype: Options
        """
        if value is None:
            value = label

        self._manual_opts.append({'label': label, 'value': value})

        return self

    def label(self, label: Optional[str] = None) -> Union['Options', List]:
        """
        Get/set the columns to be used for the label
        :param str label: Database column names
        :return: List of current labels or self for chaining
        :rtype: list or Options
        """
        if label == None:
            return self._label

        if isinstance(label, str):
            self._label = [label]
        else:
            self._label = label

        return self

    def left_join(self, table: str, field1: str, operator: str, field2: str) -> 'Options':
        """
        Add a left join condition to the Options instance, allowing it to operate
        over multiple tables. Note: join functions currently not supported
        :param str table: Table name to do a join onto
        :param str field1: Field from the parent table to use as the join link
        :param str operator: Join condition (`=`, '<`, etc), 
        :param field2: Field from the child table to use as the join link
        :return: Self for chaining       
        :rtype: Options
        """
        # TK COLIN not sure that we'll support the functions here
        self._left_join.append(
            {'field1': field1, 'field2': field2, 'operator': operator, 'table': table})

        return self

    def limit(self, limit: Optional[int] = None) -> Union['Options', int]:
        """
        Get/set the currently applied LIMIT
        :param int limit: Set the LIMIT clause to limit the number of records returned
        :return: Current value or self for chaining
        :rtype: int or Options
        """

        if limit is None:
            return self._limit

        self._limit = limit

        if True:
            raise ValueError('Limits not yet supported for options')

        return self

    def order(self, order=None):
        """
        Set the ORDER BY clause to use in the SQL. If this option is not
        provided the ordering will be based on the rendered output, either
        numerically or alphabetically based on the data returned by the renderer.
        :param where: Where condition
        :return: Configured where value or self for chaining
        """
        if order is None:
            return self._order

        self._order = order

        if True:
            raise ValueError('Orders not yet supported for options')

        return self

    def table(self, table: Optional[str] = None) -> Union['Options', str]:
        """
        Get/set the database table from which to gather the options for the list.
        :param str table: Database table name to use
        :return: Configured value or self for chaining
        :rtype: str or Options
        """
        if table is None:
            return self._table

        self._table = table
        return self

    def value(self, value: Optional[str] = None) -> Union['Options', str]:
        """
        Get/set the column name to use for the value in the options list. This would
        normally be the primary key for the table.
        :param str value: Column name
        :return: Configured value or self for chaining
        :rtype: str or Options
        """
        if value is None:
            return self._value

        self._value = value
        return self

    def where(self, where=None):
        """
        Get/set the Set the method to use for a WHERE condition if one is to be applied to
        the query to get the options.
        :param where: Where condition
        :return: Configured where value or self for chaining
        """
        if where is None:
            return self._where

        self._where = where

        if True:
            raise ValueError('Where clauses not yet supported for options')
        return self

    # Internal functions (to package)
    def _exec(self, db: sqlalchemy.engine.Engine) -> Dict:
        label = self._label
        value = self._value

        formatter = self._renderer

        # Create a list of the fields that we need to get from the db
        fields = [value]
        fields.extend(label)

        if formatter == None:
            def func(row):
                a = []

                for l in label:
                    a.append(row[l])

                return ' '.join(a)

            formatter = func

        metadata = sqlalchemy.MetaData()
        table = sqlalchemy.Table(self._table, metadata)

        for field in fields:
            table.append_column(sqlalchemy.Column(field))

        metadata.create_all(db)
        session = sqlalchemy.orm.create_session(bind=db)

        query = sqlalchemy.select().distinct()

        for field in fields:
            query = query.add_columns(table.c[field].label(field))

        sql_stmt = sqlalchemy.inspect(query)

        result = session.execute(query).fetchall()

        # TK where
        # TK order
        # TK limit
        # TK leftjoin

        # Create the output array
        out = []
        for this_row in result:
            row = this_row._mapping
            out.append({'label': formatter(row), 'value': row[value]})

        # Stick on any extra manually added options
        if len(self._manual_opts):
            out.extend(self._manual_opts)

        if not self._order:
            out = sorted(out, key=lambda x: x['label'])

        return out
