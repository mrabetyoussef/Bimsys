import dash_bootstrap_components as dbc
from dash import html, dcc, Input, Output, State, callback_context, no_update
from flask import current_app
from database.db import db
from database.model import BimUsers as dbBimUsers
from datetime import datetime
import pandas as pd
from dash import dcc
from dash import callback, Output, Input, ctx, dcc, MATCH , ALL
import pdb
from mailjet_rest import Client


class BimUsers:
    def __init__(self, app):
        """Initialize Users Page and Register Callbacks"""
        self.app = app
        self.register_callbacks()
        self.view_type = "Vue Carte"
        
    def projects_by_users(self):
        users = dbBimUsers.query.all()
        users_project_dict = [{user.name: [project.name for project in user.projects]} for user in users]

        return dbc.Container([
            html.H3("Projets en cours par collaborateurs", className="my-4 text-primary"),

            dbc.Row([
                dbc.Col(
                    dbc.Card([
                        dbc.CardHeader(html.H5(user_name, className="mb-0")),
                        dbc.CardBody([
                            html.Ul([html.Li(project, className="mb-1") for project in projects])
                        ])
                    ],
                    className="shadow-sm border-0 h-100"),
                    xs=12, sm=6, md=4, lg=3, className="mb-4"
                )
                for user_dict in users_project_dict
                for user_name, projects in user_dict.items()
            ])
        ], fluid=True)


    def layout(self):
        """Return User List with Add User Modal"""
            

        if self.view_type == "Vue Carte":
            users_list = self.get_user_list()
        else :
            users_list = self.get_user_table()
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
                    value= self.view_type,
                    id="user-view-type",
                    inline=True
                ), width=12)
            ], className="mb-4"),

            dbc.Row(id="user-list", children=users_list, className="g-4"), 
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
        ], fluid=True, style={"padding": "30px", "min-height": "100vh"})



    def get_user_table(self):
        """Fetch all users and return a styled, modern table with visually clickable rows"""
        with current_app.app_context():
            users = dbBimUsers.query.all()

            table_rows = []
            for user in users:
                table_rows.append(
                    (html.Tr(
                        [
                            html.Td(user.name, className="fw-bold"),
                            html.Td(user.email, className="text-muted"),
                            html.Td(dbc.Badge(user.role.capitalize(), color="info", className="px-2 py-1")),
                            html.Td(
                                dbc.Button(
                                    html.I(className="fas fa-arrow-right"),  # Font Awesome arrow icon
                                    href=f"/BIMSYS/bimuser/{user.id}",  # Navigation link
                                    color="link",  # or another style (e.g., "primary")
                                    style={"textDecoration": "none"}
                                ),
                            className="text-end"
                ),

                        ],
                        style={"cursor": "pointer"},

                    ))
                )

            return dbc.Card([
                dbc.CardHeader(html.H4("Utilisateurs BIM", className="mb-0 text-primary")),
                dbc.CardBody([
                    dbc.Table([
                        html.Thead(
                            html.Tr([
                                html.Th("Nom"),
                                html.Th("Email"),
                                html.Th("Rôle"),
                                html.Th("")
                            ])
                        ),
                        html.Tbody(table_rows)
                    ],
                    bordered=False, striped=True, hover=True, responsive=True, className="align-middle mb-0")
                ])
            ], className="shadow-sm border-0 mb-4")





    def get_user_list(self):
        """Fetch all users and return as cards"""
        with current_app.app_context():
            users = dbBimUsers.query.all()
            return [
                dbc.Col(
                    html.A(
                        dbc.Card(
                            dbc.CardBody([
                                html.H5(u.name, className="card-title"),
                                html.P(f"Email: {u.email}", className="card-text"),
                                html.P(f"Rôle: {u.role}", className="card-text"),
                            ]),
                            className="card-hover", 
                            style={
                                "margin-bottom": "20px",
                                "box-shadow": "0px 4px 6px rgba(0, 0, 0, 0.1)"
                            }
                        ),
                        href=f"/BIMSYS/bimuser/{u.id}",
                        style={"textDecoration": "none", "color": "inherit"}
                    ),
                    width=4
                )
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
                    new_user = dbBimUsers(
                        name=name,
                        email=email,
                        role=role
                    )
                    db.session.add(new_user)
                    db.session.commit()
                    self.notify_subscription(name , email, new_user.password)
                users_display = self.get_user_list() if user_view_type == "Vue Carte" else self.get_user_table()

                return (False, None, None, None, users_display)

            if button_id == "user-view-type":
                self.view_type = user_view_type_click
                users_display = self.get_user_list() if user_view_type_click == "Vue Carte" else self.get_user_table()

                return (False, None, None, None, users_display)

        @self.app.callback(
            Output("url", "pathname"),
            Input({"type": "user-card", "index": ALL}, "n_clicks"),
            prevent_initial_call=True
        )
        def navigate_on_card_click(n_clicks_list):
            triggered = ctx.triggered_id
            if triggered and "index" in triggered:
                return f"/BIMSYS/bimuser/{triggered['index']}"
            return dash.no_update
    


    def notify_subscription(self, name, email, password):
        mailjet = Client(
            auth=("1855d6eacbcc8dc12442521492fb8d76", "7afee7a226886cb7362f7102e7e151f5"),  # ou via os.environ
            version='v3.1'
        )

        data = {
                        'Messages': [
                            {
                                "From": {
                                    "Email": "mrabetyoussef95@gmail.com",
                                    "Name": "BIMSYS"
                                },
                                "To": [
                                    {
                                        "Email": email,
                                        "Name": name
                                    }
                                ],
                                "Subject": "Vos identifiants BIMSYS",
                                "TextPart": f"""
                Bonjour {name},

                Un compte vient d’être créé pour vous sur la plateforme BIMSYS.

                Identifiants :
                Email : {email}
                Mot de passe : {password}

                Connectez-vous ici : https://ton-domaine/BIMSYS/login

                Merci.
                                """,
                                "HTMLPart": f"""
                <h3>Bonjour {name},</h3>
                <p>Un compte vient d’être créé pour vous sur la plateforme <strong>BIMSYS</strong>.</p>
                <p><b>Identifiants :</b><br>Email : {email}<br>Mot de passe : {password}</p>
                <p>➡️ <a href="https://ton-domaine/BIMSYS/login">Cliquez ici pour vous connecter</a></p>
                <p style="color:#888">Merci,<br>L’équipe BIMSYS</p>
                """
                            }
                        ]
                    }

        result = mailjet.send.create(data=data)
        print("Status:", result.status_code)
        print("Response:", result.json())
