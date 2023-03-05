import os
import flask
import pickle
import pandas as pd
from flask import redirect, url_for, render_template, flash, request, send_from_directory
from flask_cors import CORS
from flask_migrate import Migrate
from sqlalchemy import desc
from flask_uploads import UploadSet, IMAGES, configure_uploads
from werkzeug.utils import secure_filename
from flask_login import UserMixin, LoginManager, login_user, current_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash

from forms import RegistrationForm, LoginForm, MemoryForm, photos

SECRET_KEY = os.urandom(32)

print(SECRET_KEY)

plain_password = "qwerty"
hashed_password = generate_password_hash(plain_password)
print(hashed_password)
submitted_password = "qwerty"
matching_password = check_password_hash(hashed_password, submitted_password)
print(matching_password)

# Use pickle to load in the pre-trained model.
with open(f'model/weather_model_two.pkl', 'rb') as f:
    model = pickle.load(f)
app = flask.Flask(__name__, template_folder='templates')

# app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://postgres:Bowen123@localhost:5432/tourism_ke"
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# WEBSITE_HOSTNAME exists only in production environment
if 'WEBSITE_HOSTNAME' not in os.environ:
    # local development, where we'll use environment variables
    print("Loading config.development and environment variables from .env file.")
    app.config.from_object('azureproject.development')
else:
    # production
    print("Loading config.production.")
    app.config.from_object('azureproject.production')

app.config.update(
    SQLALCHEMY_DATABASE_URI=app.config.get('DATABASE_URI'),
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
)

app.config['SECRET_KEY'] = 'ade24rset6TEFY4434fdy4ss'
app.config['UPLOADED_PHOTOS_DEST'] = 'uploads'

# photos = UploadSet('photos', IMAGES)
configure_uploads(app, photos)
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy(app)
migrate = Migrate(app, db)
CORS(app)

from models import User, CountiesModel, PlacesModel, Memories, db

# configure Login Manager class in app
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


@app.route('/', methods=['GET', 'POST'])
def main():
    if flask.request.method == 'GET':
        print("We are here")
        return (flask.render_template('main.html'))
    if flask.request.method == 'POST':
        temperature = flask.request.form['temperature']
        rainfall = flask.request.form['humidity']
        month = flask.request.form['month-today']
        place = flask.request.form['select_place']
        print(place.title())
        data = CountiesModel.query.filter_by(county_name=place).first()
        rate = data.change_rate
        months = [0] * 11
        places = PlacesModel.query.filter_by(county_id=data.id).first()
        print(places.place_description)

        if month == 1:
            months[3] = 1
        elif month == 2:
            months[6] = 1
        elif month == 3:
            months[0] = 1
        elif month == 4:
            months[7] = 1
        elif month == 5:
            months[5] = 1
        elif month == 6:
            months[4] = 1
        elif month == 7:
            months[1] = 1
        elif month == 8:
            months[10] = 1
        elif month == 9:
            months[9] = 1
        elif month == 10:
            months[8] = 1
        elif month == 11:
            months[2] = 1
        else:
            months = months

        input_variables = pd.DataFrame([[rainfall, temperature, *months]],
                                       columns=[
                                           'Rainfall - (MM)',
                                           'Temperature - (Celsius)',
                                           'Apr Average',
                                           'Aug Average',
                                           'Dec Average',
                                           'Feb Average',
                                           'Jul Average',
                                           'Jun Average',
                                           'Mar Average',
                                           'May Average',
                                           'Nov Average',
                                           'Oct Average',
                                           'Sep Average',
                                       ],
                                       dtype=float)
        prediction = model.predict(input_variables)[0]
        return flask.render_template('main.html',
                                     original_input={'Temperature': temperature,
                                                     'Rainfall': rainfall},
                                     result=prediction * rate,
                                     places=places
                                     )


@app.route('/register', methods=['POST', 'GET'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password1.data)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('registration.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None and user.check_password(form.password.data):
            login_user(user)
            next = request.args.get("next")
            return redirect(next or url_for('memory'))
        flash('Invalid email address or Password.')
    return render_template('login.html', form=form)


@app.route("/uploads/<filename>")
def get_file(filename):
    return send_from_directory(app.config['UPLOADED_PHOTOS_DEST'], filename)


@app.route("/memories", methods=['GET', 'POST'])
@login_required
def memory():
    form = MemoryForm()
    memories = Memories.query.filter_by(owner=current_user.id).order_by(desc(Memories.created_at))
    print(memories)
    if form.validate_on_submit():
        filename = photos.save(form.picture.data)
        file_url = url_for('get_file', filename=filename)
        print(current_user.id)
        print(file_url)
        memory = Memories(title=form.title.data, text=form.text.data, picture=file_url, owner=form.owner.data)
        db.session.add(memory)
        db.session.commit()
    else:
        file_url = None
    return render_template('memories.html', form=form, memories=memories)


@app.route("/logout")
# @login_required
def logout():
    logout_user()
    return redirect(url_for('main'))


@app.route("/forbidden", methods=['GET', 'POST'])
@login_required
def protected():
    return redirect(url_for('forbidden.html'))


if __name__ == '__main__':
    app.run()
