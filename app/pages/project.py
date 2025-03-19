import dash_bootstrap_components as dbc
from dash import html
from flask import current_app
from database.model import Project


class ProjectPage:
    def __init__(self, project_id):
        """Initialize Project Page with a specific project"""
        self.project_id = project_id

    def layout(self):
        """Return a Single Project View with Enhanced UI"""
        with current_app.app_context():
            project = Project.query.get(self.project_id)

            if project:
                return dbc.Container([
                    dbc.Row([
                        dbc.Col(dbc.Card([
                            dbc.CardHeader(html.H2(f"📁 {project.name}", className="card-title")),
                            dbc.CardBody([
                                html.P(f"🔹 Code: {project.code_akuiteo}", className="mb-2"),
                                html.P(f"🔹 Phase: {project.phase}", className="mb-2"),
                                html.P(f"🔹 Status: {project.status}", className="mb-2"),
                                html.P(f"📅 Start Date: {project.start_date}", className="mb-2"),
                                html.P(f"👤 BIM Manager ID: {project.bim_manager_id}", className="mb-2"),
                            ])
                        ], style={"box-shadow": "0px 4px 6px rgba(0, 0, 0, 0.1)", "margin-bottom": "20px"}), width=6),

                        # Placeholder for future sections (like project updates, team members, etc.)
                        dbc.Col([
                            dbc.Card([
                                dbc.CardHeader(html.H4("Additional Information")),
                                dbc.CardBody([
                                    html.P("More details about the project will be added here."),
                                    html.P("This section can include documents, tasks, and updates."),
                                ])
                            ], style={"box-shadow": "0px 4px 6px rgba(0, 0, 0, 0.1)"})
                        ], width=6),
                    ], className="g-4"),

                    # Back to Projects Button
                    dbc.Row([
                        dbc.Col(dbc.Button("Back to Projects", href="/BIMSYS/projects", color="secondary", className="mt-3"), width=12)
                    ], className="text-center"),
                ], fluid=True, style={"padding": "30px", "background": "#ecf0f1", "min-height": "100vh"})

        return dbc.Container([
            dbc.Row([
                dbc.Col(html.H1("Project Not Found", style={"color": "red"}), width=12),
            ]),
            dbc.Row([
                dbc.Col(dbc.Button("Back to Projects", href="/BIMSYS/projects", color="secondary", className="mt-3"), width=12, className="text-center"),
            ]),
        ], fluid=True, style={"padding": "30px", "background": "#ecf0f1", "min-height": "100vh"})
