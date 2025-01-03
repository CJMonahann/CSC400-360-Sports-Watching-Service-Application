from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, DateField, TimeField, TextAreaField, RadioField
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
    s_time = TimeField("Start Time", validators=[DataRequired()]) #start time
    e_time = TimeField("End Time", validators=[DataRequired()]) #end time
    e_id = StringField("Event ID", validators=[DataRequired()]) #event ID
    notes = TextAreaField("Additional Notes")
    submit = SubmitField("Submit")

class modifyForm(FlaskForm):
    event_name = StringField("Event Name")
    sport = StringField("Sport")
    date = DateField("Date")
    s_time = TimeField("Start Time") #start time
    e_time = TimeField("End Time") #end time
    e_id = StringField("Event ID") #event ID
    notes = TextAreaField("Additional Notes")
    submit = SubmitField("Submit")

class eventsEOForm(FlaskForm):
    modify = SubmitField("Modify")
    delete = SubmitField("Delete")
    stream = SubmitField("Stream")

class eventsSMForm(FlaskForm):
    update_event = SubmitField("Site Information")
    stream = SubmitField("Stream")

class SiteManagerSettingsForm(FlaskForm):
    site_location = StringField('Site Location', validators=[DataRequired()], render_kw={"placeholder": "Enter site location"})
    ip = StringField('IP Address', validators=[DataRequired()], render_kw={"placeholder": "Enter IP address"})
    port = StringField('Port', validators=[DataRequired()], render_kw={"placeholder": "Enter port number"})
    cameras = RadioField('Number of Cameras', choices=[('1', '1 Camera'), ('2', '2 Cameras'), ('3', '3 Cameras')], validators=[DataRequired()])
    notes = TextAreaField('Additional Notes for Event', render_kw={"placeholder": "Enter any additional notes here"})
    submit = SubmitField('Submit')

class CameraForm(FlaskForm):
    mxid = StringField(validators=[DataRequired()])
    submit = SubmitField('Submit')

class SiteForm(FlaskForm):
    name = StringField(validators=[DataRequired()])
    about = StringField(validators=[DataRequired()])
    s_id = StringField(validators=[DataRequired()])
    submit = SubmitField('Submit')

class UpdateSiteForm(FlaskForm):
    s_id = StringField(validators=[DataRequired()])
    submit = SubmitField('Submit')

class UpdateEventForm(FlaskForm):
    e_id = StringField(validators=[DataRequired()])
    submit = SubmitField('Submit')

class OrgForm(FlaskForm):
    name = StringField(validators=[DataRequired()])
    street = StringField(validators=[DataRequired()])
    city = StringField(validators=[DataRequired()])
    state = StringField(validators=[DataRequired()])
    about = StringField(validators=[DataRequired()])
    submit = SubmitField('Submit')