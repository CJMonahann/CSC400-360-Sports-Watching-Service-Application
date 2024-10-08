from app import db
from sqlalchemy import ForeignKey

# This defines the DB schema
class Accounts(db.Model):
    __tablename__ = 'Accounts'
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(30), unique=False)
    last_name = db.Column(db.String(30), unique=False)
    user_name = db.Column(db.String(30), unique=False)
    password = db.Column(db.String(30), unique=False)
    email = db.Column(db.String(30), unique=False)
    mod_level = db.Column(db.Integer, unique=False) #1-3, with 3 being the highest