from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import ForeignKey
from flask_sqlalchemy import SQLAlchemy
from flask_login import FlaskLoginClient, LoginManager, login_user, logout_user, login_required, UserMixin
from sqlalchemy import event

# This defines the DB schema
class User(db.Model):
    __tablename__ = 'User'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), unique=False)
    password = db.Column(db.String(30), unique=False)
    email = db.Column(db.String(30), unique=False)
    is_eo = db.Column(db.Boolean, unique=False, default=False)
    is_sm = db.Column(db.Boolean, unique=False, default=False)

# Function to create an admin user

def create_event_organizer(target, connection, **kw):
    existing_event_organizer = connection.execute(
        db.select(User).where(User.username == "eventorganizer")
    ).first()
    
    if not existing_event_organizer:
        event_organizer = User(
            username="eventorganizer",
            email="eventorganizer@gmail.com",
            password="password",  # Plaintext password for example
            is_eo=True,
            is_sm = False
        )
        connection.execute(db.insert(User), [
            {"username": event_organizer.username, "email": event_organizer.email, 
             "password": event_organizer.password, "is_eo": event_organizer.is_eo}
        ])
        print("Event organizer user created successfully.")

# Attach the admin creation function to the 'after_create' event on the User table
event.listen(User.__table__, "after_create", create_event_organizer)


def create_site_manager(target, connection, **kw):
    existing_site_manager = connection.execute(
        db.select(User).where(User.username == "sitemanager")
    ).first()
    
    if not existing_site_manager:
        site_manager = User(
            username="sitemanager",
            email="sitemanager@gmail.com",
            password="password",  # Plaintext password for example
            is_eo =False,
            is_sm= True
        )
        connection.execute(db.insert(User), [
            {"username": site_manager.username, "email": site_manager.email, 
             "password": site_manager.password, "is_sm": site_manager.is_sm}
        ])
        print("Site manager user created successfully.")

# Attach the admin creation function to the 'after_create' event on the User table
event.listen(User.__table__, "after_create", create_site_manager)


class Organization(db.Model):
    __tablename__ = 'Organization'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    street = db.Column(db.String(255), nullable=False)
    city = db.Column(db.String(255), nullable=False)
    state = db.Column(db.String(255), nullable=False)
    about = db.Column(db.String(255))

class Site(db.Model):
    __tablename__ = 'Site'
    id = db.Column(db.Integer, primary_key=True)
    org_id = db.Column(db.Integer, ForeignKey('Organization.id', ondelete='CASCADE'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    about = db.Column(db.String(100))
    s_id = db.Column(db.String(50))

class Event(db.Model):
    __tablename__ = 'Event'
    id = db.Column(db.Integer, primary_key=True)
    s_id = db.Column(db.Integer, ForeignKey('Site.id', ondelete='CASCADE'), nullable=False)
    event_name = db.Column(db.String(100), nullable=False)
    sport = db.Column(db.String(50), nullable=False)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.Time, nullable=False)
    notes = db.Column(db.Text)
    port = db.Column(db.Integer)
    ip = db.Column(db.String(50))
    site = db.Column(db.String(50))
    
class Camera(db.Model):
    __tablename__ = 'Camera'
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, ForeignKey('Event.id', ondelete='CASCADE'), nullable=False)
    mxid = db.Column(db.String(50)) #the actual ID inputted by an admin, had by each camera