from flask import Blueprint, render_template, request, flash, jsonify, send_from_directory
import json

examples = Blueprint('examples', __name__)


@examples.route('/examples/<path:path>', methods=['GET', 'POST'])
def editorexamples(path):
    return send_from_directory('static/examples', path)

# TK COLIN shouldn't need these two as nginx will sort out in VM


@examples.route('/DataTables/<path:path>')
def datatables(path):
    return send_from_directory('/mnt/DataTablesSrc/built/DataTables', path)

@examples.route('/Extensions/<path:path>')
def editor(path):
    return send_from_directory('/mnt/DataTablesSrc/built/DataTables/extensions', path)


@examples.route('/css/<path:path>')
def css(path):
    return send_from_directory('/mnt/DataTablesSrc/extensions/Editor-Node-Demo/public/css', path)


@examples.route('/js/<path:path>')
def js(path):
    return send_from_directory('/mnt/DataTablesSrc/extensions/Editor-Node-Demo/public/js', path)
