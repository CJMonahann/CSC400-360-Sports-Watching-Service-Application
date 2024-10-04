from flask import Flask

# New imports
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
from os import environ
import os

# force loading of environment variables
load_dotenv('.flaskenv')

app = Flask(__name__)

# Add models
from app import routes