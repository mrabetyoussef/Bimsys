import dash_bootstrap_components as dbc
from dash import html, dcc, Input, Output, State, callback_context
from flask import current_app
from database.db import db
from database.model import Project

class ProjectsPage:
    def __init__(self, app):
        """Initialize Projects Page and Register Callbacks"""
        self.app = app
        self.register_callbacks()  

    def layout(self):
        """Return List of Projects with Add Project Modal"""
        with current_app.app_context():
            projects = Project.query.all()

        return dbc.Container([
            dbc.Row([
                dbc.Col(html.H1("📂 Projets", className="mb-4", style={"color": "#2c3e50"}), width=9),
                dbc.Col(dbc.Button("➕ Ajouter un Projet", id="open-add-project", color="success", 
                                   className="mt-2", n_clicks=0),
                        width=3, className="text-end"),
            ], className="align-items-center mb-4"),

            dbc.Row(id="project-list", children=[
                dbc.Col(dbc.Card([
                    dbc.CardBody([
                        html.H5(p.name, className="card-title"),
                        html.P(f"Statut: {p.status}", className="card-text"),
                        dbc.Button("Voir plus", href=f"/BIMSYS/project/{p.id}", color="primary", className="mt-2")
                    ])
                ], style={"margin-bottom": "20px", "box-shadow": "0px 4px 6px rgba(0, 0, 0, 0.1)"}), width=4)
                for p in projects
            ], className="g-4"),

            dbc.Modal([
                dbc.ModalHeader(dbc.ModalTitle("Ajouter un Projet")),
                dbc.ModalBody([
                    dbc.Label("Nom du Projet"),
                    dbc.Input(id="project-name", type="text", placeholder="Entrez le nom du projet"),
                ]),
                dbc.ModalFooter([
                    dbc.Button("Annuler", id="close-add-project", className="ml-auto"),
                    dbc.Button("Ajouter", id="submit-add-project", color="primary"),
                ])
            ], id="add-project-modal", is_open=False),
        ], fluid=True, style={"padding": "30px", "background": "#ecf0f1", "min-height": "100vh"})

    def register_callbacks(self):
        """Register Callbacks for Adding a Project"""
        @self.app.callback(
            Output("add-project-modal", "is_open"),
            [Input("open-add-project", "n_clicks"),
             Input("close-add-project", "n_clicks")],
            [State("add-project-modal", "is_open")]
        )
        def toggle_modal(open_click, close_click, is_open):
            ctx = callback_context  
            print(f"Button Click Detected: {ctx.triggered}")  

            if not ctx.triggered:
                return is_open

            button_id = ctx.triggered[0]["prop_id"].split(".")[0]
            print(f"Clicked Button: {button_id}")  

            if button_id == "open-add-project":
                return True
            elif button_id == "close-add-project":
                return False
            return is_open
