from flask import Blueprint, request, jsonify
# import json

from .db import db

from ..editor import Editor, Field, Validate, Formatter

staff = Blueprint('staff', __name__)


@staff.route('/staff', methods=['GET', 'POST'])
def endpoint():
    # with open('/home/colin/Dropbox/Work/Languages/Python/Editor/website/db.json') as f:
    #     db = json.load(f)

    def preGet(editor, id):
        print(f'pre get {id}')
        return True

    def postGet(editor, id, data):
        print(f'post get {id}')
        return True

    def preRemove(editor, id, data):
        print(f'pre remove {id}')
        if id == '3':
            return False

        return True

    def postRemove(editor, id, data):
        print(f'post remove {id}')

    def processed(editor, action, data, response):
        print(f'processed {action}')

    def preCreate(editor, data):
        print(f'pre create {data}')

    def postCreate(editor, ids, data, submitted_data):
        print(f'post create {ids}')

    def writeCreateAll(editor, ids, submitted_data):
        print(f'write create all {ids}')

    def postCreateAll(editor, ids, data, submitted_data):
        print(f'post create all {ids}')

    editor = Editor(db, 'datatables_demo').debug(True).trace(True).fields(
        [
            Field('first_name')
                .validator(Validate.not_empty(
                    Validate.Options({'message': 'First name must not be blank'})
                )),
            Field('last_name')
                .validator(Validate.not_empty(
                    Validate.Options({'message': 'gotta be present'})
                )),
            Field('position')
                .get_formatter(Formatter.if_empty('EMPTY STRING')),
            Field('office')
                .validator(Validate.not_empty()),
            Field('extn')
                .validator(Validate.numeric(
                    cfg=Validate.Options({'message': 'gotta be numeric'})
                ))
                .validator(Validate.not_empty(
                    Validate.Options({'message': 'gotta be present'})
                ))            
                .validator(Validate.min_max_num(
                    min=1000, max=2000, cfg=Validate.Options({'message': 'gotta be in range 1000 - 2000'})
                )),
            Field('start_date')
                .validator(Validate.date_format(
                    '%Y-%m-%d',
                    Validate.Options(
                        {'message': 'Incorrect data format, should be YYYY-MM-DD'})
                ))
                .get_formatter(Formatter.sql_date_to_format('%Y-%m-%d'))
                .set_formatter(Formatter.format_to_sql_date('%Y-%m-%d')),
            Field('salary')
                .validator(Validate.numeric())
                .set_formatter(Formatter.if_empty(None)),            

        ]
    ).on('processed', processed).on('preGet', preGet).on('postGet', postGet).on('preRemove', preRemove).on('postRemove', postRemove).on('preCreate', preCreate).on('postCreateAll', postCreateAll).on('postCreate', postCreate).on('writeCreateAll', writeCreateAll)

    data = editor.process(request.form.to_dict())
    return jsonify(data)
