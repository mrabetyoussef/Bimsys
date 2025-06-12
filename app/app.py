from flask import Flask, redirect, url_for
from flask_migrate import Migrate
from database.db import db
from database.model import Project, Task, BimUsers
from app.dash_app import DashApp 
from flask_login import LoginManager , logout_user
from flask_mail import Mail

name = __name__
app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///bimsys.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["DEBUG"] = True  
app.secret_key  = "12345"
db.init_app(app)
migrate = Migrate(app, db)

app.config.update(
    MAIL_SERVER='in-v3.mailjet.com',
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USERNAME='1855d6eacbcc8dc12442521492fb8d76',
    MAIL_PASSWORD='7afee7a226886cb7362f7102e7e151f5',
    MAIL_DEFAULT_SENDER='mrabetyoussef95@gmail.com'
)

mail = Mail(app)
app.extensions["mail"] = mail 

login_manager = LoginManager()
login_manager.login_view = "/BIMSYS/login"
login_manager.init_app(app)



@login_manager.user_loader
def load_user(user_id):
    return BimUsers.query.get((user_id))


@app.route("/")
def home():
    return redirect(url_for("/BIMSYS/"))  

@app.route("/BIMSYS/logout")
def logout():
    logout_user()
    return redirect("/BIMSYS/login")

dash_app = DashApp(app)  
dash_app.mail = mail

if __name__ == "__main__":
    app.run(debug=True)
