import dash_bootstrap_components as dbc
from dash import html, dcc, Input, Output, State, callback_context, no_update
from flask import current_app
from database.db import db
from database.model import Project
from database.model import BimUsers as dbBimUsers

from datetime import datetime
import pandas as pd

class ProjectsPage:
    def __init__(self, app):
        """Initialize Projects Page and Register Callbacks"""
        self.app = app
        self.register_callbacks()

    def layout(self):
        """Return List of Projects with Add Project Modal"""
        return dbc.Container([
            dbc.Row([dbc.Col(html.H1("Projets", className="mb-4", style={"color": "#2c3e50"}), width=9),
                     dbc.Col(dbc.Button("Ajouter un Projet", id="open-add-project", color="success",
                                        className="mt-2", n_clicks=0),
                                        width=3, className="text-end"), 
                            dbc.RadioItems( options=[
                                {"label": "Vue Tableau", "value": "Vue Tableau"},
                                {"label": "Vue Carte", "value":"Vue Carte"},   ],
                                value=1,
                                id="project-view-type",
                                inline=True,),

                    ], 
                    className="align-items-center mb-4"),

            dbc.Row(id="project-list", children=self.get_project_list(), className="g-4"),

            self.add_project_modal()
        ], fluid=True, style={"padding": "30px", "background": "#ecf0f1", "min-height": "100vh"})
    
    def add_project_modal(self):
        users = dbBimUsers.query.filter(dbBimUsers.role == "BIM MANAGER")
        
        ui= dbc.Modal([
                dbc.ModalHeader(dbc.ModalTitle("Ajouter un Projet")),
                dbc.ModalBody([
                    dbc.Label("Nom du Projet"),
                    dbc.Input(id="project-name", type="text", placeholder="Entrez le nom du projet"),

                    dbc.Label("Statut"),
                    dcc.Dropdown(
                        id="project-status",
                        options=[
                            {"label": "Non commencé", "value": "Non commencé"},
                            {"label": "En cours", "value": "En cours"},
                            {"label": "Terminé", "value": "Terminé"}
                        ],
                        placeholder="Sélectionnez un statut"
                    ),

                    dbc.Label("Date de début"),
                    dbc.Input(id="project-start-date", type="date"),

                    dbc.Label("Date de fin"),
                    dbc.Input(id="project-end-date", type="date"),

                    dbc.Label("Phase"),
                    dcc.Dropdown(id="project-phase",
                        options=[
                            {"label": "EP", "value": "EP"},
                            {"label": "APS", "value": "APS"},
                            {"label": "APD", "value": "APD"},
                            {"label": "PRO", "value": "PRO"}
                        ],
                        placeholder="Sélectionnez une phase"
                    ),

                    dbc.Label("BIM MANAGER"),
                    dcc.Dropdown(id="project-bim-manager",
                        options=[
                            {"label": user.name , "value": user.id} for user in users
                        ],
                        placeholder="Sélectionnez un BIM MANAGER"
                    ),
                ]),
                dbc.ModalFooter([
                    dbc.Button("Annuler", id="close-add-project", className="ml-auto"),
                    dbc.Button("Ajouter", id="submit-add-project", color="primary"),
                ])
            ], id="add-project-modal", is_open=False)
        
        return ui
    
    def get_project_list(self):
        """Fetch and return project cards"""
        with current_app.app_context():
            projects = Project.query.all()
            return [
                dbc.Col(dbc.Card([
                    dbc.CardBody([
                        html.H5(p.name, className="card-title"),
                        html.P(f"Statut: {p.status}", className="card-text"),
                        dbc.Button("Voir plus", href=f"/BIMSYS/project/{p.id}", color="primary", className="mt-2")
                    ])
                ], style={"margin-bottom": "20px", "box-shadow": "0px 4px 6px rgba(0, 0, 0, 0.1)"}), width=4)
                for p in projects
            ]
        
    def get_project_table(self):
        projects = Project.query.all()

        project_data = [
            {
                "id": p.id,
                "name": p.name,
                "status": p.status,
                "start_date": p.start_date.strftime("%Y-%m-%d") if p.start_date else None,
                "end_date": p.end_date.strftime("%Y-%m-%d") if p.end_date else None,
                "phase": p.phase,
                "bim Manager": dbBimUsers.query.filter(p.bim_manager_id ==dbBimUsers.id).one_or_none().name
            }
            for p in projects
        ]

        df = pd.DataFrame(project_data)    

        table = dbc.Table.from_dataframe(
            df, striped=True, bordered=True, hover=True, index=True
        )
        return table





    def register_callbacks(self):
        """Register a Single Callback for Modal Control and Project adding"""

        @self.app.callback(
            [Output("add-project-modal", "is_open"),
             Output("project-name", "value"),
             Output("project-status", "value"),
             Output("project-start-date", "value"),
             Output("project-end-date", "value"),
             Output("project-phase", "value"),
             Output("project-bim-manager", "value"),
             Output("project-list", "children")],
            [Input("open-add-project", "n_clicks"),
             Input("close-add-project", "n_clicks"),
             Input("submit-add-project", "n_clicks"),
             Input("project-view-type" , "value")],

            [State("add-project-modal", "is_open"),
             State("project-name", "value"),
             State("project-status", "value"),
             State("project-start-date", "value"),
             State("project-end-date", "value"),
             State("project-phase", "value"),
             State("project-bim-manager", "value"),
             State("project-view-type" , "value")],
            prevent_initial_call=True
        )
        def handle_modal_and_add_project(open_click, close_click, submit_click,project_view_type_click, is_open,
                                         name, status, start_date, end_date, phase, bim_manager_id , project_view_type):
            


            ctx = callback_context

            if not ctx.triggered:
                return is_open, no_update, no_update, no_update, no_update, no_update, no_update, no_update

            button_id = ctx.triggered[0]["prop_id"].split(".")[0]

            if button_id == "open-add-project":
                return True, no_update, no_update, no_update, no_update, no_update, no_update, no_update

            if button_id == "close-add-project":
                return False, no_update, no_update, no_update, no_update, no_update, no_update, no_update

            if button_id == "submit-add-project":
                if not all([name, status, start_date, end_date, phase, bim_manager_id]):
                    return is_open, no_update, no_update, no_update, no_update, no_update, no_update, no_update

                try:
                    start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
                    end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()
                except ValueError:
                    return is_open, no_update, no_update, no_update, no_update, no_update, no_update, no_update

                with current_app.app_context():
                    
                    new_project = Project(
                        name=name,
                        status=status,
                        start_date=start_date_obj,
                        end_date=end_date_obj,
                        phase=phase,
                        bim_manager_id=bim_manager_id
                    )
                    db.session.add(new_project)
                    db.session.commit()
                if project_view_type == "Vue Carte" : 
                    projects_display = self.get_project_list()
                else :
                    projects_display = self.get_project_table()

                return (False,  None, None, None, None, None, None,     projects_display )  

            if button_id == "project-view-type" :
                print(project_view_type_click)
                if project_view_type_click == "Vue Carte" : 
                    projects_display = self.get_project_list()
                else :
                    projects_display = self.get_project_table()

                return (False,  None, None, None, None, None, None,     projects_display )  