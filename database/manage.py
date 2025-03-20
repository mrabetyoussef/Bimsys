from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from database.db import db
from database.model import Project, Task,  BimUsers

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///bimsys.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

migrate = Migrate(app, db)
