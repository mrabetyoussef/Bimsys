from flask import Flask, redirect, url_for
from flask_migrate import Migrate
from database.db import db
from database.model import Project, Task, BimUsers
from app.dash_app import DashApp 
from flask_login import LoginManager , logout_user

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///bimsys.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["DEBUG"] = True  
app.secret_key  = "12345"
db.init_app(app)
migrate = Migrate(app, db)


login_manager = LoginManager()
login_manager.login_view = "/login"  # Redirection si non authentifié
login_manager.init_app(app)



@login_manager.user_loader
def load_user(user_id):
    return BimUsers.query.get(int(user_id))


@app.route("/")
def home():
    return redirect(url_for("/BIMSYS/"))  

@app.route("/logout")
def logout():
    print("loggginggg outtt")
    logout_user()
    # on renvoie vers la page de login du dash
    return redirect("/BIMSYS/lo gin")

DashApp(app)  

if __name__ == "__main__":
    app.run(debug=True)
