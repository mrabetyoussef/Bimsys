# app/pages/login.py

from dash import html, Input, Output, State, no_update
import dash_bootstrap_components as dbc
from flask_login import login_user , logout_user
from database.model import BimUsers
from flask import redirect


class LoginPage:
    def __init__(self, dash_app):
        self.dash_app = dash_app
        # on construit le layout une fois
        self.ui = dbc.Container([
            dbc.Row([
                dbc.Col([
                    html.H2("Connexion", className="text-center mb-4"),
                    dbc.Card([
                        dbc.CardBody([
                            dbc.Label("Email"),
                            dbc.Input(id="login-email", type="text", placeholder="Entrez votre identifiant", className="mb-3"),
                            
                            dbc.Label("Mot de passe"),
                            dbc.Input(id="login-password", type="password", placeholder="Entrez votre mot de passe", className="mb-3"),
                            
                            dbc.Button("Se connecter", id="login-button", color="primary", className="w-100 mb-2"),
                            html.Div(id="login-message", className="text-danger")
                        ])
                    ], className="shadow p-4")
                ], width=6)
            ], justify="center", align="center", style={"height": "80vh"})
        ], fluid=True)

       
        

        self.register_callbacks()

    def layout(self):
        return self.ui
    
    def register_callbacks(self):
        @self.dash_app.callback(
            Output("login-message", "children"),
            Output("url", "pathname", allow_duplicate=True),
            Input("login-button", "n_clicks"),
            State("login-email", "value"),
            State("login-password", "value"),
            prevent_initial_call=True
        )
        def handle_login(n_clicks, email, password):
            print("logging in ")
            user = BimUsers.query.filter(BimUsers.email == email).first()
            print(user)
            if user and  password:
                login_user(user)
                return "", "/BIMSYS/"  # redirige vers l'accueil
            return "Identifiant ou mot de passe incorrect", no_update
