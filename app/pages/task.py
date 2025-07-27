import dash_bootstrap_components as dbc
from dash import html, dcc, Input, Output, State, MATCH, no_update ,ctx
from flask import current_app
from database.db import db
from database.model import Task, Project, BimUsers as dbBimUsers
from datetime import datetime
import logging

class TaskPage:
    def __init__(self, app):
        self.app = app
        self.register_callbacks()

    def layout(self, task_id):
        self.task_id = task_id
        users = dbBimUsers.query.all()

        with current_app.app_context():
            task = Task.query.get(self.task_id)
            if not task:
                return dbc.Container(html.H3("Tâche introuvable", className="text-danger"))

            assigned_user = dbBimUsers.query.get(task.assigned_to) if task.assigned_to else None
            project = Project.query.get(task.project_id) if task.project_id else None

            return dbc.Container([
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader(html.H4("Tâche ")),
                            dbc.CardBody([

                                dbc.Label("Nom du projet"),
                                dbc.Input(
                                    id={"type": "task-project-name", "id": self.task_id},
                                    type="text",
                                    value=project.name if project else "",
                                    disabled=True
                                ),

                                dbc.Label("ID du projet"),
                                dbc.Input(
                                    id={"type": "task-project-id", "id": self.task_id},
                                    type="text",
                                    value=project.id if project else "",
                                    disabled=True
                                ),

                                dbc.Label("Nom de la Tâche"),
                                dbc.Input(
                                    id={"type": "task-name", "id": self.task_id},
                                    type="text",
                                    value=task.name
                                ),

                                dbc.Label("Description de la Tâche"),
                                dbc.Input(
                                    id={"type": "task-description", "id": self.task_id},
                                    type="text",
                                    value=task.description
                                ),

                                dbc.Label("Statut"),
                                dcc.Dropdown(
                                    id={"type": "task-status", "id": self.task_id},
                                    options=[
                                        {"label":  "À faire", "value":  "À faire"},
                                        {"label": "En cours", "value": "En cours"},
                                        {"label":  "Terminée", "value":  "Terminée"},
                                        {"label":  "Urgente", "value":  "Urgente"}


                                    ],
                                    value=task.status,
                                    placeholder="Sélectionnez un statut"
                                ),

                                dbc.Label("Assigné à"),
                                dcc.Dropdown(
                                    id={"type": "task-responsable", "id": self.task_id},
                                    options=[{"label": user.name, "value": user.id} for user in users],
                                    value=task.assigned_to,
                                    placeholder="Sélectionnez un BIM MANAGER"
                                ),

                                dbc.Label("Date de fin"),
                                dbc.Input(
                                    id={"type": "task-due-date", "id": self.task_id},
                                    type="date",
                                    value=task.due_date.strftime("%Y-%m-%d") if task.due_date else ""
                                )
                            ])
                        ])
                    ])
                ]),
                dbc.Row([
                    dbc.Col(
                        dbc.Button("Retour au projet", href=f"/BIMSYS/project/{project.id}", color="secondary", className="mt-3"),
                        width={"size": 4, "offset": 4},
                        className="text-center"
                    )
                ])
            ], fluid=True, style={"padding": "30px", "backgroundColor": "#ecf0f1", "minHeight": "100vh"})

    def register_callbacks(self):
        # Nom de la tâche
        @self.app.callback(
            Output({"type": "task-name", "id": MATCH}, "value"),
            Input({"type": "task-name", "id": MATCH}, "value"),
            State({"type": "task-name", "id": MATCH}, "id"),
            prevent_initial_call=True
        )
        def update_name(value, id_dict):
            task_id = id_dict["id"]
            with current_app.app_context():
                task = Task.query.get(task_id)
                if task:
                    task.name = value
                    db.session.commit()
            return value

        # Description
        @self.app.callback(
            Output({"type": "task-description", "id": MATCH}, "value"),
            Input({"type": "task-description", "id": MATCH}, "value"),
            State({"type": "task-description", "id": MATCH}, "id"),
            prevent_initial_call=True
        )
        def update_description(value, id_dict):
            task_id = id_dict["id"]
            with current_app.app_context():
                task = Task.query.get(task_id)
                if task:
                    task.description = value
                    db.session.commit()
            return value

        # Statut
        @self.app.callback(
            Output({"type": "task-status", "id": MATCH}, "value"),
            Input({"type": "task-status", "id": MATCH}, "value"),
            State({"type": "task-status", "id": MATCH}, "id"),
            prevent_initial_call=True
        )
        def update_status(value, id_dict):
            task_id = id_dict["id"]
            with current_app.app_context():
                task = Task.query.get(task_id)
                if task:
                    task.status = value
                    db.session.commit()
            return value

        # Assigné à
        @self.app.callback(
            Output({"type": "task-responsable", "id": MATCH}, "value"),
            Input({"type": "task-responsable", "id": MATCH}, "value"),
            State({"type": "task-responsable", "id": MATCH}, "id"),
            prevent_initial_call=True
        )
        def update_assigned_to(value, id_dict):
            logging.debug(ctx.triggered_id)
            logging.debug("assigné à ....")
            task_id = id_dict["id"]
            logging.debug(task_id)

            with current_app.app_context():
                task = Task.query.get(task_id)
                logging.debug(task)
                logging.debug(value)

                if task:
                    task.assigned_to = value
                    logging.debug(  task.assigned_to)

                    db.session.commit()
                    logging.debug(  task.assigned_to)

            return value

        # Date de fin
        @self.app.callback(
            Output({"type": "task-due-date", "id": MATCH}, "value"),
            Input({"type": "task-due-date", "id": MATCH}, "value"),
            State({"type": "task-due-date", "id": MATCH}, "id"),
            prevent_initial_call=True
        )
        def update_due_date(value, id_dict):
            task_id = id_dict["id"]
            with current_app.app_context():
                task = Task.query.get(task_id)
                if task:
                    try:
                        task.due_date = datetime.strptime(value, "%Y-%m-%d").date()
                        db.session.commit()
                    except ValueError:
                        return no_update
            return value
