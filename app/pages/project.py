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




class ProjectPage:
    def __init__(self,  app):
        #self.project_id = project_id
        #self.project = Project.query.get(self.project_id)
        self.app = app
        self.register_callbacks()


    def calculate_jours_par_semaine(self, project):
        if not (project.start_date and project.end_date):
            return None

        duration_days = (project.end_date - project.start_date).days
        nb_semaines = max(1, ceil(duration_days / 7))  # éviter division par 0
        jours_par_semaine = round(20 / nb_semaines, 2)
        return jours_par_semaine

    def generate_weekly_planning_table_by_month(self, project, selected_month: str = None, jours_par_semaine=None):
        from math import ceil
        from datetime import date

        # Mois courant par défaut
        if not selected_month:
            selected_month = date.today().strftime("%Y-%m")

        year, month = map(int, selected_month.split("-"))
        start_of_month = date(year, month, 1)
        last_day = calendar.monthrange(year, month)[1]
        end_of_month = date(year, month, last_day)

        # Début au lundi précédent le 1er du mois
        current = start_of_month - timedelta(days=start_of_month.weekday())
        weeks = []

        while current <= end_of_month:
            weeks.append({
                "monday": current,
                "end": current + timedelta(days=6)
            })
            current += timedelta(days=7)

        jours_par_semaine = jours_par_semaine or self.calculate_jours_par_semaine(project)

        # Colonnes avec date du lundi
        week_headers = [html.Th(w["monday"].strftime("%d/%m/%Y")) for w in weeks]

        # Ligne des jours alloués
        jours_row = html.Tr([html.Td("Jours alloués")] + [
            html.Td(f"{jours_par_semaine} j") for _ in weeks
        ])

   
        return dbc.Table([
            html.Thead(html.Tr([html.Th("")] + week_headers)),
            html.Tbody([jours_row])
        ], bordered=True, striped=True, hover=True, className="weekly-planning-matrix")

    def get_month_list(self, start_date, end_date):
        months = []
        current = start_date.replace(day=1)
        while current <= end_date:
            months.append(current.strftime("%Y-%m"))
            # passer au 1er jour du mois suivant
            if current.month == 12:
                current = current.replace(year=current.year + 1, month=1)
            else:
                current = current.replace(month=current.month + 1)
        return months


    def layout(self,project_id):


        self.project_id = project_id
        self.project = Project.query.get(self.project_id)
        lst_mois = self.get_month_list( self.project.start_date,  self.project.end_date)
        print(list)
        with current_app.app_context():
            project = Project.query.get(self.project_id)
            bim_manager = dbBimUsers.query.filter(dbBimUsers.id ==project.bim_manager_id).one_or_none()
            
            if project:
                return dbc.Container([self.task_adding_modal(),
                    dbc.Row([
                        dbc.Col(
                            [dbc.Card([
                                dbc.CardHeader(html.H2(project.name, className="card-title")),
                                dbc.CardBody([
                                    html.P(f"Code: {project.code_akuiteo}", className="mb-2"),
                                    html.P(f"Phase: {project.phase}", className="mb-2"),
                                    html.P(f"Status: {project.status}", className="mb-2"),
                                    html.P(f"Date de début: {project.start_date}", className="mb-2"),
                                    html.P(f"Date de fin: {project.end_date}", className="mb-2"),
                                    html.P(f"BIM Manager: {bim_manager.name}", className="mb-2"),
                                ])
                            ], style={"box-shadow": "0px 4px 6px rgba(0, 0, 0, 0.1)", "margin-bottom": "20px"}),
                            dbc.Card([
                            dbc.CardHeader([
                                html.H5("Planning Prévisionnel du projet", className="mb-2"),
                                dcc.Dropdown(
                                    id="project-calendar-month",
                                    options=[
                                        {"label": date(2025, m, 1).strftime("%B %Y"), "value": f"2025-{m:02d}"}
                                        for m in range(1, 13)
                                    ],
                                    value=project.start_date.strftime("%Y-%m"),
                                    clearable=False
                                )
                            ]),
                            dbc.CardBody(children=[self.generate_weekly_planning_table_by_month(project=project , selected_month=mois)   for mois in lst_mois],id="calendar-container")
                        ])
                    
                            
                            
                            ], width=6
                        ),
                        dbc.Col(
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
                            width=6
                        )
                    ], className="g-4"),
                    dbc.Row(
                        dbc.Col(
                            dbc.Button("Back to Projects", href="/BIMSYS/projects", color="secondary", className="mt-3", size="lg"),
                            width=12,
                            className="text-center"
                        )
                    )
                ], fluid=True, style={"padding": "30px", "background": "#ecf0f1", "min-height": "100vh"})
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
            ], fluid=True, style={"padding": "30px", "background": "#ecf0f1", "min-height": "100vh"})

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
        if project.tasks:
            return [
                dbc.Row(
                    html.A(
                        dbc.Card(
                            dbc.CardBody([
                                html.H5(t.name, className="card-title"),
                                dbc.Badge(t.status, color=self.get_status_badge_color(t), className="me-1"),
                                dbc.Badge(t.due_date, color="primary", className="me-1"),

                            ]),
                            className="card-hover", 
                            style={
                                "margin-bottom": "20px",
                                "box-shadow": "0px 4px 6px rgba(0, 0, 0, 0.1)"
                            }
                        ),
                        href=f"/BIMSYS/task/{t.id}",
                        style={"textDecoration": "none", "color": "inherit"}
                    ),
                )
                for t in project.tasks
            ]
        return html.Strong("Pas de tâche encore sur ce projet")

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
        