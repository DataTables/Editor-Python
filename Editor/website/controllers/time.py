from flask import Blueprint, request, jsonify
import datetime
from .db import db


from ..editor import Editor, Field, Options, Validate, ValidationOptions, Formatter

time = Blueprint('time', __name__)


@time.route('/time', methods=['GET', 'POST'])
def endpoint():
    def validate_time(val, data, host):
        # This is need as there isn't a single digit format for hours in Python!!
        msg = 'Bad time format - e.g. "9:30 PM"'
        try:
            dt = datetime.datetime.strptime(val, '%I:%M %p')

            # Manually format the time to remove leading zero from hour
            hour = dt.strftime('%I').lstrip('0')  # Remove leading zero from hour
            minute = dt.strftime('%M')
            am_pm = dt.strftime('%p')

            formatted_time = f"{hour}:{minute} {am_pm}"

            if formatted_time != val:
                return msg
        except:
            return msg  
        
        return True

    editor = (
        Editor(db, 'users')
        .debug(True)
        .fields([
            Field('first_name'),
            Field('last_name'),
            Field('city'),
            Field('shift_start')
            .validator(validate_time)
            .get_formatter(Formatter.date_time("%H:%M:%S", "%I:%M %p"))
            .set_formatter(Formatter.date_time("%I:%M %p", "%H:%M:%S")),
            Field('shift_end')
            .validator(Validate.date_format("%H:%M:%S"))
        ])
    )

    data = editor.process(request.form.to_dict())
    return jsonify(data)
