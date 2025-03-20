import shortuuid
from database.db import db
from datetime import date

class Project(db.Model):
    __tablename__ = "projects"

    id = db.Column(db.String(16), primary_key=True, unique=True, nullable=False, default=lambda: shortuuid.uuid()[:10])
    code_akuiteo = db.Column(db.String(16), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(50), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=True)
    phase = db.Column(db.String(50), nullable=False)
    bim_manager_id = db.Column(db.Integer, db.ForeignKey("BimUsers.id"))

    def __init__(self, name, status, start_date, end_date, phase, bim_manager_id,):
        self.id = shortuuid.uuid()[:10] 
        self.code_akuiteo  = shortuuid.uuid()[:10] 
        self.name = name
        self.status = status
        self.start_date = start_date
        self.end_date = end_date
        self.phase = phase
        self.bim_manager_id = bim_manager_id


class Task(db.Model):
    __tablename__ = "Task"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default="À faire")  # À faire, En cours, Terminé
    assigned_to = db.Column(db.Integer, db.ForeignKey("BimUsers.id"), nullable=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=False)
    due_date = db.Column(db.Date, nullable=True)


class BimUsers(db.Model):
    __tablename__ = "BimUsers"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    role = db.Column(
        db.String(50), nullable=False
    )  # Manager, BIM Manager, Collaborateur
    projects = db.relationship("Project", backref="bim_manager", lazy=True)
