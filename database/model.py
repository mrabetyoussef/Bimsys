import shortuuid
from database.db import db 
from sqlalchemy import Float , Boolean
from datetime import date
from flask_login import UserMixin
import logging
from dateutil.rrule import rrule, WEEKLY, MO
import logging
from datetime import timedelta

class Phase(db.Model):
    __tablename__ = "phases"
    id = db.Column(db.String(16), primary_key=True, unique=True, nullable=False, default=lambda: shortuuid.uuid()[:10])
    name =  db.Column(db.String(255), nullable=False)
    
    def __init__(self, name):
        self.id = shortuuid.uuid()[:10]
        self.name = name

class ProjectPhase(db.Model):
    __tablename__ = "project_phases"

    id = db.Column(db.String(16), primary_key=True, nullable=False, default=lambda: shortuuid.uuid()[:10])
    project_id = db.Column(db.String(16), db.ForeignKey("projects.id", name="fk_projectphase_project"), nullable=False)
    phase_id = db.Column(db.String(16), db.ForeignKey("phases.id", name="fk_projectphase_phase"), nullable=False)
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    costum_days_budget =  db.Column(Float)
    tasks_days_budget =  db.Column(Float)
    days_budget = db.Column(Float)
    euros_budget = db.Column(Float)
    assigned_bimuser_id = db.Column(db.String(16), db.ForeignKey("BimUsers.id", name="fk_projectphase_user"))
    status = db.Column(db.String(16))
    project_parent = db.relationship("Project", back_populates="phases")
    phase = db.relationship('Phase', backref='project_phases', lazy=True)
    tasks = db.relationship("Task", back_populates="project_phase", lazy=True)
    assigned_bimuser = db.relationship("BimUsers")


    def __init__(self, project_id, phase_id,start_date=None , end_date = None , days_budget = None,assigned_bimuser_id=None,euros_budget=None,costum_days_budget=None):
        self.id = shortuuid.uuid()[:10]
        self.project_id = project_id
        self.phase_id = phase_id
        self.start_date=start_date
        self.end_date=end_date
        self.days_budget=days_budget
        self.assigned_bimuser_id = assigned_bimuser_id
        self.euros_budget = euros_budget
        self.costum_days_budget=costum_days_budget
        
class Project(db.Model):
        

    __tablename__ = "projects"

    id = db.Column(db.String(16), primary_key=True, unique=True, nullable=False, default=lambda: shortuuid.uuid()[:10])
    code_akuiteo = db.Column(db.String(16))
    name = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(50), nullable=False)
    phases = db.relationship("ProjectPhase", back_populates="project_parent", lazy=True )



    def __init__(self, name, status, code_akuiteo):
        self.id = shortuuid.uuid()[:10] 
        self.name = name
        self.status = status
        self.code_akuiteo = code_akuiteo
     

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
    def parent_task(self):
        return self.standard_task or self.custom_task

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
    category1 = db.Column(db.Text, nullable=True)
    category2 = db.Column(db.Text, nullable=True)


    def __init__(self, name, description, estimated_days ,category1,category2):
        self.id = shortuuid.uuid()[:10]
        self.name = name
        self.description = description
        self.estimated_days = estimated_days        
        self.category1 = category1
        self.category2 = category2




