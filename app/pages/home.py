import dash_bootstrap_components as dbc
from dash import html, dcc
from flask import current_app
from database.model import Project


class HomePage:
    def __init__(self):
        pass  

    def layout(self):
        """Return Home Page Layout with Enhanced UI"""

        with current_app.app_context():
            projects = Project.query.all()
            projects_count = len(projects)
            completed_projects = projects_count // 2  
            active_teams = 5

        return dbc.Container([
            dbc.Row([
                dbc.Col([
                    html.H1("Bienvenue sur BIMSYS", style={"color": "#2c3e50", "margin-bottom": "20px"}),
                    
                ], width=12, style={"margin-bottom": "30px"}),
            ]),

            dbc.Row([
                dbc.Col([
                    html.H4("À Propos", style={"color": "#2c3e50"}),
                    html.Hr(),

                    html.P("BIMSYS vous permet de gérer efficacement vos projets BIM avec des outils "
                           "de suivi détaillés et des analyses avancées."),
                    html.H4("Nouveautés", style={"color": "#2c3e50"}),

                    html.Hr(),
                    
                    html.Ul([
                                html.Li("Consultez les projets en cours enregistrés dans la base de données."),
                                html.Li("Ajoutez de nouveaux projets facilement."),
                                html.Li("Visualisez les statistiques de vos équipes."),
                            ]),
                 

                ], width=4, style={"background": "#f8f9fa", "padding": "30px", "border-radius": "10px"}),

                dbc.Col([
                    html.H4("📊 Statistiques Générales", style={"color": "#2c3e50", "margin-bottom": "20px"}),

                    dbc.Row([
                        dbc.Col(dbc.Card([
                            dbc.CardBody([
                                html.H5("Projets en cours", className="card-title"),
                                html.H1(f"{projects_count}", className="card-text", style={"font-weight": "bold"}),
                            ])
                        ], style={"text-align": "center", "border-radius": "10px", 
                                  "box-shadow": "0 4px 6px rgba(0, 0, 0, 0.1)"}), width=4),

                        dbc.Col(dbc.Card([
                            dbc.CardBody([
                                html.H5("Projets terminés", className="card-title"),
                                html.H1(f"{completed_projects}", className="card-text", style={"font-weight": "bold"}),
                            ])
                        ], style={"text-align": "center", "border-radius": "10px",
                                  "box-shadow": "0 4px 6px rgba(0, 0, 0, 0.1)"}), width=4),

                        dbc.Col(dbc.Card([
                            dbc.CardBody([
                                html.H5("Équipes actives", className="card-title"),
                                html.H1(f"{active_teams}", className="card-text", style={"font-weight": "bold"}),
                            ])
                        ], style={"text-align": "center", "border-radius": "10px", 
                                  "box-shadow": "0 4px 6px rgba(0, 0, 0, 0.1)"}), width=4),
                    ], className="g-4", style={"margin-bottom": "30px"}),

                    dbc.Card([
                        dbc.CardBody([
                            html.H5("Répartition des Projets", className="card-title"),
                            dcc.Graph(
                                figure={
                                    "data": [
                                        {"values": [projects_count, completed_projects], 
                                         "labels": ["En cours", "Terminés"], 
                                         "type": "pie", "hole": 0.4,
                                         "marker": {"colors": ["#3498db", "#2ecc71"]},
                                         "hoverinfo": "label+percent"},
                                    ],
                                    "layout": {"showlegend": True, "height": 300}
                                }
                            ),
                        ])
                    ], style={"border-radius": "10px", "box-shadow": "0px 4px 6px rgba(0, 0, 0, 0.1)"}),

                ], width=8, style={"padding": "30px", "border-radius": "10px"}),

            ], className="g-0"),  

        ], fluid=True, style={"padding": "30px", "background": "#ecf0f1", "min-height": "100vh"})
