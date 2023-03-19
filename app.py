import math
import os

import flask
import pickle
import pandas as pd
from flask import redirect, url_for, render_template, flash, request, send_from_directory, jsonify
from flask_cors import CORS
from flask_migrate import Migrate
from sqlalchemy import desc, func
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

from models import User, CountiesModel, PlacesModel, Memories, db, ToVisit, News

# configure Login Manager class in app
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


@app.route('/', methods=['GET', 'POST'])
def main():
    all_counties = CountiesModel.query.all()
    form_login = LoginForm()

    if flask.request.method == 'GET':
        print("We are here")
        featured_places = PlacesModel.query.filter_by(featured=True)
        print("wait")
        print(featured_places)

        print("Counties === >>> ", all_counties)
        return flask.render_template('main.html', featured_places=featured_places, all_counties=all_counties,
                                     form=form_login)

    if flask.request.method == 'POST':

        if form_login.validate_on_submit():
            user = User.query.filter_by(email=form_login.email.data).first()
            if user is not None and user.check_password(form_login.password.data):
                login_user(user)
                next = request.args.get("next")
                return redirect(next or url_for('main'))
            flash('Invalid email address or Password.')
            return render_template('main.html')

        temperature = flask.request.form['temperature']
        rainfall = flask.request.form['humidity']
        month = flask.request.form['month-today']
        place = flask.request.form['select_place']
        print(place.title())
        data = CountiesModel.query.filter_by(county_name=place).first()
        rate = data.change_rate
        months = [0] * 11
        suggested_places = PlacesModel.query.filter_by(county_id=data.id)
        visits = ToVisit.query.filter_by(user_id=current_user.id)

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
                                                     'Humidity': rainfall},
                                     all_counties=all_counties,
                                     result=round((prediction * rate), 2),
                                     suggested_places=suggested_places,
                                     county=data,
                                     form=form_login
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
        place = PlacesModel(place_name=form_place.place_name.data, place_description=form_place.place_description.data,
                            place_picture=form_place.place_picture.data, place_map=form_place.place_map.data,
                            county_id=form_place.county_id.data)
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
        db.session.add(user)  # add to db
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


@app.route('/to-visit/add', methods=['POST'])
def add_to_visit():
    place_id = request.form.get('place_id')
    print("Adding Visit")
    print(place_id)
    # Add product to user's cart in database
    tovisit = ToVisit(place_id=place_id, user_id=current_user.id)
    db.session.add(tovisit)  # add to db
    db.session.commit()
    visits = ToVisit.query.filter_by(user_id=current_user.id)
    # Return JSON response with updated cart information
    return jsonify([visit.toDict() for visit in visits])


@app.route('/to-visit', methods=['GET', 'POST'])
def visits():
    visits = ToVisit.query.filter_by(user_id=current_user.id)

    return render_template('visits.html', visits=visits)


@app.route("/rate/<int:visit_id>/<int:rating>")
def rate_task(visit_id, rating):
    # Update task rating in database
    visit = ToVisit.query.filter_by(id=visit_id, user_id=current_user.id).first()

    count = ToVisit.query.filter_by(place_id=visit.place_id).count()
    total = db.session.query(func.sum(ToVisit.rate)).filter_by(place_id=visit.place_id).scalar()
    print(count, total, total / count)
    place = PlacesModel.query.filter_by(id=visit.place_id).first()
    place.rating = math.ceil(total / count)
    visit.rate = rating
    db.session.commit()
    return jsonify({"success": True})


@app.route("/toggle-visit", methods=['POST'])
def toggleVisit():
    visit_id = request.form.get('visit_id')
    print("Visit id for toggle", visit_id)
    visit = ToVisit.query.filter_by(id=visit_id, user_id=current_user.id).first()
    print(visit.id)
    visit.visited = not visit.visited
    db.session.commit()
    return jsonify({"success": True})


@app.route('/delete-visit', methods=['POST'])
def deleteVisit():
    visit_id = request.form.get('visit_id')
    print("Deleting ", visit_id)
    tovisit = ToVisit.query.filter_by(id=visit_id, user_id=current_user.id).first()
    db.session.delete(tovisit)
    db.session.commit()
    return jsonify({"success": True})


# news
@app.route('/news', methods=['GET'])
def view_news():
    news = News.query.all()
    return render_template('news.html', news=news)


@app.route('/news/create', methods=['GET', 'POST'])
def create_news():
    counties = CountiesModel.query.all()
    if request.method == 'POST':
        county_name = flask.request.form['select_place']
        topic = flask.request.form['topic']
        news = flask.request.form['news']
        type_n = flask.request.form['select_type']
        recomm = flask.request.form['recomm']
        county = CountiesModel.query.filter_by(county_name=county_name).first()
        # safety
        count = News.query.filter_by(county_id=county.id).count()
        total = db.session.query(func.sum(News.recommendation)).filter_by(county_id=county.id).scalar()

        if count > 0:
            avg_recomm = math.ceil(total / count)
            print(avg_recomm, "is this")
            if avg_recomm >= 3:
                county.is_safe = True
            else:
                county.is_safe = False

        else:
            if recomm >= 3:
                county.is_safe = True
            else:
                county.is_safe = False

        news = News(topic=topic, news=news, type=type_n, recommendation=recomm, county_id=county.id, news_anc_id=current_user.id)
        db.session.add(news)
        db.session.commit()
        return 'News created successfully'
    return render_template('create_news.html', all_counties=counties)


@app.route('/delete-news', methods=['POST'])
def deleteNews():
    news_id = request.form.get('news_id')
    print("Deleting ", news_id)
    todel = News.query.filter_by(id=news_id, news_anc_id=current_user.id).first()
    db.session.delete(todel)
    db.session.commit()
    return jsonify({"success": True})

if __name__ == '__main__':
    app.run()
