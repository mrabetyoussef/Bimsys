import shortuuid
from database.db import db 
from sqlalchemy import Float , Boolean
from datetime import date
from flask_login import UserMixin



class Phase(db.Model):
    __tablename__ = "phases"
    id = db.Column(db.String(16), primary_key=True, unique=True, nullable=False, default=lambda: shortuuid.uuid()[:10])
    name =  db.Column(db.String(255), nullable=False)

class ProjectPhase(db.Model):
    __tablename__ = "project_phases"

    id = db.Column(db.String(16), primary_key=True, nullable=False, default=lambda: shortuuid.uuid()[:10])
    project_id = db.Column(db.String(16), db.ForeignKey("projects.id", name="fk_projectphase_project"), nullable=False)
    phase_id = db.Column(db.String(16), db.ForeignKey("phases.id", name="fk_projectphase_phase"), nullable=False)
    project_parent = db.relationship("Project", back_populates="phases")
    phase = db.relationship('Phase', backref='project_phases', lazy=True)
    tasks = db.relationship("Task", back_populates="project_phase", lazy=True)
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    days_budget = db.Column(Float)
    euros_budget = db.Column(Float)
    assigned_bimuser_id = db.Column(db.String(16), db.ForeignKey("BimUsers.id", name="fk_projectphase_user"))
    assigned_bimuser = db.relationship("BimUsers")


    def __init__(self, project_id, phase_id):
        self.id = shortuuid.uuid()[:10]
        self.project_id = project_id
        self.phase_id = phase_id

    
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
    phases = db.relationship("ProjectPhase", back_populates="project_parent", lazy=True)



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
    status = db.Column(db.String(50), default="À faire")
    assigned_to = db.Column(db.Integer, db.ForeignKey("BimUsers.id"), nullable=True)
    project_id = db.Column(db.String(16), db.ForeignKey("projects.id"), nullable=False)
    project_phase_id = db.Column(db.String(16), db.ForeignKey("project_phases.id"), nullable=True)
    due_date = db.Column(db.Date, nullable=True)
    project_phase = db.relationship('ProjectPhase', back_populates='tasks', lazy=True)

    #lien vers un modèle standard
    standard_task_id = db.Column(db.String(16), db.ForeignKey("standard_tasks.id"), nullable=True)
    standard_task = db.relationship("StandardTask", backref="tasks", lazy=True)

    # lien vers tâche personnalisée (si elle existe)
    custom_task_id = db.Column(db.String(16), db.ForeignKey("custom_tasks.id"), nullable=True)
    custom_task = db.relationship("CustomTask", backref="tasks", lazy=True)
        
    @property
    def name(self):
        if self.standard_task:
            return self.standard_task.name
        elif self.custom_task:
            return self.custom_task.custom_name
        return "None"

    @property
    def description(self):
        if self.standard_task:
            return self.standard_task.description
        elif self.custom_task:
            return self.custom_task.custom_description
        return "None"

    @property
    def source_type(self):
        if self.standard_task:
            return "standard"
        elif self.custom_task:
            return "custom"
        return "undefined"



    def __init__(
        self,
        project_phase_id,
        due_date=None,
        status="À faire",
        assigned_to=None,
        standard_task=None,
        custom_task = None
    ):
        self.id = shortuuid.uuid()[:10]
        self.project_phase_id = project_phase_id
        self.status = status
        self.due_date = due_date
        self.assigned_to = assigned_to

        # déduire le projet automatiquement via la phase
        phase = ProjectPhase.query.get(project_phase_id)
        if phase:
            self.project_id = phase.project_id
        else:
            raise ValueError("project_phase_id invalide ou introuvable")

        # Si la tâche est liée à un modèle standard
        if standard_task:
            self.standard_task = standard_task
        if custom_task:
            self.custom_task = custom_task

class CustomTask(db.Model):
    __tablename__ = "custom_tasks"
    id = db.Column(db.String(16), primary_key=True, default=lambda: shortuuid.uuid()[:10])
    custom_name = db.Column(db.String(200), nullable=False)
    custom_description = db.Column(db.Text)
    estimated_days = db.Column(db.Float, nullable=True)

    def __init__(self, custom_name, custom_description, estimated_days ):
        self.id = shortuuid.uuid()[:10]
        self.custom_name = custom_name
        self.custom_description = custom_description
        self.estimated_days = estimated_days 

class StandardTask(db.Model):

    __tablename__ = "standard_tasks"
    id = db.Column(db.String(16), primary_key=True, default=lambda: shortuuid.uuid()[:10])
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    estimated_days = db.Column(db.Float, nullable=True)

    def __init__(self, name, description, estimated_days ):
        self.id = shortuuid.uuid()[:10]
        self.name = name
        self.description = description
        self.estimated_days = estimated_days        




class BimUsers(db.Model, UserMixin):
    __tablename__ = "BimUsers"

    id = db.Column(db.String(16), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    role = db.Column(
        db.String(50), nullable=False
    )  
    projects = db.relationship("Project", backref="bim_manager", lazy=True )
    password = db.Column(db.String(255))
    taj = db.Column(db.Integer)


    def __init__(self, name, email , role, password=None):
        self.id = shortuuid.uuid()[:10] 
        self.name = name
        self.email = email
        self.role = role
        self.password = password or shortuuid.uuid()[:10] 
        


    @staticmethod
    def create_default_admin():
        existing_admin = BimUsers.query.filter_by(email="admin").first()
        print("existing_admin",existing_admin)
        if not existing_admin:
            admin = BimUsers(
                name="Admin",
                email="admin",
                role="Manager",
                password="admin" 
            )
            db.session.add(admin)
            db.session.commit()