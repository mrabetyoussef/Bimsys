import dash_bootstrap_components as dbc
from dash import html, dcc
from flask import current_app
from database.model import Project
from datetime import datetime, timedelta
import feffery_antd_components as fac

class HomePage:
   

    def layout(self):
        """Return page layout """

        with current_app.app_context():
            projects = Project.query.all()            
            projects_count = len(projects)
            completed_projects = len([i for i in projects if i.status == "Terminé"])
            active_teams = 5
            today = datetime.now()
            week_later = today + timedelta(days=7)
            projects_ending_in_week = Project.query.filter(Project.end_date < week_later).filter(Project.end_date > today).all()
            projects_ending_lst = [dbc.Accordion(dbc.AccordionItem(title=p.name , children=[html.P(f"Date de fin {p.end_date}")] ),start_collapsed=True)for p in projects_ending_in_week]
        return dbc.Container([
            dbc.Row([
                dbc.Col([
                    
                fac.AntdBreadcrumb(
                    items=[
                        {
                            'title': 'Accueil',
                            'href': '/',
                            'target': '_blank',
                            'icon': 'antd-home',
                        },
                        {
                            'title': 'feffery-antd-components',
                            'href': '/',
                            'target': '_blank',
                            'icon': 'antd-home',
                        },
                     
                    ]
                ),
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
                 

                ], width=4, style={"background": "white", "padding": "30px", "border-radius": "10px"}),

                dbc.Col([
                    html.H4("Statistiques Générales", style={"color": "#2c3e50", "margin-bottom": "20px"}),

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
                                html.H5("Prochainement terminé", className="card-title"),                            
                                dbc.Col(projects_ending_lst)
                            ])
                        ], style={"text-align": "center", "border-radius": "10px",
                                  "box-shadow": "0 4px 6px rgba(0, 0, 0, 0.1)"}), width=4),

                        dbc.Col(dbc.Card([
                            dbc.CardBody([
                                html.H5("Personnes mobilisés", className="card-title"),
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

        ], fluid=True, style={"padding": "30px", "min-height": "100vh"})
