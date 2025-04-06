import dash_bootstrap_components as dbc
from dash import html, dcc, Input, Output, State, callback_context
from flask import current_app
from database.db import db
from database.model import Project
from database.model import BimUsers as dbBimUsers
from database.model import Task as  dbTask
from dash import html, dcc, Input, Output, State, callback_context, no_update

from datetime import datetime
import pandas as pd


class ProjectPage:
    def __init__(self,  app):
        #self.project_id = project_id
        #self.project = Project.query.get(self.project_id)
        self.app = app
        self.register_callbacks()

    def layout(self,project_id):
        self.project_id = project_id
        self.project = Project.query.get(self.project_id)

        with current_app.app_context():
            project = Project.query.get(self.project_id)
            if project:
                return dbc.Container([self.task_adding_modal(),
                    dbc.Row([
                        dbc.Col(
                            dbc.Card([
                                dbc.CardHeader(html.H2(project.name, className="card-title")),
                                dbc.CardBody([
                                    html.P(f"Code: {project.code_akuiteo}", className="mb-2"),
                                    html.P(f"Phase: {project.phase}", className="mb-2"),
                                    html.P(f"Status: {project.status}", className="mb-2"),
                                    html.P(f"Start Date: {project.start_date}", className="mb-2"),
                                    html.P(f"BIM Manager ID: {project.bim_manager_id}", className="mb-2"),
                                ])
                            ], style={"box-shadow": "0px 4px 6px rgba(0, 0, 0, 0.1)", "margin-bottom": "20px"}),
                            width=6
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

