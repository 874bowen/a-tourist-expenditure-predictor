from flask_login import UserMixin
from sqlalchemy.orm import backref
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from app import db


class CountiesModel(db.Model):
    __tablename__ = 'counties_table'

    id = db.Column(db.Integer, primary_key=True)
    county_name = db.Column(db.String())
    change_rate = db.Column(db.Float())

    def __init__(self, county_name, change_rate):
        self.county_name = county_name
        self.change_rate = change_rate

    def __repr__(self):
        return f"{self.county_name}:{self.change_rate}"


class PlacesModel(db.Model):
    __tablename__ = 'places_table'

    id = db.Column(db.Integer, primary_key=True)
    place_name = db.Column(db.String())
    place_description = db.Column(db.String())
    place_picture = db.Column(db.String())
    place_map = db.Column(db.String())
    county_id = db.Column(db.Integer, db.ForeignKey('counties_table.id'))
    county = db.relationship("CountiesModel", backref=backref("request", uselist=False))


class User(UserMixin, db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), index=True, unique=True)
    email = db.Column(db.String(150), unique=True, index=True)
    password_hash = db.Column(db.String(150))
    joined_at = db.Column(db.DateTime(), default=datetime.utcnow, index=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Memories(db.Model):
    __tablename__ = "memories"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String())
    text = db.Column(db.String())
    picture = db.Column(db.String())
    owner = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime(), default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime(), default=datetime.utcnow, index=True)

    # Shows up in the admin list
    def __str__(self):
        return self.title

