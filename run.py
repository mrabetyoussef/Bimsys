from app.app import app
from database.db import db
from flask_migrate import upgrade
from database import manage
# Apply migrations before starting the app
with app.app_context():
    upgrade()  # This applies pending migrations
    db.create_all()  # Ensures tables exist

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