class BimUsers(db.Model, UserMixin):
    __tablename__ = "BimUsers"

    id = db.Column(db.String(16), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    lastname = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    role = db.Column(
        db.String(50), nullable=False
    )  
    password = db.Column(db.String(255))
    taj = db.Column(db.Integer)
    projects = db.relationship('ProjectPhase', back_populates='assigned_bimuser', lazy=True)


    def __init__(self, name,lastname, email , role, password=None , taj=None):
        self.id = shortuuid.uuid()[:10] 
        self.name = name
        self.lastname = lastname
        self.email = email
        self.role = role
        self.taj = taj
        self.password = password or shortuuid.uuid()[:10] 
        


    @staticmethod
    def create_default_admin():
        existing_admin = BimUsers.query.filter_by(email="admin").first()
        print("existing_admin",existing_admin)
        if not existing_admin:
            admin = BimUsers(
                name="Admin",
                lastname="Admin",
                email="admin",
                role="Manager",
                password="admin" 
            )
            db.session.add(admin)
            db.session.commit()

class RealWorkload(db.Model):
    __tablename__ = "real_workload"

    __table_args__ = (
        db.UniqueConstraint('bimuser_id', 'project_phase_id', 'week', name='uq_real_user_phase_week'),
    )

    id = db.Column(db.String(16), primary_key=True, default=lambda: shortuuid.uuid()[:10])
    bimuser_id = db.Column(db.String(16), db.ForeignKey("BimUsers.id"), nullable=False)
    project_phase_id = db.Column(db.String(16), db.ForeignKey("project_phases.id"), nullable=False)
    week = db.Column(db.String(10), nullable=False)  
    actual_days = db.Column(db.Float, nullable=True)  

    project_phase = db.relationship("ProjectPhase", backref="real_workload_entries")
    bimuser = db.relationship("BimUsers", backref="real_workload_entries")


class DailyWorkload(db.Model):
    __tablename__ = "daily_workload"

    id = db.Column(db.String(16), primary_key=True, default=lambda: shortuuid.uuid()[:10])
    project_id = db.Column(db.String(16), db.ForeignKey("projects.id"), nullable=False)
    project_phase_id = db.Column(db.String(16), db.ForeignKey("project_phases.id"), nullable=False)
    user_id = db.Column(db.String(16), db.ForeignKey("BimUsers.id"), nullable=True)  
    hours = db.Column(db.Float, nullable=False, default=0.0)
    date = db.Column(db.Date, nullable=False)
    project = db.relationship("Project", backref="daily_workloads")
    phase = db.relationship("ProjectPhase", backref="daily_workloads")
    user = db.relationship("BimUsers", backref="daily_workloads")
    start_time = db.Column(db.Time)
    end_time = db.Column(db.Time)

    def __init__(self,id ,project_id ,project_phase_id,user_id,hours,date,end_time,start_time):
        self.id = id
        self.project_id=project_id
        self.project_phase_id=project_phase_id
        self.user_id=user_id
        self.hours=hours
        self.date = date
        self.start_time = start_time
        self.end_time = end_time
    @property
    def week_iso(self):
        """Retourne la semaine ISO sous forme '2025-W35' par ex."""
        iso_year, iso_week, _ = self.date.isocalendar()
        return f"{iso_year}-W{iso_week:02d}"
    
class Workload(db.Model):
    __tablename__ = "workload"


    __table_args__ = (
        db.UniqueConstraint('bimuser_id', 'project_phase_id', 'week', name='uq_user_phase_week'),
    )
    id = db.Column(db.String(16), primary_key=True, default=lambda: shortuuid.uuid()[:10])
    bimuser_id = db.Column(db.String(16), db.ForeignKey("BimUsers.id"), nullable=False)
    project_phase_id = db.Column(db.String(16), db.ForeignKey("project_phases.id"), nullable=False)
    week = db.Column(db.String(10), nullable=False)  
    planned_days = db.Column(db.Float, nullable=True)  
    actual_days = db.Column(db.Float, nullable=True)  

    project_phase = db.relationship("ProjectPhase", backref="workload_entries")
    bimuser = db.relationship("BimUsers", backref="workload_entries")


    def __init__(self, bimuser_id, project_phase_id, week, planned_days=None, actual_days=None, type_mission=None, note=None):
        self.id = shortuuid.uuid()[:10]
        self.bimuser_id = bimuser_id
        self.project_phase_id = project_phase_id
        self.week = week
        self.planned_days = planned_days
        self.actual_days = actual_days
        self.type_mission = type_mission
        self.note = note
    

    
    @staticmethod
    def get_iso_weeks_list(start_date, end_date):
            """
            Renvoie la liste des semaines ISO entre deux dates (format : '2025-W27'),
            en prenant comme début de semaine le lundi.
            """
            if not start_date or not end_date or start_date > end_date:
                return []

            # Aligner le départ sur le lundi précédent ou égal à start_date
            aligned_start = start_date - timedelta(days=start_date.weekday())

            # Génération des lundis de chaque semaine jusqu'à end_date
            mondays = list(rrule(freq=WEEKLY, dtstart=aligned_start, until=end_date, byweekday=MO))

            # Conversion en format ISO 'YYYY-Www'
            iso_weeks = [f"{d.isocalendar()[0]}-W{d.isocalendar()[1]:02d}" for d in mondays]

            return iso_weeks


    @staticmethod
    def update_workload(project_phase):

        if not (project_phase.assigned_bimuser_id and project_phase.start_date and project_phase.end_date):
            logging.warning("Phase non valide pour le plan de charge")
            return

        total_days = project_phase.days_budget or 0
        if total_days <= 0:
            logging.info("Aucun jour budgété pour cette phase, plan de charge non généré.")
            return

        

        weeks_iso = Workload.get_iso_weeks_list(project_phase.start_date, project_phase.end_date)
        logging.debug(f"iso_weeks : {len(weeks_iso)}")
        logging.debug(f"total_days : {(total_days)}")


        days_per_week = round(total_days / len(weeks_iso), 2)
        
        Workload.query.filter(
            Workload.project_phase_id == project_phase.id,
            Workload.bimuser_id == project_phase.assigned_bimuser_id,
            ~Workload.week.in_(weeks_iso)
        ).delete(synchronize_session=False)

        for week in weeks_iso:

            logging.warning(f"{project_phase.assigned_bimuser_id} , {project_phase.id,} , {week}")

            entry = Workload.query.filter_by(
                bimuser_id=project_phase.assigned_bimuser_id,
                project_phase_id=project_phase.id,
                week=week
            ).one_or_none()

            if entry:
                entry.planned_days = days_per_week
            else:
                new_entry = Workload(
                    bimuser_id=project_phase.assigned_bimuser_id,
                    project_phase_id=project_phase.id,
                    week=week,
                    planned_days=days_per_week,
                    actual_days=None,
                    type_mission=None
                )
                db.session.add(new_entry)
        logging.warning(f"done for project phase {project_phase}")
        try:
            db.session.commit()
            logging.debug(f"Workload mis à jour pour la phase {project_phase.id}")
        except Exception as ex:
            db.session.rollback()
            logging.error(f"Erreur lors de la mise à jour du workload : {str(ex)}")
