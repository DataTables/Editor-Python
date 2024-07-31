from flask import Blueprint, request, jsonify

from .db import db

from ..editor import Editor, Field, Options, Validate, ValidationOptions, Formatter

join = Blueprint('join', __name__)


@join.route('/join', methods=['GET', 'POST'])
def endpoint():
    editor = Editor(db, 'users').debug(True).trace(True).fields(
        [
            Field('users.first_name'),
            Field('users.last_name'),
            Field('users.phone'),
            Field('users.site')
                .options(Options().table('sites').value('id').label('name')),
            Field('sites.name')
        ]
    ).left_join('sites', 'sites.id', '=', 'users.site')

    data = editor.process(request.form.to_dict())
    return jsonify(data)
