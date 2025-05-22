from app.app import app
from database.db import db
from flask_migrate import upgrade
from database import manage

with app.app_context():
    # upgrade()  
    db.create_all() 

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000 )
