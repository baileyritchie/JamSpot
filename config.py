import os
from dotenv import load_dotenv
load_dotenv()

SECRET_KEY = os.urandom(32)
# Grabs the folder where the script runs.
basedir = os.path.abspath(os.path.dirname(__file__))

# Disable debug mode.
DEBUG = False

# Connect to the database
SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
SQLALCHMEY_TRACK_MODIFICATIONS = False


