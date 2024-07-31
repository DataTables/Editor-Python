from flask import Blueprint, request, jsonify
from sqlalchemy import text

from .db import db

countries = Blueprint('countries', __name__)


@countries.route('/countries', methods=['GET', 'POST'])
def endpoint():

    data = request.form

    with db.connect() as connection:
        sql = text(
            "SELECT id as value, name as label from country where continent = :continent")
        
        res = connection.execute(
            sql, {"continent": data['values[team.continent]']}).fetchall()

        countries = []
        for this_row in res:
            row = this_row._mapping
            countries.append({"value": row["value"], "label": row["label"]})

        out = {"options": {"team.country": countries}}

        connection.close()

        return jsonify(out)
