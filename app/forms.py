"""
Ben Feeser
Sentinel

Library of forms.
"""
from flask_wtf import FlaskForm
from wtforms import (
    widgets,
    HiddenField,
    BooleanField,
    TextField,
    PasswordField,
    SubmitField,
    SelectField,
    SelectMultipleField,
    DateTimeField,
)
from wtforms.validators import Email, Length, Required, EqualTo, Optional

# global day map
day_map = {
    "0": "Mon",
    "1": "Tue",
    "2": "Wed",
    "3": "Thu",
    "4": "Fri",
    "5": "Sat",
    "6": "Sun",
}


# wtform classes
# http://wtforms.simplecodes.com/docs/0.6/validators.html
class Login(FlaskForm):
    # form to login users; subclass of base form class
    email = TextField("Email", [Required(), Email(), Length(min=4, max=50)])
    pwd = PasswordField("Password", [Required(), Length(min=6, max=25)])
    remember_me = BooleanField(default=True)
    submit = SubmitField("Login")


class Register(Login):
    # form to register users; subclass of login plus confirm
    confirm = PasswordField(
        "Confirm Password",
        [
            Required(),
            Length(min=6, max=25),
            EqualTo("pwd", message="Passwords must match"),
        ],
    )
    submit = SubmitField("Register")


class MultiCheckbox(SelectMultipleField):
    # subclass select multiple field to get a list of checkboxes
    # https://gist.github.com/doobeh/4668212
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()


class Pattern(FlaskForm):
    # required fields
    path = SelectField("Path")
    pattern = TextField("Pattern", [Required(), Length(min=1, max=255)])
    name = TextField("Name", [Required(), Length(min=1, max=255)])

    # scheduling fields: recipients, time, and days
    recipients = TextField("Recipients", [Optional(), Length(max=255)])
    time = DateTimeField("Time", [Optional()], format="%H:%M")

    # create sorted list of days to choose
    choices = [(k, v) for k, v in sorted(day_map.items())]
    days = MultiCheckbox("Days", [Optional()], choices=choices)

    # hidden field for pattern_id
    pattern_id = HiddenField("pattern_id", [Optional()])

    # create two submit fields
    save = SubmitField("Save")
    delete = SubmitField("Delete")
