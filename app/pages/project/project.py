import dash_bootstrap_components as dbc
from dash import html, dcc, Input, Output, State, callback_context
from flask import current_app
from database.db import db
from database.model import Project
from database.model import BimUsers as dbBimUsers
from database.model import Task as  dbTask
from dash import html, dcc, Input, Output, State, callback_context, no_update
import plotly.express as px
from datetime import datetime
import pandas as pd
import calendar
from datetime import date, timedelta
from dash import html
import dash_bootstrap_components as dbc
from math import ceil
from dash import Input, Output, State, ctx
from dash.exceptions import PreventUpdate
from sqlalchemy.orm import Session
from .project_phases import ProjectPhases
import feffery_antd_components as fac
import full_calendar_component as fcc
import random

class ProjectPage:
    def __init__(self,  app):
        #self.project_id = project_id
        #self.project = Project.query.get(self.project_id)
        self.app = app
        self.register_callbacks()
        self.project_phases = ProjectPhases(self.app)

    def calculate_jours_par_semaine(self, project):
        if not (project.start_date and project.end_date and project.days_budget) :
            return None

        duration_days = (project.end_date - project.start_date).days
        nb_semaines = max(1, ceil(duration_days / 7))  
        jours_par_semaine = round(project.days_budget / nb_semaines, 2)
        return jours_par_semaine


    def generate_weekly_planning_table_by_month(self, project):
        # Date du jour au format ISO
        formatted_date = datetime.now().date().isoformat()
        COLOR_CLASSES = [
            "bg-gradient-primary",
            "bg-gradient-secondary",
            "bg-gradient-success",
            "bg-gradient-danger",
            "bg-gradient-warning",
            "bg-gradient-info",
            "bg-gradient-light",
            "bg-gradient-dark",
        ]
        # Génération des événements à partir des phases du projet
        new_events = [
            {
                "title": project_phase.phase.name,
                "start": datetime.strptime(str(project_phase.start_date), "%Y-%m-%d").date().isoformat(),
                "end": datetime.strptime(str(project_phase.end_date), "%Y-%m-%d").date().isoformat(),
                "className": random.choice(COLOR_CLASSES),

            }
            for project_phase in project.phases
            if project_phase.start_date and project_phase.end_date
        ]

        return html.Div(
            fcc.FullCalendarComponent(
                id="calendar",
                initialView="dayGridMonth",  # ou "dayGridWeek" si tu veux la vue hebdo
                headerToolbar={
                    "left": "prev,next today",
                    "center": "title",
                    "right": "listWeek,timeGridDay,timeGridWeek,dayGridMonth",
                },
                initialDate=formatted_date,
                editable=False,
                selectable=True,
                events=new_events,
                nowIndicator=True,
                navLinks=True,
                
            ),
             style={
        "height": "600px",          
        "overflow": "auto",         
        "border": "1px solid #ccc", 
        "padding": "10px",
    }
        )


    def get_month_list(self, start_date, end_date):
        months = []
        current = start_date.replace(day=1)
        while current <= end_date:
            months.append(current.strftime("%Y-%m"))
            if current.month == 12:
                current = current.replace(year=current.year + 1, month=1)
            else:
                current = current.replace(month=current.month + 1)
        return months




    def layout(self,project_id):


        self.project_id = project_id
        self.project = Project.query.get(self.project_id)
        lst_mois = self.get_month_list( self.project.start_date,  self.project.end_date)
        with current_app.app_context():
            project = Project.query.get(self.project_id)
            bim_manager = dbBimUsers.query.filter(dbBimUsers.id ==project.bim_manager_id).one_or_none()
            
            if project:
                return dbc.Container([self.task_adding_modal(),
                    dbc.Row([
                        dbc.Col(
                            [
                            self.project_info(project, bim_manager), 
                            self.project_planning(lst_mois, project)]),
                        dbc.Col(
                            [ self.project_phases.layout(project)])
                           ]),


                    dbc.Row(
                        dbc.Col(
                            dbc.Button("Back to Projects", href="/BIMSYS/projects", color="secondary", className="mt-3", size="lg"),
                            width=12,
                            className="text-center"
                        )
                    )
                ], fluid=True, style={"padding": "30px", "background": "white", "min-height": "100vh"})
            
            return self.project_not_found_ui()

    def project_planning(self, lst_mois, project):
        return dbc.Card([
                            dbc.CardHeader([
                                html.H5("Planning Prévisionnel du projet", className="mb-2"),                           
                            ]),
                            dbc.CardBody(children=[self.generate_weekly_planning_table_by_month(project=project)  ],id="calendar-container")
                        ])

    def project_not_found_ui(self):
        return dbc.Container([
                dbc.Row(
                    dbc.Col(html.H1("Project Not Found", style={"color": "red"}), width=12)
                ),
                dbc.Row(
                    dbc.Col(
                        dbc.Button("Back to Projects", href="/BIMSYS/projects", color="secondary", className="mt-3", size="lg"),
                        width=12,
                        className="text-center"
                    )
                )
            ], fluid=True, style={"padding": "30px", "background": "white", "min-height": "100vh"})

    def project_tasks(self, project):
        return dbc.Col(
                            dbc.Card([
                                dbc.CardHeader(
                                    dbc.Row([
                                        dbc.Col(html.H4("Tâches", className="mb-0"), width=10),
                                        dbc.Col(
                                            dbc.Button(
                                                html.I(className="fa fa-plus", style={"color": "blue"}),
                                                outline=True,
                                                color="primary",
                                                id="open-add-task"
                                            ),
                                            width=2,
                                            className="text-end"
                                        )
                                    ], align="center")
                                ),
                                dbc.CardBody(self.get_project_tasks(project) , id="project-tasks-list")
                            ], style={"box-shadow": "0px 4px 6px rgba(0, 0, 0, 0.1)"}),
                        )

    def project_info(self, project, bim_manager):
        return dbc.Card([
                                dbc.CardHeader(html.H2(project.name, className="card-title")),
                                dbc.CardBody([
                                     dbc.Label("Code Akuiteo"),
                                    dbc.Input(type="text", value=project.code_akuiteo, id="input-code-akuiteo", disabled=True, className="mb-3"),
                                    dbc.Label("Phase du projet"),
                                    dbc.Input(type="text", value=project.phase, id="input-phase", className="mb-3"),
                                    dbc.Label("Statut"),
                                    dbc.Select(
                                        options=[
                                            {"label": "En cours", "value": "en cours"},
                                            {"label": "Terminé", "value": "terminé"},
                                            {"label": "Non commencé", "value": "non commencé"}
                                        ],
                                        value=project.status,
                                        id="input-status",
                                        className="mb-3"
                                    ),
                                    
                                ])
                            ], style={"box-shadow": "0px 4px 6px rgba(0, 0, 0, 0.1)", "margin-bottom": "20px"})

    def task_adding_modal(self):
        users = dbBimUsers.query.all()

        return dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle("Ajouter une Tâche")),
            dbc.ModalBody([
                dbc.Label("Nom du projet"),
                dbc.Input(id="task-project-name", type="text", value=self.project.name , disabled=True),
                dbc.Label("id du projet"),
                dbc.Input(id="task-project-name", type="text", value=self.project.id , disabled=True),
                dbc.Label("Nom de la Tâche"),
                dbc.Input(id="task-name", type="text", ),
                dbc.Label("Description de la Tâche"),
                dbc.Input(id="task-description", type="text", ),
                dbc.Label("Statut"),
                dcc.Dropdown(
                    id="task-status",
                    options=[
                        {"label": "Non commencé", "value": "Non commencé"},
                        {"label": "En cours", "value": "En cours"},
                        {"label": "Terminé", "value": "Terminé"}
                    ],
                    placeholder="Sélectionnez un statut"
                ),
                
                dbc.Label("Assigné à"),
                dcc.Dropdown(id="task-responsable",
                    options=[
                        {"label": user.name , "value": user.id} for user in users
                    ],
                    placeholder="Sélectionnez un BIM MANAGER"
                ),
                dbc.Label("Date de fin"),
                dbc.Input(id="task-due-date", type="date"),
            ]),
            dbc.ModalFooter([
                dbc.Button("Annuler", id="close-add-task", className="ml-auto"),
                dbc.Button("Ajouter", id="submit-add-task", color="primary"),
            ])
        ], id="add-task-modal-uuid", is_open=False)

    def get_status_badge_color(self, task):
        status = task.status
        match =   {"Non commencé" :  "secondary",
                         "En cours" : "primary",
                       "Terminé" : "success"}
        print(match.get(status, "secondary"))
        return match.get(status, "secondary")
    
    def get_project_tasks(self, project):
        # if project.tasks:
        #     return [
        #         dbc.Row(
        #             html.A(
        #                 dbc.Card(
        #                     dbc.CardBody([
        #                         html.H5(t.name, className="card-title"),
        #                         dbc.Badge(t.status, color=self.get_status_badge_color(t), className="me-1"),
        #                         dbc.Badge(t.due_date, color="primary", className="me-1"),

        #                     ]),
        #                     className="card-hover", 
        #                     style={
        #                         "margin-bottom": "20px",
        #                         "box-shadow": "0px 4px 6px rgba(0, 0, 0, 0.1)"
        #                     }
        #                 ),
        #                 href=f"/BIMSYS/task/{t.id}",
        #                 style={"textDecoration": "none", "color": "inherit"}
        #             ),
        #         )
        #         for t in project.tasks
        #     ]
        # return html.Strong("Pas de tâche encore sur ce projet")
        pass

    def register_callbacks(self):
        @self.app.callback(
            [Output("add-task-modal-uuid", "is_open"),
             Output("project-tasks-list", "children")],
            [Input("open-add-task", "n_clicks"),
            Input("close-add-task", "n_clicks"),
            Input("submit-add-task", "n_clicks")],
            [State("add-task-modal-uuid", "is_open"),
            State("task-name", "value"),
            State("task-description", "value"),
            State("task-status", "value"),
            State("task-responsable", "value"),
            State("task-due-date", "value")],
            prevent_initial_call=True,
            
        )
        def toggle_task_modal(open_click, close_click, submit_click, is_open,
                            task_name, task_description, task_status, task_responsable, task_due_date):
            ctx = callback_context
            if not ctx.triggered:
                return is_open
            button_id = ctx.triggered[0]["prop_id"].split(".")[0]
            if button_id == "open-add-task":
                return True, no_update
            if button_id == "close-add-task":
                return False,no_update
            if button_id == "submit-add-task":
                if task_name:
                    due_date_obj = datetime.strptime(task_due_date, "%Y-%m-%d").date() if task_due_date else None
                    new_task = dbTask(
                        name=task_name,
                        description=task_description,
                        status=task_status if task_status else "Non commencé",
                        assigned_to=task_responsable,
                        project_id=self.project.id,
                        due_date=due_date_obj
                    )
                    db.session.add(new_task)
                    db.session.commit()
                self.project = Project.query.get(self.project_id)

                return False , self.get_project_tasks(self.project )
            return is_open
        
        @self.app.callback(
        Output("calendar-container", "children"),
        [
            Input("input-status", "value"),
        ],
        State("input-code-akuiteo", "value"),
    )
        def auto_save_project( status, code):
            if not ctx.triggered_id:
                raise PreventUpdate

            project = db.session.query(Project).filter(Project.id == self.project_id).first()

            if not project:
                raise PreventUpdate
           
            project.status = status           
            db.session.commit()
            
            if ctx.triggered_id in ("input-start-date","input-end-date","input-days-budget"):
                if ctx.triggered_id =="input-days-budget":
                    new_budget = project.days_budget * 750

                else :
                    new_budget = no_update
                lst_mois = self.get_month_list( project.start_date, project.end_date)
                new_calendar = [self.generate_weekly_planning_table_by_month(project=project , selected_month=mois)     for mois in lst_mois]
                return new_calendar , no_update ,new_budget
            
           

            return no_update
        

            

            
        
            