import dash_bootstrap_components as dbc
from dash import html, dcc, Input, Output, State, callback_context, no_update
from flask import current_app
from database.db import db
from database.model import BimUsers as dbBimUsers
from datetime import datetime
import pandas as pd

class BimUsers:
    def __init__(self, app):
        """Initialize Users Page and Register Callbacks"""
        self.app = app
        self.register_callbacks()
        
    def projects_by_users (self):
        users = dbBimUsers.query.all()       
        users_project_dict = [{user.name : [project.name for project in user.projects]} for user in users ]
        return dbc.Col(children=[ html.H3("Projets en cours par collaborateurs"),
                        dbc.Row(
                        children=[ 
                                    dbc.Col(children=[
                                                dbc.Card(children=[dbc.CardHeader(name), dbc.CardBody([html.Li(p) for p in projects])]) for name , projects in dict_user.items()]
                                            )
                                        for dict_user in users_project_dict
                        ]
                    )])

    def layout(self):
        """Return User List with Add User Modal"""
        return dbc.Container([
            dbc.Row([
                dbc.Col(html.H1("Collaborateurs", className="mb-4", style={"color": "#2c3e50"}), width=9),
                dbc.Col(dbc.Button("Ajouter un collaborateur", id="open-add-user", color="success",
                                   className="mt-2", n_clicks=0),
                        width=3, className="text-end"),
            ], className="align-items-center mb-4"),

            dbc.Row([
                dbc.Col(dbc.RadioItems(
                    options=[
                        {"label": "Vue Tableau", "value": "Vue Tableau"},
                        {"label": "Vue Carte", "value": "Vue Carte"},
                    ],
                    value="Vue Tableau",
                    id="user-view-type",
                    inline=True
                ), width=12)
            ], className="mb-4"),

            dbc.Row(id="user-list", children=self.get_user_table(), className="g-4"), 
            dbc.Row(id="user-projects-lst", children=self.projects_by_users(), className="g-4"),  

            dbc.Modal([
                dbc.ModalHeader(dbc.ModalTitle("Ajouter un Collaborateur")),
                dbc.ModalBody([
                    dbc.Label("Nom du Collaborateur"),
                    dbc.Input(id="user-name", type="text", placeholder="Entrez le nom du collaborateur"),

                    dbc.Label("Email"),
                    dbc.Input(id="user-email", type="email", placeholder="Email"),

                    dbc.Label("Rôle"),
                    dcc.Dropdown(id="user-role",
                        options=[
                            {"label": "BIM MANAGER", "value": "BIM MANAGER"},
                            {"label": "COORDINATEUR", "value": "COORDINATEUR"},
                        ],
                        placeholder="Sélectionnez un rôle"
                    ),
                ]),
                dbc.ModalFooter([
                    dbc.Button("Annuler", id="close-add-user", className="ml-auto"),
                    dbc.Button("Ajouter", id="submit-add-user", color="primary"),
                ])
            ], id="add-user-modal", is_open=False),
        ], fluid=True, style={"padding": "30px", "background": "#ecf0f1", "min-height": "100vh"})

    def get_user_table(self):
        """Fetch all users and return as a table"""
        with current_app.app_context():
            users = dbBimUsers.query.all()
            return dbc.Table([
                html.Thead(html.Tr([html.Th("Nom"), html.Th("Email"), html.Th("Rôle")])),
                html.Tbody([
                    html.Tr([html.Td(dbc.Button(u.name, href=f"/BIMSYS/bimuser/{u.id}", color="primary", className="mt-2")), html.Td(u.email), html.Td(u.role)]) for u in users
                ])
            ], bordered=True, striped=True, hover=True)

    def get_user_list(self):
        """Fetch all users and return as cards"""
        with current_app.app_context():
            users = dbBimUsers.query.all()
            return [
                dbc.Col(dbc.Card([
                    dbc.CardBody([
                        html.H5(u.name, className="card-title"),
                        html.P(f"Email: {u.email}", className="card-text"),
                        html.P(f"Rôle: {u.role}", className="card-text"),
                    ])
                ], style={"margin-bottom": "20px", "box-shadow": "0px 4px 6px rgba(0, 0, 0, 0.1)"}), width=4)
                for u in users
            ]

    def register_callbacks(self):
        """Register Callbacks for Modal Control and User Addition"""

        @self.app.callback(
            [Output("add-user-modal", "is_open"),
             Output("user-name", "value"),
             Output("user-email", "value"),
             Output("user-role", "value"),
             Output("user-list", "children")],
            [Input("open-add-user", "n_clicks"),
             Input("close-add-user", "n_clicks"),
             Input("submit-add-user", "n_clicks"),
             Input("user-view-type", "value")],
            [State("add-user-modal", "is_open"),
             State("user-name", "value"),
             State("user-email", "value"),
             State("user-role", "value"),
             State("user-view-type", "value")],
            prevent_initial_call=True
        )
        def handle_modal_and_add_user(open_click, close_click, submit_click, user_view_type_click, is_open,
                                      name, email, role, user_view_type):
            """Handle modal open/close, user addition, and view change"""
            ctx = callback_context

            if not ctx.triggered:
                return is_open, no_update, no_update, no_update, no_update

            button_id = ctx.triggered[0]["prop_id"].split(".")[0]

            if button_id == "open-add-user":
                return True, no_update, no_update, no_update, no_update

            if button_id == "close-add-user":
                return False, no_update, no_update, no_update, no_update

            if button_id == "submit-add-user":
                if not all([name, email, role]):
                    return is_open, no_update, no_update, no_update, no_update

                with current_app.app_context():
                    print(name, email, role)
                    new_user = dbBimUsers(
                        name=name,
                        email=email,
                        role=role
                    )
                    db.session.add(new_user)
                    db.session.commit()

                users_display = self.get_user_list() if user_view_type == "Vue Carte" else self.get_user_table()

                return (False, None, None, None, users_display)

            if button_id == "user-view-type":
                print(f"View switched to: {user_view_type_click}")
                users_display = self.get_user_list() if user_view_type_click == "Vue Carte" else self.get_user_table()

                return (False, None, None, None, users_display)
