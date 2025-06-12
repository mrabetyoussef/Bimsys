from app.app import app
from database.db import db 
from database.model import BimUsers
from flask_migrate import upgrade
from database import manage

with app.app_context():
    # upgrade()  
    print('creating all')    
    db.create_all() 
    admin = BimUsers.create_default_admin()
    print(admin)
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000 )
