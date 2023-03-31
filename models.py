from flask_login import UserMixin
from sqlalchemy.orm import backref
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from app import db


class CountiesModel(db.Model):
    __tablename__ = 'counties_table'

    id = db.Column(db.Integer, primary_key=True)
    county_name = db.Column(db.String(), unique=True)
    is_safe = db.Column(db.Boolean, default=True)
    change_rate = db.Column(db.Float())

    def toDict(self):
        return dict(id=self.id, county_name=self.county_name, change_rate=self.change_rate)

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
    rating = db.Column(db.Integer(), default=5)
    county_id = db.Column(db.Integer, db.ForeignKey('counties_table.id'))
    featured = db.Column(db.Boolean, default=False)
    county = db.relationship("CountiesModel", backref=backref("request", uselist=False))


class User(UserMixin, db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), index=True, unique=True)
    email = db.Column(db.String(150), unique=True, index=True)
    password_hash = db.Column(db.String(150))
    joined_at = db.Column(db.DateTime(), default=datetime.utcnow, index=True)
    is_admin = db.Column(db.Boolean(), default=True)
    is_anchor = db.Column(db.Boolean(), default=True)
    writer_request = db.Column(db.Boolean(), default=False)

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


class ToVisit(db.Model):
    __tablename__ = "tovisit"

    def toDict(self):
        return dict(id=self.id, place_id=self.place_id, visited=self.visited)

    id = db.Column(db.Integer, primary_key=True)
    place_id = db.Column(db.Integer, db.ForeignKey('places_table.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    visited = db.Column(db.Boolean, default=False)
    rate = db.Column(db.Integer, default=5)
    place = db.relationship("PlacesModel", backref=backref("request", uselist=False))
    user = db.relationship("User", backref=backref("request", uselist=False))

    __table_args__ = (
        db.UniqueConstraint('place_id', 'user_id', name='_unique_place_id_user_id'),
    )


class News(db.Model):
    __tablename__ = "news"

    id = db.Column(db.Integer, primary_key=True)
    topic = db.Column(db.String())
    news = db.Column(db.String())
    type = db.Column(db.String())
    recommendation = db.Column((db.Integer()))
    created_at = db.Column(db.DateTime(), default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime(), default=datetime.utcnow, index=True)
    county_id = db.Column(db.Integer, db.ForeignKey('counties_table.id'))
    news_anc_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    county = db.relationship("CountiesModel", backref=backref("county", uselist=False))
