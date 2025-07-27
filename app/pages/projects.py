import dash_bootstrap_components as dbc
from dash import html, dcc, Input, Output, State, callback_context, no_update
from flask import current_app
from database.db import db
from database.model import Project

from datetime import datetime
import pandas as pd

class ProjectsPage:
    def __init__(self, app):
        """Initialize Projects Page and Register Callbacks"""
        self.app = app
        self.register_callbacks()
        self.view_type = "Vue Carte"

    def layout(self):
        """Return List of Projects with Add Project Modal"""
        projects_display = self.get_projects_display()
        
        return dbc.Container([
            # Header with title and controls
            dbc.Row([
                dbc.Col([
                    html.H1("Projets", className="mb-0", style={"color": "#2c3e50", "font-weight": "600"}),
                    html.P(f"Gérez vos projets et suivez leur progression", 
                          className="text-muted mb-0", style={"font-size": "0.9rem"})
                ], width=6),
                dbc.Col([
                    dbc.ButtonGroup([
                        dbc.Button([
                            html.I(className="fas fa-th-large me-2"),
                            "Vue Carte"
                        ], id="btn-card-view", color="primary", outline=True, 
                           active=self.view_type == "Vue Carte", size="sm"),
                        dbc.Button([
                            html.I(className="fas fa-table me-2"),
                            "Vue Tableau"
                        ], id="btn-table-view", color="primary", outline=True, 
                           active=self.view_type == "Vue Tableau", size="sm"),
                    ], className="me-3"),
                    dbc.Button([
                        html.I(className="fas fa-plus me-2"),
                        "Nouveau Projet"
                    ], id="open-add-project", color="success", size="sm", n_clicks=0)
                ], width=6, className="text-end d-flex justify-content-end align-items-center")
            ], className="mb-4 pb-3", style={"border-bottom": "1px solid #e9ecef"}),

            # Projects display area
            dbc.Row(id="project-list", children=projects_display, className="g-4"),

            # Add project modal
            self.add_project_modal(),
            
            # Toast for notifications
            dbc.Toast(
                id="project-toast",
                header="Notification",
                is_open=False,
                dismissable=True,
                duration=4000,
                style={"position": "fixed", "top": 20, "right": 20, "width": 350, "z-index": 1050}
            )
        ], fluid=True, style={"padding": "30px", "background": "#f8f9fa", "min-height": "100vh"})
    
    def add_project_modal(self):
        """Enhanced modal for adding new projects"""
        return dbc.Modal([
            dbc.ModalHeader([
                dbc.ModalTitle([
                    html.I(className="fas fa-plus-circle me-2"),
                    "Ajouter un Nouveau Projet"
                ], style={"color": "#2c3e50"})
            ]),
            dbc.ModalBody([
                dbc.Form([
                    # Project Name
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Nom du Projet *", className="fw-bold"),
                            dbc.Input(
                                id="project-name", 
                                type="text", 
                                placeholder="Ex: Résidence Les Jardins",
                                className="mb-3"
                            ),
                            dbc.FormFeedback("Veuillez saisir un nom de projet", type="invalid")
                        ])
                    ]),
                    
                    # Akuiteo Code
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Code Akuiteo *", className="fw-bold"),
                            dbc.Input(
                                id="project-akuiteo-code", 
                                type="text", 
                                placeholder="Ex: AK2024001",
                                className="mb-3"
                            ),
                            dbc.FormFeedback("Veuillez saisir un code Akuiteo", type="invalid")
                        ])
                    ]),
                    
                    # Status
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Statut", className="fw-bold"),
                            dcc.Dropdown(
                                id="project-status",
                                options=[
                                    {"label": "Non commencé", "value": "Non commencé"},
                                    {"label": "En cours", "value": "En cours"},
                                    {"label": "En attente", "value": "En attente"},
                                    {"label": "Terminé", "value": "Terminé"},
                                    {"label": "Suspendu", "value": "Suspendu"}
                                ],
                                placeholder="Sélectionnez un statut (optionnel)",
                                value="Non commencé",  # Default value
                                className="mb-3"
                            )
                        ])
                    ])
                ])
            ]),
            dbc.ModalFooter([
                dbc.Button([
                    html.I(className="fas fa-times me-2"),
                    "Annuler"
                ], id="close-add-project", color="secondary", outline=True),
                dbc.Button([
                    html.I(className="fas fa-save me-2"),
                    "Créer le Projet"
                ], id="submit-add-project", color="success", className="ms-2"),
            ])
        ], id="add-project-modal", is_open=False, size="lg")
    
    def get_projects_display(self):
        """Get projects display based on current view type"""
        if self.view_type == "Vue Carte":
            return self.get_project_cards()
        else:
            return self.get_project_table()
    
    def get_project_cards(self):
        """Fetch all projects and return as enhanced cards"""
        with current_app.app_context():
            projects = Project.query.all()
            
            if not projects:
                return [
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.Div([
                                    html.I(className="fas fa-folder-open", style={"font-size": "3rem", "color": "#6c757d"}),
                                    html.H5("Aucun projet", className="mt-3 text-muted"),
                                    html.P("Commencez par créer votre premier projet", className="text-muted")
                                ], className="text-center py-5")
                            ])
                        ], className="border-0 shadow-sm")
                    ], width=12)
                ]
            
            return [
                dbc.Col(
                    html.A(
                        dbc.Card([
                            dbc.CardBody([
                                dbc.Row([
                                    dbc.Col([
                                        html.H5(p.name, className="card-title mb-2", style={"color": "#2c3e50"}),
                                        html.P([
                                            html.I(className="fas fa-code me-2", style={"color": "#6c757d"}),
                                            f"Code: {p.code_akuiteo}"
                                        ], className="card-text text-muted mb-2", style={"font-size": "0.9rem"}),
                                        dbc.Badge(
                                            p.status,
                                            color=self.get_status_color(p.status),
                                            className="me-2"
                                        )
                                    ], width=12)
                                ]),
                                html.Hr(className="my-3"),
                                dbc.Row([
                                    dbc.Col([
                                        html.Small([
                                            html.I(className="fas fa-calendar me-1"),
                                            "Créé le ", datetime.now().strftime("%d/%m/%Y")
                                        ], className="text-muted")
                                    ], width=12)
                                ])
                            ])
                        ], className="h-100 shadow-sm border-0 card-hover", style={
                            "transition": "all 0.3s ease",
                            "cursor": "pointer"
                        }),
                        href=f"/BIMSYS/project/{p.id}",
                        style={"textDecoration": "none", "color": "inherit"}
                    ),
                    width=4, className="mb-4"
                )
                for p in projects
            ]

    def get_project_table(self):
        """Enhanced table view for projects"""
        with current_app.app_context():
            projects = Project.query.all()
            
            if not projects:
                return [
                    dbc.Col([
                        dbc.Alert([
                            html.I(className="fas fa-info-circle me-2"),
                            "Aucun projet disponible. Créez votre premier projet pour commencer."
                        ], color="info", className="text-center")
                    ], width=12)
                ]

            # Create enhanced table
            table_header = [
                html.Thead([
                    html.Tr([
                        html.Th("Nom du Projet", style={"background-color": "#f8f9fa", "border": "none"}),
                        html.Th("Code Akuiteo", style={"background-color": "#f8f9fa", "border": "none"}),
                        html.Th("Statut", style={"background-color": "#f8f9fa", "border": "none"}),
                        html.Th("Actions", style={"background-color": "#f8f9fa", "border": "none"})
                    ])
                ])
            ]
            
            table_body = [
                html.Tbody([
                    html.Tr([
                        html.Td([
                            html.A(
                                p.name,
                                href=f"/BIMSYS/project/{p.id}",
                                style={"color": "#2c3e50", "text-decoration": "none", "font-weight": "500"}
                            )
                        ]),
                        html.Td([
                            html.Code(p.code_akuiteo, style={"background-color": "#f8f9fa", "color": "#6c757d"})
                        ]),
                        html.Td([
                            dbc.Badge(
                                p.status,
                                color=self.get_status_color(p.status),
                                className="me-2"
                            )
                        ]),
                        html.Td([
                            dbc.ButtonGroup([
                                dbc.Button([
                                    html.I(className="fas fa-eye")
                                ], color="primary", size="sm", outline=True, 
                                   href=f"/BIMSYS/project/{p.id}"),
                                dbc.Button([
                                    html.I(className="fas fa-edit")
                                ], color="warning", size="sm", outline=True),
                            ], size="sm")
                        ])
                    ], style={"border-bottom": "1px solid #e9ecef"})
                    for p in projects
                ])
            ]

            return [
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.Div([
                                dbc.Table(
                                    table_header + table_body,
                                    responsive=True,
                                    hover=True,
                                    className="mb-0"
                                )
                            ])
                        ])
                    ], className="shadow-sm border-0")
                ], width=12)
            ]

    def get_status_color(self, status):
        """Return appropriate color for status badge"""
        status_colors = {
            "Non commencé": "secondary",
            "En cours": "primary",
            "En attente": "warning",
            "Terminé": "success",
            "Suspendu": "danger"
        }
        return status_colors.get(status, "secondary")

    def register_callbacks(self):
        """Register callbacks for modal control, project adding, and view switching"""

        @self.app.callback(
            [Output("add-project-modal", "is_open"),
             Output("project-name", "value"),
             Output("project-akuiteo-code", "value"),
             Output("project-status", "value"),
             Output("project-list", "children"),
             Output("project-toast", "is_open"),
             Output("project-toast", "children"),
             Output("project-toast", "icon"),
             Output("btn-card-view", "active"),
             Output("btn-table-view", "active")],
            [Input("open-add-project", "n_clicks"),
             Input("close-add-project", "n_clicks"),
             Input("submit-add-project", "n_clicks"),
             Input("btn-card-view", "n_clicks"),
             Input("btn-table-view", "n_clicks")],
            [State("add-project-modal", "is_open"),
             State("project-name", "value"),
             State("project-akuiteo-code", "value"),
             State("project-status", "value")],
            prevent_initial_call=True
        )
        def handle_project_interactions(open_click, close_click, submit_click, 
                                      card_view_click, table_view_click,
                                      is_open, name, akuiteo_code, status):
            
            ctx = callback_context
            if not ctx.triggered:
                return (no_update, no_update, no_update, no_update, no_update, 
                       no_update, no_update, no_update, no_update, no_update)

            button_id = ctx.triggered[0]["prop_id"].split(".")[0]
            
            # Handle view switching
            if button_id == "btn-card-view":
                self.view_type = "Vue Carte"
                projects_display = self.get_projects_display()
                return (no_update, no_update, no_update, no_update, projects_display,
                       no_update, no_update, no_update, True, False)
            
            elif button_id == "btn-table-view":
                self.view_type = "Vue Tableau"
                projects_display = self.get_projects_display()
                return (no_update, no_update, no_update, no_update, projects_display,
                       no_update, no_update, no_update, False, True)

            # Handle modal operations
            elif button_id == "open-add-project":
                return (True, no_update, no_update, "Non commencé", no_update,
                       no_update, no_update, no_update, 
                       self.view_type == "Vue Carte", self.view_type == "Vue Tableau")

            elif button_id == "close-add-project":
                return (False, "", "", "Non commencé", no_update,
                       no_update, no_update, no_update,
                       self.view_type == "Vue Carte", self.view_type == "Vue Tableau")

            elif button_id == "submit-add-project":
                import logging
                # Validate required fields
                if not name or not name.strip():
                    return (is_open, no_update, no_update, no_update, no_update,
                           True, "Veuillez saisir un nom de projet", "danger",
                           self.view_type == "Vue Carte", self.view_type == "Vue Tableau")
                
                if not akuiteo_code or not akuiteo_code.strip():
                    return (is_open, no_update, no_update, no_update, no_update,
                           True, "Veuillez saisir un code Akuiteo", "danger",
                           self.view_type == "Vue Carte", self.view_type == "Vue Tableau")

                try:
                    with current_app.app_context():
                        # Check if project with same code already exists
                        existing_project = Project.query.filter_by(code_akuiteo=akuiteo_code.strip()).first()
                        if existing_project:
                            return (is_open, no_update, no_update, no_update, no_update,
                                   True, f"Un projet avec le code {akuiteo_code} existe déjà", "danger",
                                   self.view_type == "Vue Carte", self.view_type == "Vue Tableau")
                        logging.debug(existing_project)
                        try :
                            
                            # Create new project
                            new_project = Project(
                                name=name.strip(),
                                code_akuiteo=akuiteo_code.strip(),
                                status=status or "Non commencé",
                            )
                            logging.debug(new_project)
                        except Exception as ex:
                            logging.debug(ex)


                        
                        db.session.add(new_project)
                        db.session.commit()
                        
                        projects_display = self.get_projects_display()
                        
                        return (False, "", "", "Non commencé", projects_display,
                               True, f"Projet '{name}' créé avec succès!", "success",
                               self.view_type == "Vue Carte", self.view_type == "Vue Tableau")
                        
                except Exception as e:
                    return (is_open, no_update, no_update, no_update, no_update,
                           True, f"Erreur lors de la création du projet: {str(e)}", "danger",
                           self.view_type == "Vue Carte", self.view_type == "Vue Tableau")

            return (no_update, no_update, no_update, no_update, no_update,
                   no_update, no_update, no_update, 
                   self.view_type == "Vue Carte", self.view_type == "Vue Tableau")