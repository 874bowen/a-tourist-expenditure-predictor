from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileRequired
from wtforms import StringField, PasswordField, SubmitField, BooleanField, FileField, validators, DateTimeField, \
    IntegerField
from wtforms.validators import DataRequired, Email, EqualTo
from flask_uploads import UploadSet, IMAGES, configure_uploads
from wtforms.widgets import TextArea


class RegistrationForm(FlaskForm):
    username = StringField('username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password1 = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password1')])
    submit = SubmitField('Register')


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me', validators=[DataRequired()])
    submit = SubmitField('Login')


photos = UploadSet('photos', IMAGES)


class MemoryForm(FlaskForm):
    title = StringField('Title')
    text = StringField('Text', widget=TextArea(), render_kw={'rows': 10})
    picture = FileField('Image', validators=[
        FileAllowed(photos, 'Only images are required'),
        FileRequired('File field should not be empty')
    ])
    owner = IntegerField('Owner')
    submit = SubmitField('Post Memory')
