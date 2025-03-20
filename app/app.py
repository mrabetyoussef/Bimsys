from flask import Flask, redirect, url_for
from flask_migrate import Migrate
from database.db import db
from database.model import Project, Task, BimUsers
from app.dash_app import DashApp 

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///bimsys.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["DEBUG"] = True  

db.init_app(app)
migrate = Migrate(app, db)

@app.route("/")
def home():
    return redirect(url_for("/BIMSYS/"))  

DashApp(app)  

if __name__ == "__main__":
    app.run(debug=True)
