from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, DateField, TimeField, TextAreaField
from wtforms.validators import DataRequired

class signUpForm(FlaskForm):
    username = StringField('Username', validators = [DataRequired()])
    email = StringField('Email', validators = [DataRequired()])
    password = PasswordField('Password', validators = [DataRequired()])
    submit = SubmitField('Sign Up')

class loginForm(FlaskForm):
    username = StringField('Username', validators = [DataRequired()])
    password = PasswordField('Password', validators = [DataRequired()])
    submit = SubmitField('Sign In')

class eventOrganizerForm(FlaskForm):
    event_name = StringField("Event Name", validators=[DataRequired()])
    sport = StringField("Sport", validators=[DataRequired()])
    date = DateField("Date", validators=[DataRequired()])
    time = TimeField("Time", validators=[DataRequired()])
    notes = TextAreaField("Additional Notes")
    submit = SubmitField("Submit")

class eventsEOForm(FlaskForm):
    modify = SubmitField("Modify")
    delete = SubmitField("Delete")
    stream = SubmitField("Stream")