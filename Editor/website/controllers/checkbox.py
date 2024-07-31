from flask import Blueprint, request, jsonify
# import json

from .db import db

from ..editor import Editor, Field, Validate, ValidationOptions, Formatter

checkbox = Blueprint('checkbox', __name__)

def set_formatter(val, data):
    return True if val else False
    

@checkbox.route('/checkbox', methods=['GET', 'POST'])
def endpoint():

    editor = Editor(db, 'users').debug(True).trace(True).fields(
        [
            Field('first_name'),
            Field('last_name'),
            Field('phone'),
            Field('city'),
            Field('zip'),
            Field('active')
            .set_formatter(set_formatter),
        ]
    )

    data = editor.process(request.form.to_dict())
    return jsonify(data)
