import dash_bootstrap_components as dbc
from dash import html, dcc, Input, Output, State, callback_context, no_update
from flask import current_app
from database.model import BimUsers as dbBimUsers
from database.db import db


class BimUser:
    def __init__(self, app):
        self.app = app
        self.register_callback()

    def get_projects(self, user):
        return dbc.CardGroup([
            dbc.Col(
                html.A(
                    dbc.Card(
                        dbc.CardBody([html.H5(p.name, className="card-title")]),
                        className="card-hover",
                        style={
                            "margin": "5px",
                            "box-shadow": "0px 4px 6px rgba(0, 0, 0, 0.1)"
                        }
                    ),
                    href=f"/BIMSYS/project/{p.id}",
                    style={"textDecoration": "none", "color": "inherit"}
                ),
                width=4
            )
            for p in (user.projects or [])
        ])

    def layout(self, user_id):
        self.user_id = user_id

        with current_app.app_context():
            user = dbBimUsers.query.get(self.user_id)

            if user:
                return dbc.Container([
                    dbc.Modal(
                        [
                            dbc.ModalHeader(dbc.ModalTitle("Confirmation")),
                            dbc.ModalBody("Vous êtes sûr de vouloir supprimer cet utilisateur ?"),
                            dbc.ModalFooter([
                                dbc.Button("Annuler", id="cancel-delete-user", color="secondary", className="me-2"),
                                dbc.Button("Supprimer", id="confirm-delete-user", color="danger")
                            ])
                        ],
                        id="modal-delete-user",
                        centered=True,
                        is_open=False,
                    ),
                    dcc.Location(id="redirect-1", refresh=True),
                    dbc.Row([
                        dbc.Col(dbc.Card([
                            dbc.CardHeader([
                                html.H3("Informations utilisateur"),
                                dbc.Button(html.I(className="fa fa-trash"), color="outline-danger", id="delete-user-button", className="float-end")
                            ]),
                            dbc.CardBody([

                                dbc.Label("Nom"),
                                dbc.Input(type="text", value=user.name, disabled=True, className="mb-3"),

                                dbc.Label("Email"),
                                dbc.Input(type="email", value=user.email, disabled=True, className="mb-3"),

                                dbc.Label("Rôle"),
                                dbc.Input(type="text", value=user.role, disabled=True, className="mb-3"),

                                dbc.Label("Nombre de projets assignés"),
                                dbc.Input(type="number", value=len(user.projects), disabled=True, className="mb-3"),
                                
                                dbc.Label("Taj (valeur modifiable)"),
                                dbc.Input(id="input-user-taj", type="number", value=user.taj, className="mb-3"),

                            ])
                        ], style={"box-shadow": "0px 4px 6px rgba(0, 0, 0, 0.1)", "margin-bottom": "20px"}), width=6),

                        dbc.Col([
                            dbc.Card([
                                dbc.CardHeader(html.H4("Projets affiliés")),
                                dbc.CardBody([self.get_projects(user)])
                            ], style={"box-shadow": "0px 4px 6px rgba(0, 0, 0, 0.1)"})
                        ], width=6),
                    ], className="g-4"),

                    dbc.Row([
                        dbc.Col(dbc.Button("Retour aux utilisateurs", href="/BIMSYS/users", color="secondary", className="mt-3"), width=12)
                    ], className="text-center"),
                ], fluid=True, style={"padding": "30px", "min-height": "100vh"})

        return dbc.Container([
            dbc.Row([
                dbc.Col(html.H1("Utilisateur introuvable", style={"color": "red"}), width=12),
            ]),
            dbc.Row([
                dbc.Col(dbc.Button("Retour aux utilisateurs", href="/BIMSYS/users", color="secondary", className="mt-3"), width=12, className="text-center"),
            ]),
        ], fluid=True, style={"padding": "30px", "background": "white", "min-height": "100vh"})

    def register_callback(self):
        @self.app.callback(
            Output("modal-delete-user", "is_open"),
            Output("redirect-1", "pathname"),
            Input("delete-user-button", "n_clicks"),
            Input("confirm-delete-user", "n_clicks"),
            Input("cancel-delete-user", "n_clicks"),
            State("modal-delete-user", "is_open"),
            prevent_initial_call=True,
        )
        def delete_user(n_clicks_delete, n_clicks_confirm, n_clicks_cancel, is_open):
            ctx = callback_context.triggered_id

            if ctx == "delete-user-button":
                return True, no_update

            elif ctx == "cancel-delete-user":
                return False, no_update

            elif ctx == "confirm-delete-user" and self.user_id:
                with current_app.app_context():
                    user = dbBimUsers.query.get(self.user_id)
                    if user:
                        db.session.delete(user)
                        db.session.commit()
                        return False, "/BIMSYS/collaborateurs"

            return is_open, no_update

        @self.app.callback(
        Output("input-user-taj", "value"),
        Input("input-user-taj", "value"),
        prevent_initial_call=True
    )
        def auto_save_taj(new_taj):
            if new_taj is None or self.user_id  is None:
                return no_update

            with current_app.app_context():
                user = dbBimUsers.query.get(self.user_id )
                if user:
                    user.taj = new_taj
                    db.session.commit()
            return new_taj
