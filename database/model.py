from database.db import db


class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code_akuiteo = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    phase = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(50), nullable=False)  # En cours, Terminé, etc.
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=True)
    bim_manager_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    tasks = db.relationship("Task", backref="project", lazy=True)


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default="À faire")  # À faire, En cours, Terminé
    assigned_to = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    project_id = db.Column(db.Integer, db.ForeignKey("project.id"), nullable=False)
    due_date = db.Column(db.Date, nullable=True)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    role = db.Column(
        db.String(50), nullable=False
    )  # Manager, BIM Manager, Collaborateur
    projects = db.relationship("Project", backref="bim_manager", lazy=True)
