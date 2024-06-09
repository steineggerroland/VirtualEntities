from flask_babel import gettext
from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired, Length, Regexp


class ApplianceForm(FlaskForm):
    name = StringField(label=gettext('Name'),
                       validators=[DataRequired(), Length(min=1, max=40), Regexp('^[-A-Za-z0-9_.,()]+$')])
