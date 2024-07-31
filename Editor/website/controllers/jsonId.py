from flask import Blueprint, request, jsonify
from .db import db

from ..editor import Editor, Field, Validate, ValidationOptions, Formatter

jsonId = Blueprint('jsonId', __name__)


@jsonId.route('/jsonId', methods=['GET', 'POST'])
def endpoint():

    def get_id(val, data):
        return 'row_' + str(val)

    editor = (
        Editor(db, 'datatables_demo')
            .debug(True)
            .trace(True)
            .fields([
                Field('id').get_formatter(get_id).set(False),
                Field('first_name').validator(Validate.not_empty()),
                Field('last_name').validator(Validate.not_empty()),
                Field('position'),
                Field('office')
                    .set_formatter(Formatter.if_empty('NOT GIVEN')),
                Field('extn'),
                Field('age')
                    .validator(Validate.numeric())
                    .set_formatter(Formatter.if_empty()),
                Field('salary')
                    .validator(Validate.numeric())
                    .set_formatter(Formatter.if_empty(None)),
                Field('start_date')
                    .validator(Validate.date_format(
                        '%Y-%m-%d',
                        Validate.Options(
                            {'message': 'Incorrect data format, should be YYYY-MM-DD'})
                    ))
                    .get_formatter(Formatter.sql_date_to_format('%Y-%m-%d'))
                    .set_formatter(Formatter.format_to_sql_date('%Y-%m-%d'))
            ])
    )

    data = editor.process(request.form.to_dict())

    for item in data['data']:
        item.pop('DT_RowId', None)

    return jsonify(data)
