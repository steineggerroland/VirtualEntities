from flask_babel import gettext
from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired, Length, Regexp


class RoomForm(FlaskForm):
    name = StringField(label=gettext('Name'),
                       description=gettext('Name may contain digits, letters and symbols of _-,.()'),
                       validators=[DataRequired(), Length(min=1, max=42),
                                   Regexp('^[-A-Za-z0-9_.,() ]+$', message=gettext('May just contain digits, letters and symbols of _-,.()'))])
