import os

import flask
import pickle
import pandas as pd
from flask import redirect, url_for, render_template, flash, request, send_from_directory, jsonify
from flask_cors import CORS
from flask_migrate import Migrate
from sqlalchemy import desc
from flask_uploads import configure_uploads
from flask_login import LoginManager, login_user, current_user, logout_user, login_required

from forms import RegistrationForm, LoginForm, MemoryForm, photos, CountyForm, PlaceForm

# Use pickle to load in the pre-trained model.
with open(f'model/weather_model_two.pkl', 'rb') as f:
    model = pickle.load(f)
app = flask.Flask(__name__, template_folder='templates')


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

    all_counties = CountiesModel.query.all()

    if flask.request.method == 'GET':
        print("We are here")
        featured_places = PlacesModel.query.filter_by(featured=True)
        print("wait")
        print(featured_places)

        print("Counties === >>> ", all_counties)
        return flask.render_template('main.html', featured_places=featured_places, all_counties=all_counties)

    if flask.request.method == 'POST':
        temperature = flask.request.form['temperature']
        rainfall = flask.request.form['humidity']
        month = flask.request.form['month-today']
        place = flask.request.form['select_place']
        print(place.title())
        data = CountiesModel.query.filter_by(county_name=place).first()
        rate = data.change_rate
        months = [0] * 11
        suggested_places = PlacesModel.query.filter_by(county_id=data.id)
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
                                     all_counties=all_counties,
                                     result=prediction * rate,
                                     suggested_places=suggested_places
                                     )


@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():

    if not (current_user.email == os.environ['admin']):
        print(False)
        return redirect(url_for('main'))

    form_county = CountyForm()
    form_place = PlaceForm()

    if form_county.submit_county.data and form_county.validate_on_submit():
        county = CountiesModel(county_name=form_county.county_name.data, change_rate=form_county.change_rate.data)
        db.session.add(county)
        db.session.commit()
        return redirect(url_for('admin'))

    elif form_place.submit_place.data and form_place.validate_on_submit():
        print("We are here posting a place", form_place.place_name.data)
        place = PlacesModel(place_name=form_place.place_name.data, place_description=form_place.place_description.data, place_picture=form_place.place_picture.data, place_map=form_place.place_map.data, county_id=form_place.county_id.data)
        db.session.add(place)
        print("We are here posting a place")
        db.session.commit()
        return redirect(url_for('admin'))

    return render_template('admin.html', form_county=form_county, form_place=form_place)


@app.route('/register', methods=['POST', 'GET'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password1.data)
        db.session.add(user) # add to db
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
        memory = Memories(title=form.title.data, text=form.text.data, picture=file_url, owner=current_user.id)
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


@app.route('/counties', methods=['GET'])
def get_counties():
    counties = CountiesModel.query.all()
    print(counties)
    return jsonify([county.toDict() for county in counties])

if __name__ == '__main__':
    app.run()
