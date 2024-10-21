from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import ForeignKey
from flask_sqlalchemy import SQLAlchemy
from flask_login import FlaskLoginClient, LoginManager, login_user, logout_user, login_required, UserMixin

# This defines the DB schema
class User(db.Model):
    __tablename__ = 'User'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), unique=False)
    password = db.Column(db.String(30), unique=False)
    email = db.Column(db.String(30), unique=False)
