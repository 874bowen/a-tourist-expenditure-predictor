from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileRequired
from wtforms import StringField, PasswordField, SubmitField, BooleanField, FileField, validators, DateTimeField, \
    IntegerField, FloatField
from wtforms.validators import DataRequired, Email, EqualTo
from flask_uploads import UploadSet, IMAGES, configure_uploads
from wtforms.widgets import TextArea


class RegistrationForm(FlaskForm):
    username = StringField('username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password1 = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password1')])
    req_to_be_anchor= BooleanField('Request to be news writer')
    submit = SubmitField('Register')


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit_login = SubmitField('Login')


photos = UploadSet('photos', IMAGES)


class MemoryForm(FlaskForm):
    title = StringField('Title')
    text = StringField('Text', widget=TextArea(), render_kw={'rows': 10})
    picture = FileField('Image', validators=[
        FileAllowed(photos, 'Only images are required'),
        FileRequired('File field should not be empty')
    ])
    submit = SubmitField('Post Memory')


class CountyForm(FlaskForm):
    county_name = StringField('County Name')
    change_rate = FloatField('Change Rate')
    submit_county = SubmitField('Add county')


class PlaceForm(FlaskForm):
    place_name = StringField('Place Name')
    place_description = StringField('Place Description', widget=TextArea(), render_kw={'rows': 10})
    place_picture = StringField('Image Link')
    place_map = StringField('Map Link')
    county_id = IntegerField('County ID')
    featured = BooleanField('Featured')
    submit_place = SubmitField('Add Place')