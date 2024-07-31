from flask import Blueprint, request, jsonify
from .db import db

from ..editor import Editor, Field, Options, Validate, ValidationOptions, Formatter

cascadingLists = Blueprint('cascadingLists', __name__)


@cascadingLists.route('/cascadingLists', methods=['GET', 'POST'])
def endpoint():

    editor = Editor(db, 'team').debug(True).trace(True).fields(
        [
            Field('team.name'),
            Field('team.continent')
            .options(Options().table('continent').value('id').label('name')),
            Field('continent.name'),
            Field('team.country')
            .options(Options().table('country').value('id').label('name')),
            Field('country.name'),
        ]
    )
    
    editor.left_join('continent', 'continent.id', '=', 'team.continent')
    editor.left_join('country', 'country.id', '=', 'team.country')

    data = editor.process(request.form.to_dict())
    return jsonify(data)
