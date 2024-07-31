from flask import Blueprint, render_template, request, flash, jsonify, send_from_directory
from .db import db

from ..editor import Editor, Field, Validate, ValidationOptions

todo = Blueprint('todo', __name__)


@todo.route('/todo', methods=['GET', 'POST'])
def endpoint():
    editor = Editor(db, 'todo').debug(True).fields(
        [
            Field('item'),
            Field('done'),
            Field('priority')
        ]
    )

    data = editor.process(request.form.to_dict())
    return data
