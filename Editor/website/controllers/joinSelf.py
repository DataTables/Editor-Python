from flask import Blueprint, request, jsonify
from .db import db

from ..editor import Editor, Field, Options, Validate, ValidationOptions, Formatter

joinSelf = Blueprint('joinSelf', __name__)

@joinSelf.route('/joinSelf', methods=['GET', 'POST'])
def endpoint():

    editor = Editor(db, 'users').debug(True).trace(True).fields(
        [
            Field('users.first_name'),
            Field('users.last_name'),
            Field('users.manager')
                .options(Options().table('users').value('id').label(['first_name', 'last_name'])),
            Field('manager.first_name'),
            Field('manager.last_name'),
        ]
    ).left_join('users as manager', 'users.manager', '=', 'manager.id')

    data = editor.process(request.form.to_dict())
    return jsonify(data)

