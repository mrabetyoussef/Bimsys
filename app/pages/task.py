import dash_bootstrap_components as dbc
from dash import html, dcc
from flask import current_app
from database.db import db
from database.model import Task, Project, BimUsers as dbBimUsers
from datetime import datetime

class TaskPage:
    def __init__(self, task_id, app):
        self.task_id = task_id
        self.task = Task.query.get(self.task_id)
        self.app = app

    def layout(self):
        with current_app.app_context():
            task = Task.query.get(self.task_id)
            if task:
                assigned_user = dbBimUsers.query.get(task.assigned_to) if task.assigned_to else None
                project = Project.query.get(task.project_id) if task.project_id else None
                return dbc.Container([
                  
                    dbc.Row([
                        dbc.Col(
                            dbc.Card([
                                dbc.CardHeader(
                                    html.H4("Task Information", className="text-white"),
                                    className="bg-primary"
                                ),
                                dbc.CardBody([
                                    html.P(f"Task Name: {task.name}", className="mb-2"),
                                    html.P(f"Description: {task.description}", className="mb-2"),
                                    html.P(f"Status: {task.status}", className="mb-2"),
                                    html.P(f"Due Date: {task.due_date}", className="mb-2"),
                                    html.P(f"Assigned To: {assigned_user.name if assigned_user else 'Unassigned'}", className="mb-2")
                                ])
                            ], className="shadow-sm mb-4"),
                            width=6
                        ),
                        dbc.Col(
                            dbc.Card([
                                dbc.CardHeader(
                                    html.H4("Project Information", className="text-white"),
                                    className="bg-info"
                                ),
                                dbc.CardBody([
                                    html.P(f"Project Name: {project.name if project else 'N/A'}", className="mb-2"),
                                    html.P(f"Project Code: {project.code_akuiteo if project else 'N/A'}", className="mb-2"),
                                    html.P(f"Project Phase: {project.phase if project else 'N/A'}", className="mb-2"),
                                    html.P(f"Project Status: {project.status if project else 'N/A'}", className="mb-2")
                                ])
                            ], className="shadow-sm mb-4"),
                            width=6
                        )
                    ]),
                    dbc.Row(
                        dbc.Col(
                            dbc.Button("Back to Tasks", href=f"/BIMSYS/project/{project.id}", color="secondary", className="mt-3", size="lg"),
                            width={"size": 4, "offset": 4},
                            className="text-center"
                        )
                    )
                ], fluid=True, style={"padding": "30px", "backgroundColor": "#ecf0f1", "minHeight": "100vh"})
            return dbc.Container([
                dbc.Row(
                    dbc.Col(html.H1("Task Not Found", className="text-danger text-center"), width=12)
                ),
                dbc.Row(
                    dbc.Col(
                        dbc.Button("Back to Tasks", href="/BIMSYS/tasks", color="secondary", className="mt-3", size="lg"),
                        width=12,
                        className="text-center"
                    )
                )
            ], fluid=True, style={"padding": "30px", "backgroundColor": "#ecf0f1", "minHeight": "100vh"})
