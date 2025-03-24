import dash_bootstrap_components as dbc
from dash import html
from flask import current_app
from database.model import BimUsers as  dbBimUsers


class BimUser:
    def __init__(self, user_id):
        self.user_id  = user_id

   


    def layout(self):
        """Return a Single user View with Enhanced UI"""
        with current_app.app_context():
            user = dbBimUsers.query.get(self.user_id)

            if user:
                return dbc.Container([
                    dbc.Row([
                        dbc.Col(dbc.Card([
                            dbc.CardHeader(html.H3("Informations")),
                            dbc.CardBody([ 

                                dbc.ListGroupItem( children=dbc.Row([html.Strong("NOM") , html.P(user.name)],align="center")),
                                dbc.ListGroupItem( children=dbc.Row([html.Strong("Email") , html.P(user.email)],align="center")),
                                dbc.ListGroupItem( children=dbc.Row([html.Strong("Fonction") , html.P(user.role)],align="center")),

                                ])
                        ], style={"box-shadow": "0px 4px 6px rgba(0, 0, 0, 0.1)", "margin-bottom": "20px"}), width=6),

                        dbc.Col([
                            dbc.Card([
                                dbc.CardHeader(html.H4("Projets affilé")),
                                dbc.CardBody([
                                    html.P("More details about the user will be added here."),
                                    html.P("This section can include documents, tasks, and updates."),
                                ])
                            ], style={"box-shadow": "0px 4px 6px rgba(0, 0, 0, 0.1)"})
                        ], width=6),
                    ], className="g-4"),

                    dbc.Row([
                        dbc.Col(dbc.Button("Back to users", href="/BIMSYS/users", color="secondary", className="mt-3"), width=12)
                    ], className="text-center"),
                ], fluid=True, style={"padding": "30px", "background": "#ecf0f1", "min-height": "100vh"})

        return dbc.Container([
            dbc.Row([
                dbc.Col(html.H1("user Not Found", style={"color": "red"}), width=12),
            ]),
            dbc.Row([
                dbc.Col(dbc.Button("Back to users", href="/BIMSYS/users", color="secondary", className="mt-3"), width=12, className="text-center"),
            ]),
        ], fluid=True, style={"padding": "30px", "background": "#ecf0f1", "min-height": "100vh"})
