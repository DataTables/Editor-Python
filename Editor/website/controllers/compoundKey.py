from flask import Blueprint, request, jsonify
# import json

from .db import db
from sqlalchemy import text
from sqlalchemy import create_engine, select, func, Table, MetaData, Column
from sqlalchemy.orm import sessionmaker

from ..editor import Editor, Field, Options, Validate, ValidationOptions, Formatter

# The key thing to note for compound key support is the use of an array as the
# third parameter for the Editor constructor, which is used to tell Editor what
# the primary key column(s) are called (default is just `id`).

# TK COLIN multi-editing on the date gives an errorm, but same as existing scripts
compoundKey = Blueprint('compoundKey', __name__)


@compoundKey.route('/compoundKey', methods=['GET', 'POST'])
def endpoint():

    def do_query(editor, user_id, visit_date):
        metadata = MetaData()
        users_visits = Table(
            'users_visits',
            metadata,
            autoload_with=editor._engine
        )

        stmt = select(users_visits.c.user_id).where(
            (users_visits.c.user_id == user_id) &
            (users_visits.c.visit_date == visit_date)
        )

        result = editor._session.execute(stmt).scalar()
        return result

    def validate(editor, action, data):

        if action == "create":
            keys = list(data['data'].keys())

            for key in keys:
                values = data['data'][key]['users_visits']

                # If there was a matching row, then report it as an error
                result = do_query(
                    editor, values['user_id'], values['visit_date'])
                if result != None:
                    return 'This staff member is already busy that day'

        elif action == "edit":
            keys = list(data['data'].keys())

            for key in keys:
                values = data['data'][key]['users_visits']
                pkey = editor.pkey_to_object(key)['users_visits']

                # Discount the row being edited
                if (
                    pkey['user_id'] != values['user_id'] or
                    pkey['visit_date'] != values['visit_date']
                ):
                    # If there was a matching row, then report it as an error
                    result = do_query(
                        editor, values['user_id'], values['visit_date'])
                    if result != None:
                        return 'This staff member is already busy that day'

    editor = (
        Editor(db, 'users_visits', ['user_id', 'visit_date'])
        .debug(True)
        .trace(True)
        .fields([
                Field('users_visits.user_id')
                .options(
                    Options()
                    .table('users')
                    .value('id')
                    .label(['first_name', 'last_name'])
                )
                .validator(Validate.db_values()),

                Field('users_visits.site_id')
                .options(
                    Options()
                    .table('sites')
                    .value('id')
                    .label('name')
                )
                .validator(Validate.db_values()),

                Field('users_visits.visit_date')
                .validator(
                    Validate.date_format(
                        "%Y-%m-%d",
                        cfg=Validate.Options(
                            {'message': 'Please enter a date in the format yyyy-mm-dd'}
                        )
                    )
                )
                .get_formatter(Formatter.sql_date_to_format("%Y-%m-%d"))
                .set_formatter(Formatter.format_to_sql_date("%Y-%m-%d")),

                Field('sites.name').set(False),
                Field('users.first_name').set(False),
                Field('users.last_name').set(False)
                ])
    )

    editor.left_join('sites', 'users_visits.site_id', '=', 'sites.id')
    editor.left_join('users', 'users_visits.user_id', '=', 'users.id')
    editor.validator(validate)

    data = editor.process(request.form.to_dict())
    return jsonify(data)
