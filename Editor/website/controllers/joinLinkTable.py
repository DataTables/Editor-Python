from flask import Blueprint, request, jsonify
from .db import db

from ..editor import Editor, Field, Options, Validate, ValidationOptions, Formatter

joinLinkTable = Blueprint('joinLinkTable', __name__)


@joinLinkTable.route('/joinLinkTable', methods=['GET', 'POST'])
def endpoint():
    editor = Editor(db, 'users').debug(True).trace(True).fields(
        [
            Field('users.first_name'),
            Field('users.last_name'),
            Field('users.phone'),
            Field('users.site')
            .options(Options().table('sites').value('id').label('name')),
            Field('sites.name'),
            Field('user_dept.dept_id')
            .options(Options().table('dept').value('id').label('name')),
            Field('dept.name'),
        ]
    )
    editor.left_join('sites', 'sites.id', '=', 'users.site')
    editor.left_join('user_dept', 'users.id', '=', 'user_dept.user_id')
    editor.left_join('dept', 'user_dept.dept_id', '=', 'dept.id')
    editor.left_join_remove(True)

    data = editor.process(request.form.to_dict())
    return jsonify(data)
