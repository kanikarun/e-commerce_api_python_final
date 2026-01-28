import os

from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime, timedelta

from flask_jwt_extended import (
    JWTManager, create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity, get_jwt
)


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'


db = SQLAlchemy(app)
migrate = Migrate(app, db)

app.config["JWT_SECRET_KEY"] = "change-me"
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(minutes=30)
app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=7)

jwt = JWTManager(app)



import model

import route

# @app.get('/')
# @app.get('/home')
# def home():
#     return render_template('home.html')



if __name__ == '__main__':
    app.run()
