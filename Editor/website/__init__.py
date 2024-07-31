from flask import Flask
from os import path


def create_app():
    app = Flask(__name__)

    from .examples import examples
    from .controllers.staff import staff
    from .controllers.join import join
    from .controllers.joinSelf import joinSelf
    from .controllers.joinLinkTable import joinLinkTable
    from .controllers.todo import todo
    from .controllers.jsonId import jsonId
    from .controllers.cascadingLists import cascadingLists
    from .controllers.countries import countries
    from .controllers.checkbox import checkbox
    from .controllers.compoundKey import compoundKey
    from .controllers.time import time

    app.register_blueprint(examples, url_prefix='/')
    app.register_blueprint(staff, url_prefix='/api')
    app.register_blueprint(join, url_prefix='/api')
    app.register_blueprint(joinSelf, url_prefix='/api')
    app.register_blueprint(joinLinkTable, url_prefix='/api')
    app.register_blueprint(todo, url_prefix='/api')
    app.register_blueprint(jsonId, url_prefix='/api')
    app.register_blueprint(cascadingLists, url_prefix='/api')
    app.register_blueprint(countries, url_prefix='/api')
    app.register_blueprint(checkbox, url_prefix='/api')
    app.register_blueprint(compoundKey, url_prefix='/api')
    app.register_blueprint(time, url_prefix='/api')

    return app
