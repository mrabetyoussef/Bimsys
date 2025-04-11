import shortuuid
from database.db import db 
from sqlalchemy import Float
from datetime import date



class Phases(db.Model):
    __tablename__ = "phases"
    id = db.Column(db.String(16), primary_key=True, unique=True, nullable=False, default=lambda: shortuuid.uuid()[:10])
    project_id = db.Column(db.String, db.ForeignKey("projects.id"))
    name =  db.Column(db.String(255), nullable=False)
    
    
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
    days_budget = db.Column(Float)
    budget = db.Column(Float)
    tasks = db.relationship("Task", backref="project", lazy=True)
    phases = db.relationship("Phases", backref="project", lazy=True)



    def __init__(self, name, status, start_date, end_date, phase, bim_manager_id,days_budget):
        self.id = shortuuid.uuid()[:10] 
        self.code_akuiteo  = shortuuid.uuid()[:10] 
        self.name = name
        self.status = status
        self.start_date = start_date
        self.end_date = end_date
        self.phase = phase
        self.bim_manager_id = bim_manager_id
        self.days_budget = days_budget
        self.budget = self.update_budget()

    def update_budget(self):
        return self.self.days_budget * 700
        


class Task(db.Model):
    __tablename__ = "tasks"

    id = db.Column(db.String(16), primary_key=True, default=lambda: shortuuid.uuid()[:10])
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default="À faire")
    assigned_to = db.Column(db.Integer, db.ForeignKey("BimUsers.id"), nullable=True)
    project_id = db.Column(db.String(16), db.ForeignKey("projects.id"), nullable=False)
    due_date = db.Column(db.Date, nullable=True)

    def __init__(self, name, description, status="À faire", assigned_to=None, project_id=None, due_date=None):
        self.id = shortuuid.uuid()[:10]
        self.name = name
        self.description = description
        self.status = status
        self.assigned_to = assigned_to
        self.project_id = project_id
        self.due_date = due_date



class BimUsers(db.Model):
    __tablename__ = "BimUsers"

    id = db.Column(db.String(16), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    role = db.Column(
        db.String(50), nullable=False
    )  
    projects = db.relationship("Project", backref="bim_manager", lazy=True)

    def __init__(self, name, email , role):
        self.id = shortuuid.uuid()[:10] 
        self.name = name
        self.email = email
        self.role = role


