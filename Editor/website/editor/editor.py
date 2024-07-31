from sqlalchemy import create_engine, Table, MetaData, Column, Integer, String, select, or_, and_

import sqlalchemy.orm
import json
import re
import copy
import zlib

from datetime import datetime

from typing import Callable, Dict, Union, List, Optional, Any




from .field import Field
from .action import Action
from .set_type import SetType

from .nested_data import NestedData
from .table import Table
from .utils import *


class Editor(NestedData):
    """
    A class to represent an Editor that manages database operations.
    """

    # Constants
    version = '0.0.1'

    def __trace(self, string: str):
        """
        Print trace information if tracing is enabled.

        :param string: The string to print for tracing.
        :type string: str
        """
        if self._trace:
            print(string)

    def __init__(self, db: sqlalchemy.engine.Engine, table: str = None, pkey: Optional[list] = None):
        """
        Initialize the Editor instance.

        :param db: The SQLAlchemy engine or database connection.
        :type db: sqlalchemy.engine.Engine
        :param table: The name of the table.
        :type table: str, optional
        :param pkey: The primary key column(s).
        :type pkey: list, optional
        """
        # Setup initial values
        self._pkey = ['id']
        self._table = []
        self._id_prefix = 'row_'
        self._where = []
        self._join = []
        self._left_join = []
        self._debug = False
        self._trace = False
        self._fields = []
        self._debug_info = []
        self._validators = []
        self._do_validate = True
        self._custom_get = None
        self._left_join_remove = False
        self._schema = None
        self._write = True
        self._read_table_names = []
        self._events = {}

        # Get the output ready to go
        self._out = {}
        self._out['debug'] = []
        self._out['data'] = {}
        self._out['fieldErrors'] = []
        self._out['cancelled'] = []

        # Store stuff passed in
        if table is not None:
            self.table(table)

        if pkey is not None:
            self.pkey(pkey)

        self._engine = db
        self._session = sqlalchemy.orm.Session(self._engine)

    def debug(self, debug: bool = None) -> Union[bool, 'Editor']:
        """
        Get or set Editor debug. Debug is returned to the client.

        :param debug: If present, set debug value, otherwise return current value.
        :type debug: bool, optional
        :return: Either current debug value or self for chaining.
        :rtype: bool or Editor
        """

        if debug is None:
            return self._debug

        if debug is True or debug is False:
            self._debug = debug
        elif self._debug is True:
            self._debug_info.append(debug)

        return self

    def trace(self, trace: bool) -> 'Editor':
        """
        Enable or disable trace information. This is seen purely on the server.

        :param trace: True or False to enable/disable tracing.
        :type trace: bool
        :return: Self for chaining.
        :rtype: Editor
        """
        self._trace = trace
        return self

    def do_validate(self, flag: bool = None) -> Union[bool, 'Editor']:
        """
        Enable or disable validation, or get current status.

        This would be used with after the `validate` method if you call that
        before `process()`.        

        :param flag: If present, set validation flag, otherwise return current value.
        :type flag: bool, optional
        :return: Either current validation status or self for chaining.
        :rtype: bool or Editor
        """
        if flag is None:
            return self._do_validate

        self._do_validate = flag

        return self

    def action(self, data: dict) -> Action:
        """
        Determine the request type from an HTTP request.

        :param data: HTTP request - normally `request.body`. Note that
            if you are using `body-parser` you should use `{ extended: true }` as
            its options to ensure that nested properties are correctly resolved.
        :type data: dict            
        :return: Indicates what action the request is
        :rtype: Action

        """
        if 'action' not in data:
            return Action.READ

        # Note "match" was only introduced in Python 3.10
        if data['action'] == 'remove':
            return Action.DELETE
        if data['action'] == 'edit':
            return Action.EDIT
        if data['action'] == 'create':
            return Action.CREATE

        return Action.UNKNOWN

    def pkey(self, pkey: list = None) -> Union[List, 'Editor']:
        """
        Get or set primary key value(s).

        :param pkey: Primary key column name(s). Use a list of strings if using a compound key.
        :type pkey: list or str, optional
        :return: Either current primary key value or self for chaining.
        :rtype: list or Editor
        """
        if pkey is None:
            return self._pkey

        if isinstance(pkey, str):
            self._pkey = [pkey]
        else:
            self._pkey = pkey

        return self

    def _pkey_separator(self) -> str:
        """
        Get the primary key separator.

        :return: The primary key separator.
        :rtype: str
        """
        # Join the list returned by pkey() with commas
        str_val = ','.join(self.pkey())

        # Compute the CRC32 checksum
        crc32_value = zlib.crc32(str_val.encode('utf-8'))

        # Convert the CRC32 value to a hexadecimal string
        return '_' + format(crc32_value, 'x') + '_'

    def _pkey_submit_merge(self, pkey_val: str, row: dict) -> str:
        """
        Merge the primary key values.

        :param pkey_val: The primary key value.
        :type pkey_val: str
        :param row: The row data.
        :type row: dict
        :return: The merged primary key value.
        :rtype: str
        """
        pkey = self._pkey
        arr = self.pkey_to_object(pkey_val, True)

        for column in pkey:
            field = self._find_field(column, 'db')
            if field is not None and field._apply('edit', row):
                arr[column] = field.val('set', row)

        return self.pkey_to_value(arr, True)

    def pkey_to_value(self, row: dict, flat: Optional[bool] = False) -> str:
        """
        Convert a primary key array of field values to a combined value.

        :param row: The row of data that the primary key value should be extracted from.
        :type row: dict
        :param flat: Flag to indicate if the given array is flat (useful for `where` conditions) or nested for join tables.
        :type flat: bool, optional
        :return: The created primary key value.
        :rtype: str
        """
        pkey = self._pkey
        id = []

        # for i in range(len(pkey)):
        for column in pkey:
            # column = pkey[i]

            if flat:
                val = row[column] if column in row else None
            else:
                val = self._read_prop(column, row)

            if val is None:
                raise Exception(
                    "Primary key element is not available in the data set")

			# Postgres gives a `Date` object for timestamps which causes issues as
			# a value, so convert it to be a string. Could also be done with setTypeParser
			# https://github.com/brianc/node-postgres/issues/1200
            if isinstance(val, datetime):
                val = val.isoformat()			

            id.append(str(val))

        sep = self._pkey_separator()
        return sep.join(id)

    def pkey_to_object(self, value: str, flat: Optional[bool] = False, pkey: Optional[list] = None) -> Dict:
        """
        Convert a primary key combined value to an array of field values.

        :param value: The id that should be split apart.
        :type value: str
        :param flat: Flag to indicate if the given array is flat (useful for `where` conditions) or nested for join tables.
        :type flat: bool, optional
        :param pkey: The primary key name - will use the instance value if not given.
        :type pkey: list, optional
        :return: Array of field values that the id was made up of.
        :rtype: dict
        """
        arr = {}

        value = value.replace(self.id_prefix(), '')
        id_parts = value.split(self._pkey_separator())

        if pkey is None:
            pkey = self.pkey()

        if len(pkey) != len(id_parts):
            raise Exception("Primary key data does not match submitted data")

        for i in range(len(id_parts)):
            if flat:
                arr[pkey[i]] = id_parts[i]
            else:
                self._write_prop(arr, pkey[i], id_parts[i])

        return arr

    def field(self, field: Union[None, str] = None) -> Union[Field, 'Editor']:
        """
        Get specific field or add to the fields assigned to this instance.

        :param field: Field name to get, or None to add a field.
        :type field: str, optional
        :return: Getting returns the specified field, otherwise self for chaining.
        :rtype: Field or Editor
        """
        if isinstance(field, str):
            for fld in self._fields:
                if fld.name() == field:
                    return fld

            raise Exception("Unknown field: " + field)

        self._fields.append(field)

        return self

    def fields(self, fields: Optional[list] = None) -> Union[list, 'Editor']:
        """
        Get or add to the fields assigned to this instance.

        :param fields: Fields to add, or None to return current fields.
        :type fields: list, optional
        :return: Getting returns current fields, otherwise self for chaining.
        :rtype: list or Editor
        """
        if fields is None or len(fields) == 0:
            return self._fields

        self._fields += fields

        return self

    def get(self, fn: callable) -> 'Editor':
        """
        Set a custom get function.

        :param fn: The custom get function.
        :type fn: callable
        :return: Self for chaining.
        :rtype: Editor
        """
        self._custom_get = fn
        return self

    def id_prefix(self, id: str = None) -> Union[str, 'Editor']:
        """
        Get the id prefix.

        Typically primary keys are numeric and this is not a valid ID value in an
        HTML document - it also increases the likelihood of an ID clash if multiple
        tables are used on a single page. As such, a prefix is assigned to the
        primary key value for each row, and this is used as the DOM ID, so Editor
        can track individual rows.        

        :param id: None returns current prefix, otherwise set with new value.
        :type id: str, optional
        :return: Either current id or self for chaining.
        :rtype: str or Editor
        """
        if id is None:
            return self._id_prefix

        self._id_prefix = id

        return self

    def inData(self) -> Dict:
        """
        Get the data that is being processed by the Editor instance. This is only
        useful once the `process()` method has been called, and is available for
        use in validation and formatter methods.

        :return: Data that has been passed into process.
        :rtype: dict
        """
        return self._process_data

    def join(self, join: List = None) -> Union[List, 'Editor']:
        """
        Get the configured Mjoin instances.

        Note that for the majority of use cases you will want to use the
        `left_join()` method. It is significantly easier to use if you are just
        doing a simple left join!

        The list of Join instances that Editor will join the parent table to
        (i.e. the one that the {@link Editor.table} and {@link Editor.fields}
        methods refer to in this class instance).

        :return: Array of Mjoin instances, or self for chaining
        """

        if join == None or len(join) == 0:
            return self._join

        self._join += join

        return self

    def left_join(self, table: str, field1: str, operator: str = None, field2: str = None) -> 'Editor':
        """
        Add a left join condition to the Editor instance, allowing it to operate
        over multiple tables. Multiple `left_join()` calls can be made for a
        single Editor instance to join multiple tables.

        A left join is the most common type of join that is used with Editor
        so this method is provided to make its use very easy to configure. Its
        parameters are basically the same as writing an SQL left join statement,
        but in this case Editor will handle the create, update and remove
        requirements of the join for you:

        * Create - On create Editor will insert the data into the primary table
        and then into the joined tables - selecting the required data for each
        table.
        * Edit - On edit Editor will update the main table, and then either
        update the existing rows in the joined table that match the join and
        edit conditions, or insert a new row into the joined table if required.
        * Remove - On delete Editor will remove the main row and then loop over
        each of the joined tables and remove the joined data matching the join
        link from the main table.

        Please note that when using join tables, Editor requires that you fully
        qualify each field with the field's table name. SQL can result table
        names for ambiguous field names, but for Editor to provide its full CRUD
        options, the table name must also be given. For example the field
        `first_name` in the table `users` would be given as `users.first_name`.   

        :param table: Table name to do a join onto.
        :type table: str
        :param field1: Field from the parent table to use as the join link.
        :type field1: str
        :param operator: Join condition (`=`, '<`, etc).
        :type operator: str, optional
        :param field2: Field from the child table to use as the join link.
        :type field2: str, optional
        :return: Self for chaining.
        :rtype: Editor
        """
        if hasattr(field1, '__call__'):
            raise Exception(
                'Left joins with functions not currently supported')
        else:
            self._left_join.append(
                {'field1': field1, 'field2': field2, 'operator': operator, 'table': table})

        return self

    def left_join_remove(self, remove: bool = None) -> Union[List, 'Editor']:
        """
        Indicate if a remove should be performed on left joined tables when deleting
        from the parent row. Note that this is disabled by default and will be
        removed completely in v2. Use `ON DELETE CASCADE` in your database instead.

        :param remove: Value to set, or None to get the current value.
        :type remove: bool, optional
        :return: Current value, or self for chaining.
        :rtype: bool or Editor
        """
        if not remove:
            return self._left_join_remove

        self._left_join_remove = remove

        return self

    def on(self, name: str, callback: Callable) -> 'Editor':
        """
        Add an event listener.

        The `Editor` class will trigger an number of events that some action can be taken on.

        :param name: Event name.
        :type name: str
        :param callback: Event callback function that will be executed when the event occurs.
        :type callback: callable
        :return: Self for chaining.
        :rtype: Editor
        """
        if name not in self._events:
            self._events[name] = []

        self._events[name].append(callback)

        return self

    def schema(self, schema=None) -> Union[str, 'Editor']:
        """
        Set or get the database schema.

        This is used if you are using multiple schema's in your database. By default Editor
        will not specify a schema, so the default search path will be used. This allows that
        to be overridden.        

        :param schema: Schema to use, or None to get the current schema.
        :type schema: str, optional
        :return: Self for chaining.
        :rtype: str or Editor
        """
        if schema is None:
            return self._schema

        self._schema = schema

        return self

    def read_table(self, table: Optional[Union[str, List[str]]] = None) -> Union[List, 'Editor']:
        """
        Get or set CRUD read table name.

        If this method is used, Editor will create from the table name(s) given rather
        than those given by `Editor->table()`. This can be a useful distinction to allow
        a read from a VIEW (which could make use of a complex SELECT) while writing to
        a different table.       

        :param table: Database table name to use for reading from, or None to get current read table names.
        :type table: str or list, optional
        :return: Self for chaining.
        :rtype: list or Editor
        """

        if table is None or len(table) == 0:
            return self._read_table_names

        if isinstance(table, str):
            self._read_table_names.append(table)
        else:
            self._read_table_names += table

        return self

    def table(self, table: Optional[Union[str, List[str]]] = None) -> Union[str, List[str], 'Editor']:
        """
        Get or set the table name.

        The table name designated which DB table Editor will use as its data
        source for working with the database. Table names can be given with an
        alias, which can be used to simplify larger table names. The field
        names would also need to reflect the alias, just like an SQL query. For
        example: `users as a`.  

        :param table: Database table name(s) to use
        :return: Self for chaining if setting a table, otherwise the current table name(s)
        """

        if table is None or len(table) == 0:
            return self._table

        if isinstance(table, str):
            self._table.append(table)
        else:
            self._table += table

        return self

    def _trigger(self, name: str, *args: Any) -> Optional[Any]:
        """
        Trigger an event by name.

        :param name: Name of the event to trigger
        :param args: Arguments to pass to the event handlers
        :return: Result of the event handler if any, otherwise None
        """
        out = None

        if name not in self._events:
            return

        for event in self._events[name]:
            res = event(self, *args)
            if res != None:
                out = res

        return out

    def _update(self, orig_id: str, values: Dict[str, Any]) -> str:
        """
        Update a record by ID.

        :param orig_id: Original ID of the record
        :param values: Dictionary of values to update
        :return: Updated ID
        """
        id = orig_id.replace(self.id_prefix(), '')

        self._trigger('validateEdit', id, values)

        # Update or insert the rows for the parent table and the left joined
        # tables
        self._insert_or_update(id, values)

        for join in self._join:
            join.update(self, id, values)

        # Was the primary key altered as part of the edit, if so use the
        # submitted values
        get_id = self._pkey_submit_merge(id, values)

        self._trigger('writeEdit', id, values)

        return get_id

    def _upload(self, data: Any) -> None:
        """
        Handle file uploads.

        :param data: Data to upload
        """
        pass

    def __file_clean(self) -> None:
        """
        Clean up files.
        """
        pass

    def __file_data(self, limit_table: Optional[str] = None, ids: Optional[List[str]] = None, data: Optional[Any] = None) -> None:
        """
        Get file data.

        :param limit_table: Table to limit the query to
        :param ids: List of IDs to query
        :param data: Additional data for the query
        """
        pass

    def __file_data_fields(self, limit_table: Optional[str] = None, ids: Optional[List[str]] = None, data: Optional[Any] = None) -> None:
        """
        Get file data fields.

        :param limit_table: Table to limit the query to
        :param ids: List of IDs to query
        :param data: Additional data for the query
        """
        pass

    def _find_field(self, name: str, type: str) -> Optional[Field]:
        """
        Find a field by name or database field name.

        :param name: Field name to search for
        :param type: Type of name to search for ('name' or 'db')
        :return: Found field or None if not found
        """
        for field in self._fields:
            if field is None:
                continue

            if type == 'name' and field.name() == name:
                return field

            if type == 'db' and field.db_field() == name:
                return field

        return None

    def __add_to_query(self, query: sqlalchemy.sql.Select, field: str, primary_table: str, tables: Dict[str, Table]) -> sqlalchemy.sql.Select:
        """
        Add a field to the query.

        :param query: SQLAlchemy Select object
        :param field: Field name to add
        :param primary_table: Primary table name
        :param tables: Dictionary of table objects
        :return: Updated query
        """
        c, t = split_table_column(field)

        if t is None:
            t = primary_table

        if t not in tables:
            raise ValueError(f'Table "{t}" being referenced but undefined')

        if field not in tables[t].columns():
            raise ValueError(
                f'Column "{field}" being referenced but undefined')

        query = query.add_columns(tables[t].get().c[c].label(field))

        return query

    def __get_table_from_join(self, joined_table: str) -> str:
        """
        Get the table name from a joined table string.

        :param joined_table: Joined table string
        :return: Table name
        """
        if joined_table.lower().find(' as ') == -1:
            return joined_table
        else:
            a = joined_table.split(' ')
            return a[2]

    def __get(self, id: Optional[Union[str, List[str]]] = None, http: Optional[Any] = None) -> Dict[str, Any]:
        """
        Get records by ID or HTTP request.

        :param id: ID(s) of the record(s) to get
        :param http: HTTP request object
        :return: Dictionary of records
        """
        response = {}
        options = {}

        cancel = self._trigger('preGet', id)
        if (cancel is False):
            return {}

        if self._custom_get is not None:
            response = self._custom_get(id, http)
        else:
            fields = self.fields()

            # Generate primary table object
            table = self.table()[0]

            # An array of table objects
            tables = {}
            tables[table] = self.__get_table(table)

            # And now generate the join table objects - leave aliases until the end
            alias_tables = []

            for left_join in self._left_join:
                joined_table = left_join['table']

                # Check for aliases
                if joined_table.lower().find(' as ') == -1:
                    if joined_table not in tables:
                        tables[joined_table] = self.__get_table(joined_table)
                else:
                    a = joined_table.split(' ')
                    alias_tables.append([a[0], a[2]])

            for alias in alias_tables:
                if alias[0] not in tables:
                    raise ValueError(
                        'Alias "' + alias[0] + '" present but table not defined')

                tables[alias[1]] = tables[alias[0]].alias(alias[1])
                # tables[alias[1]] .alias()

            # Now build up the query
            query = sqlalchemy.select()

            # pkeys first
            for pkey in self._pkey:
                query = self.__add_to_query(query, pkey, table, tables)

            # ... then the fields, unless they're also pkeys
            for field in self._fields:
                db_field = field.db_field()
                if db_field not in self._pkey:
                    query = self.__add_to_query(
                        query, field.db_field(), table, tables)

            for left_join in self._left_join:
                jt = self.__get_table_from_join(left_join['table'])

                if jt == split_table_column(left_join['field1'])[1]:
                    lc, lt = split_table_column(left_join['field1'])
                    rc, rt = split_table_column(left_join['field2'])
                else:
                    lc, lt = split_table_column(left_join['field2'])
                    rc, rt = split_table_column(left_join['field1'])

                query = query.join(
                    tables[lt].get(), tables[lt].get().c[lc] == tables[rt].get().c[rc], isouter=True
                )

            if id is not None:
                # Put IDs into an array an iterate through
                id_list = id if isinstance(id, list) else [id]

                or_conditions = []

                for i in id_list:
                    and_conditions = []

                    idvals = self.pkey_to_object(i, True)

                    # COLIN POSTGRES
                    for idval in idvals:
                        pk = split_table_column(idval)[0]
                        val = idvals[idval]
                        and_conditions.append(
                            tables[table].get().c[pk].__eq__(val))

                    or_conditions.append(and_(*and_conditions))

                query = query.where(or_(*or_conditions))

            sql_stmt = str(query.compile(
                compile_kwargs={"literal_binds": True}))
            print(sql_stmt)

            # Execute the query and fetch results
            result = self._session.execute(query).fetchall()

            # Field options and SearchPane options (TK)
            if id == None:
                for field in fields:
                    opts = field._options_exec(self._engine)
                    if opts != None:
                        options[field.name()] = opts

            # TK not sure if this is a good idea here - will it be used later?
            self._session.close()

            self.__trace(result)
            self.debug(str(sql_stmt))

            out = []
            for this_row in result:
                # The_mapping contains an object with the key/value
                row = this_row._mapping
                val = self.pkey_to_value(row, True)
                inner = {"DT_RowId":  self.id_prefix() + val}

                for field in self._fields:
                    if field._apply('get') and field.http():
                        field._write(inner, row)

                out.append(inner)

            # Build a DT respobnse object
            response = {
                'data': out,
                # 'draw': None,
                # 'files': {},
                'options': options
                # 'recordsFiltered': None,
                # 'recordstotal': None,
                # 'searchPanes': None,
                # 'searchBuilder': None,
            }

            # TK stuff for row based joins

        self.__trace(response)

        self._trigger('postGet', id, response['data'])
        return response

    def _insert(self, values: Dict[str, Any]) -> Optional[str]:
        """
        Insert a new record.

        :param values: Dictionary of values to insert
        :return: Inserted ID
        """
        # Get values to generate the id, including from setValue, not just the submitted values
        all = {}

        for field in self._fields:
            val = field.val('set', values)
            if val is not None:
                self._write_prop(all, field.name(), val)

        # Only allow a composite insert if the values for the key are
        # submitted. This is required because there is no reliable way in MySQL
        # to return the newly inserted row, so we can't know any newly
        # generated values.
        self._pkey_validate_insert(all)

        self._trigger('validatedCreate', values)

        # Insert the new row
        id = self._insert_or_update(None, values)
        if id is None:
            return None

        # Was the primary key altered as part of the edit, if so use the submitted values
        id = self.pkey_to_value(all) if len(
            self._pkey) > 1 else self._pkey_submit_merge(id, all)

        # Join
        for i in range(len(self._join)):
            self._join[i].create(self, id, values)

        self._trigger('writeCreate', id, values)

        return id

    def _insert_or_update(self, id: Optional[str], values: Dict[str, Any]) -> Optional[str]:
        """
        Insert or update records in the database.

        :param id: The ID of the record to update, or None for a new record.
        :param values: Dictionary of values to insert or update.
        :return: The ID of the inserted or updated record, or None if no operation was performed.
        """
        # Loop over the tables, doing the insert or update as needed
        tables = self.table()
        for table in tables:
            res = self._insert_or_update_table(
                table, values, self.pkey_to_object(id, True) if id is not None else None)

            # If you don't have an id yet, then the first insert will return the id we want
            if res is not None and id is None:
                id = res

        # And for the left join tables
        for join in self._left_join:
            # Which side of the join refers to the parent table?
            join_table = self.__alias(join['table'], 'alias')
            table_part = self._part(join['field1'])
            parent_link = None
            child_link = None
            where_val = None

            if self._part(join['field1'], 'db'):
                table_part = self._part(
                    join['field1'], 'db') + '.' + table_part

            if table_part == join_table:
                parent_link = join['field2']
                child_link = join['field1']
            else:
                parent_link = join['field1']
                child_link = join['field2']

            if parent_link == self._pkey[0] and len(self._pkey) == 1:
                where_val = id
            else:
                # We need submitted information about the joined data to be
                # submitted as well as the new value. We first check if the
                # host field was submitted
                field = self._find_field(parent_link, 'db')

                if not field or not field._apply('edit', values):
                    # If not, then check if the child id was submitted
                    field = self._find_field(child_link, 'db')

                    if not field or not field._apply('edit', values):
                        # No data available, so we can't do anything
                        continue

                where_val = field.val('set', values)

            where_name = self._part(child_link, 'column')

            self._insert_or_update_table(join['table'], values, {
                                         where_name: where_val})

        return id

    def _insert_or_update_table(self, table: str, values: Dict[str, Any], where: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        Insert or update a table in the database.

        :param table: The name of the table.
        :param values: Dictionary of values to insert or update.
        :param where: The condition for updating records, or None to insert new records.
        :return: The ID of the inserted or updated record, or None if no operation was performed.
        """
        set = {}
        action = 'create' if where is None else 'edit'
        table_alias = self.__alias(table, 'alias')

        for field in self._fields:
            table_part = self._part(field.db_field())

            part = self._part(field.db_field(), 'db')
            if part is not  None:
                table_part = part + '.' + table_part

            # Does this field apply to the table (only check when a join is being used)
            if len(self._left_join) and table_part != table_alias:
                continue

            # Check if this field should be set, based on options and submitted data
            if not field._apply(action, values):
                continue

            # Some database's (specifically pg) don't like having the table
            # name prefixing the column name.
            field_part = self._part(field.db_field(), 'column')
            set[field_part] = field.val('set', values)

        if len(set) == 0:
            return None

        sqla_table = self.__get_table(table).get()

        if action == 'create' and table in self.table():
            # On the main table we get the pkey that is generated
            stmt = sqla_table.insert().values(set)

            self.debug(str(stmt.compile()))
            self.debug(str(stmt.compile().params))

            res = self._session.execute(stmt)
            self._session.commit()

            # session.close()

            return str(res.inserted_primary_key[0])

        elif action == 'create':
            # Create on a linked table
            stmt = sqla_table.insert().values(set)

            self.debug(str(stmt.compile()))
            self.debug(str(stmt.compile().params))

            res = self._session.execute(stmt)
            self._session.commit()

            # session.close()

        elif table not in self.table():
            # Update on a linked table - the record might not yet exist, so need to check.
            stmt = sqla_table.select()

            for wk in list(where.keys()):
                c = split_table_column(wk)[0]
                stmt = stmt.where(sqla_table.c[c] == where[wk])

            self.debug(str(stmt.compile()))
            self.debug(str(stmt.compile().params))

            res = self._session.execute(stmt).fetchall()

            if len(res):
                # Nope, so do the update
                stmt = sqla_table.update().values(set)

                for wk in list(where.keys()):
                    c = split_table_column(wk)[0]
                    stmt = stmt.where(sqla_table.c[c] == where[wk])

                self.debug(str(stmt.compile()))
                self.debug(str(stmt.compile().params))

                res = self._session.execute(stmt)
                self._session.commit()

            else:
                # insert the combined values of the set and where info
                stmt = sqla_table.insert().values({**set, **where})

                self.debug(str(stmt.compile()))
                self.debug(str(stmt.compile().params))

                res = self._session.execute(stmt)
                self._session.commit()

            # session.close()

        else:
            stmt = sqla_table.update().values(set)

            for wk in list(where.keys()):
                c = split_table_column(wk)[0]
                stmt = stmt.where(sqla_table.c[c] == where[wk])

            self.debug(str(stmt.compile()))
            self.debug(str(stmt.compile().params))

            res = self._session.execute(stmt)
            self._session.commit()

            # session.close()

        return None

    def __get_table(self, requested_table: Optional[str] = None, requested_fields: Optional[List[str]] = None) -> Table:
        """
        Get a table object that contains the SQLAlchemy table setup.

        :param requested_table: Use requested table if given, otherwise use the one configured.
        :param requested_fields: Use requested fields if given, otherwise use the ones configured.
        :return: SQLAlchemy Table object.
        """
        # Use requested table if given, otherwise use the one configured
        table = self._table[0] if requested_table is None else requested_table

        table = Table(self._engine, table)

        # Use requested fields if given, otherwise use the ones configured
        if requested_fields is None:
            # Add all known fields in this config - pkeys first
            for pkey in self._pkey:
                table.columns(pkey, True)

            # ... then all other configured fields
            for field in self._fields:
                table.columns(field.db_field())

            # ... and finally go through the joins
            for left_join in self._left_join:
                table.columns(left_join['field1'])
                table.columns(left_join['field2'])

        else:
            table.columns(requested_fields)

        # TK COLIN not sure if we need this, it might create the table
        # table.create()

        return table

    def __alias(self, name: str, type: Optional[str] = 'alias') -> str:
        """
        Get the alias or original name of a table or field.

        :param name: The name of the table or field.
        :param type: Either 'alias' (default) or 'orig'.
        :return: The alias or original name.
        """
        if name.lower().find(' as ') != -1:
            a = name.lower().split(' as ')
            return a[1] if type == 'alias' else a[0]

        if ' ' in name:
            a = name.split(' ')
            return a[1] if type == 'alias' else a[0]

        return name
    
    def _part(self, name: str, type: Optional[str] = 'table') -> Optional[str]:
        """
        Get the specified part of a field name.

        :param name: The name of the field.
        :param type: Either 'table' (default), 'db', or 'column'.
        :return: The specified part of the field name.
        """

        db, table, column = None, None, None

        if '.' in name:
            a = name.split('.')
            if len(a) == 3:
                db, table, column = a[0], a[1], a[2]
            elif len(a) == 2:
                table, column = a[0], a[1]
        else:
            column = name

        if type == 'db':
            return db

        if type == 'table':
            return table

        return column

    def _prep_join(self) -> None:
        """
        Prepare join conditions for the query.
        """
        if len(self._left_join) == 0:
            return

        # Check if the primary key has a table identifier - if not - add one
        for i in range(len(self._pkey)):
            val = self._pkey[i]
            if '.' not in val:
                self._pkey[i] = self.__alias(
                    self.table()[0], 'alias') + '.' + val

        # Check that all fields have a table selector, otherwise, we'd need to
        # know the structure of the tables, to know which fields belong in
        # which. This extra requirement on the fields removes that
        for field in self._fields:
            name = field.db_field()

            if '.' not in name:
                raise ValueError('Table part of the field "{}" was not found. '
                                 'In Editor instances that use a join, all fields must have the '
                                 'database table set explicitly.'.format(name))

        return

    def _read_table(self) -> List[str]:
        """
        Get the table names to be read from.

        :return: List of table names.
        """
        return self._read_table_names if len(self._read_table_names) else self._table
    
    def __remove(self, data: Dict[str, Any]) -> None:
        """
        Remove records from the database.

        :param data: Data containing the records to remove.
        """
        ids = []
        keys = data['data'].keys()

        for key in keys:
            # Strip the ID prefix that the client-side sends back
            id = key.replace(self.id_prefix(), '')

            res = self._trigger('preRemove', id, data['data'][key])
            if res == False:
                self._out['cancelled'].append(id)
            else:
                ids.append(id)

        if len(ids) == 0:
            return

        # Row based joins - remove first as the host row will be removed which is a dependency
        for join in self._join:
            join.remove(self, ids)

        if self._left_join_remove:
            for join in self._left_join:
                # Which side of the join refers to the parent table?
                if join['field1'].startswith(join['table']):
                    parent_link = join['field2']
                    child_link = join['field1']
                else:
                    parent_link = join['field1']
                    child_link = join['field2']

                # Only delete on the primary key, since that is what the ids refer
                # to - otherwise we'd be deleting random data! Note that this
                # won't work with compound keys since the parent link would be
                # over multiple fields.
                if parent_link == self._pkey[0] and len(self._pkey) == 1:
                    self.__remove_table(join['table'], ids, [child_link])

        tables = self.table()
        for table in tables:
            self.__remove_table(table, ids)

        for id in ids:
            self._trigger('postRemove', id,
                          data['data'][self.id_prefix() + id])

        self._trigger('postRemoveAll', ids, data)

    def __remove_table(self, table: str, ids: List[str], pkey: Optional[List[str]] = None) -> None:
        """
        Remove records from a specific table.

        :param table: The name of the table.
        :param ids: List of record IDs to remove.
        :param pkey: Primary key fields, if different from the default.
        """
        if pkey is None:
            pkey = self.pkey()

        count = 0
        fields = self.fields()
        table_alias = self.__alias(table, 'alias')
        table_orig = self.__alias(table, 'orig')

        # Check that there is actually a field which has a set option for this table
        for field in fields:
            db_field = field.db_field()
            if '.' not in db_field or (self._part(db_field, 'table') == table_alias and field.set() != SetType.NONE):
                count += 1

        if count > 0:
            sqla_table = self.__get_table(table_orig).get()
            ids_to_delete = []

            for id in ids:
                cond = self.pkey_to_object(id, True, pkey)
                ids_to_delete.append(cond[pkey[0]])

            try:
                c, t = split_table_column(pkey[0])
                stmt = sqla_table.delete().where(
                    sqla_table.c[c].in_(ids_to_delete))

                sql_stmt = str(stmt.compile(
                    compile_kwargs={"literal_binds": True}))
                self.debug(str(sql_stmt))

                res = self._session.execute(stmt)
                # TK COLIN need to add some error handling into this
                # https://docs.sqlalchemy.org/en/20/tutorial/data_update.html#tutorial-update-delete-rowcount
                # can check this to determine iif the operation worked - =0 fail, >0 success
                # print(res.rowcount)
                self._session.commit()
            except Exception as e:
                # TK COLIN do something here
                self._trace(e)
                pass

    def _validate(self, errors: List[Dict[str, Any]], data: Dict[str, Any], action: Action) -> bool:
        """
        Internal version of validate. See comment for validate() for more info.

        :param errors: List to store validation errors.
        :param data: Data to validate.
        :param action: Action type (create or edit).
        :return: True if valid, False otherwise.
        """
        if self._do_validate is False:
            return True

        if action not in {Action.CREATE, Action.EDIT}:
            return True

        fields = self.fields()

        # cycle through all the ids in the request
        for id in data['data']:
            values = data['data'][id]

            # then go through all the fields
            for field in fields:
                validation = field._validate(values, self, id, action)
                if validation != True:
                    errors.append({
                        'id': id,
                        'name': field.db_field(),
                        'status': validation
                    })

            # TK MJoin validation

        return False if len(errors) > 0 else True

    def validate(self, errors: List[Dict[str, Any]], http: Dict[str, Any]) -> bool:
        """
        Perform validation on a data set.

        Note that validation is performed on data only when the action is
        `create` or `edit`. Additionally, validation is performed on the _wire
        data_ - i.e. that which is submitted from the client, without formatting.
        Any formatting required by `setFormatter` is performed after the data
        from the client has been validated.
        :param errors: Output array to which field error information will
            be written. Each element in the array represents a field in an error
            condition. These elements are themselves arrays with two properties
            set; `name` and `status`.
        :param http: The format data to check
        :return: `true` if the data is valid, `false` if not.
        """
        action = self.action(http)
        dict = self.__convert_data_to_dict(http)
        return self._validate(errors, dict, action)

    def validator(self, fn: Optional[callable] = None) -> Union[List[Callable], 'Editor']:
        """
        Get any global validator that has been set, or set one.

        :param fn: Function to execute when validating the input data.
        :return: Current validators or self for chaining.
        """
        if fn is None:
            return self._validators

        self._validators.append(fn)

        return self

    def write(self, val: Optional[bool] = None) -> Union[bool, 'Editor']:
        """
        Getter/Setter for this._write which is used to decide which actions to allow.

        :param val: Value for writing, True or False, or None if getter.
        :return: Current value if getter or self for chaining.
        """
        if val is None:
            return self._write

        if isinstance(val, bool):
            self._write = val

        return self

    def _pkey_validate_insert(self, row: Dict[str, Any]) -> bool:
        """
        Validate primary key for insert operation.

        :param row: Data row to validate.
        :return: True if valid, raises Exception otherwise.
        """
        pkey = self.pkey()

        if len(pkey):
            return True

        for column in pkey:
            field = self._find_field(column, 'db')

            if field is None or field.apply('create', row):
                raise Exception("""
When inserting into a compound key table,
all fields that are part of the compound key must be
submitted with a specific value.                                
                                """)

        return True

    def __process(self, data: Dict[str, Any], upload: Optional[Dict[str, Any]]) -> None:
        """
        Process the given data for create, edit, or delete operations.

        :param data: Data to process.
        :param upload: Upload data, if any.
        """
        self._process_data = data
        self._upload_data = upload
        self._prep_join()

        for validator in self._validators:
            ret = validator(self, data['action']
                            if 'action' in data else 'read', data)
            if type(ret) == str:
                self._out['error'] = ret
                break

        action = self.action(data)
        if 'action' in data and action != Action.UPLOAD and len(data['data']) == 0:
            self._out['error'] = 'No data detected. Have you used {extended: true} for `bodyParser`?'

        if 'error' not in self._out:
            if action == Action.READ:
                out_data = self.__get(None, data)
                for key, value in out_data.items():
                    self._out[key] = value
            elif action == Action.UPLOAD and self._write:
                self._upload(data)
            elif action == Action.DELETE and self._write:
                self.__remove(data)
                self.__file_clean()
            elif (action == Action.EDIT or action == Action.CREATE) and self._write:
                keys = data['data'].keys()
                eventName = 'Create' if action == Action.CREATE else 'Edit'

                # Pre events so they can occur before validation, and they all happen together
                for id_src in keys:
                    cancel = None
                    values = data['data'][id_src]

                    if action == Action.CREATE:
                        cancel = self._trigger('preCreate', values)
                    else:
                        id = id_src.replace(self.id_prefix(), '')
                        cancel = self._trigger('preEdit', id, values)

                    # If one of the event handlers returned false - don't continue
                    if cancel == False:
                        # Remove the data from the data set so it won't be processed
                        data['data'].pop(id_src)

                        # Tell the client-side we aren't updating this row
                        self._out['cancelled'].append(id_src)

                # Field validation
                valid = self._validate(self._out['fieldErrors'], data, action)

                pkeys = []
                just_keys = []

                if valid:
                    keys = data['data'].keys()

                    # Perform db insert / update
                    for key in keys:
                        values = data['data'][key]
                        pkey = self._insert(
                            values) if action == Action.CREATE else self._update(key, values)

                        # submit_key could be array index (create)
                        just_keys.append(pkey)
                        pkeys.append(
                            {
                                'data_key': self.id_prefix() + pkey,
                                'pkey': pkey,
                                'submit_key': key
                            }
                        )

                    # Remap the submitted data from the submitted key to the row id
                    # This isn't just row id without the prefix, since the create is
                    # array indexed
                    submitted_data = {}

                    for key in keys:
                        for p in pkeys:
                            if p['submit_key'] == key:
                                submitted_data[p['pkey']] = data['data'][key]

                    # All writes done - trigger `All`
                    self._trigger(f'write{eventName}All',
                                  just_keys, submitted_data)

                    # Get the data that was updated in a single query
                    return_data = self.__get(just_keys)
                    self._out['data'] = return_data['data']

                    # post events
                    for key in pkeys:
                        self._trigger(f'post{eventName}', key['pkey'], data['data'][key['submit_key']],
                                      list(filter(lambda rec: rec['DT_RowId'] == key['data_key'], return_data['data'])))

                    self._trigger(f'post{eventName}All', just_keys,
                                  submitted_data, return_data['data'])

                    # File tidy up
                    self.__file_clean()

        self._trigger('processed', action, data, self._out)

        self._out['debug'] = self._debug_info

    def __convert_data_to_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert data keys from string format to nested dictionary format.

        :param data: Data with string keys.
        :return: Data as nested dictionary.
        """
        # strings are in the format "data[57][last_name]"
        nested_dict = {}
        for key, value in data.items():
            keys = key.split('[')
            current_dict = nested_dict
            for k in keys[:-1]:
                k = k.rstrip(']')
                current_dict = current_dict.setdefault(k, {})
            current_dict[keys[-1].rstrip(']')] = value

        return nested_dict

    def process(self, data: Dict[str, Any], files: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process incoming data and files.

        :param data: Data to process.
        :param files: Files to process, if any.
        :return: Output data after processing.
        """
        self.debug('Editor Python libraries - version ' + self.version)

        # Convert the strings into a nested dictionary
        dict = self.__convert_data_to_dict(data)
        self.__trace(dict)

        self.__process(dict, files)

        self.__trace(self._out)

        return self._out
