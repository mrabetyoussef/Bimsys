import dash_bootstrap_components as dbc
from dash import html, dcc, Input, Output, State, callback_context, no_update
from flask import current_app
from database.model import Project
from datetime import datetime, timedelta
import feffery_antd_components as fac
from flask_login import current_user
import dash_bootstrap_components as dbc
from dash import html, dcc
from flask_login import current_user
from database.db import db
from database.model import Project, ProjectPhase, Task, Workload, Phase , BimUsers
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import dash_table
from flask_login import current_user
from database.db import db
from collections import defaultdict
import logging
from datetime import datetime, timedelta
import dash_ag_grid as dag
import calendar
from database.db import db
import pandas as pd
import logging

def iso_week_to_monday(iso_week_str):
        year, week = iso_week_str.split("-W")
        dt = datetime.strptime(f'{year} {week} 1', '%G %V %u')
        return dt

def format_week_header(iso_week_str):
    monday = iso_week_to_monday(iso_week_str)
    iso_year, iso_week = iso_week_str.split("-W")
    return f"{monday.strftime('%d/%m/%Y')}"

class HomePage:
    def __init__(self, app):
        self.app = app  
        self.register_callbacks()


    def layout(self):
        """Return enhanced page layout """

        with current_app.app_context():
            projects = Project.query.all()            
            projects_count = len(projects)
            completed_projects = len([i for i in projects if i.status == "Terminé"])
            active_teams = 5
            today = datetime.now()
            week_later = today + timedelta(days=7)

        return html.Div([
            html.Div([
                dbc.Container([
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
                                        'title': current_user.name,
                                        'href': '/BIMSYS/user',
                                        'target': '_blank',
                                        'icon': 'antd-user',
                                    },
                                ],
                                style={"marginBottom": "16px"}
                            ),
                            html.Div([
                                html.H1("Bienvenue sur BIMSYS", style={
                                    "color": "#1f2937", 
                                    "marginBottom": "8px",
                                    "fontWeight": "700",
                                    "fontSize": "32px"
                                }),
                                html.P("Gérez efficacement vos projets BIM avec des outils de suivi détaillés et des analyses avancées.", style={
                                    "color": "#6b7280",
                                    "fontSize": "16px",
                                    "marginBottom": "0"
                                })
                            ])
                        ], width=12),
                    ])
                ], fluid=True)
            ], style={
                "backgroundColor": "#ffffff",
                "padding": "24px 0",
                "borderBottom": "1px solid #e5e7eb"
            }),

      

            # Charts section
            html.Div([
                dbc.Container([
                    dbc.Row([
                        dbc.Col([
                            self.projects_pie_chart()
                        ], width=12, lg=4),
                        dbc.Col([
                            self.users_chart()
                        ], width=12, lg=8),
                    ], className="g-4")
                ], fluid=True)
            ], style={"padding": "32px 0"}),

            html.Div([
                dbc.Container([
                    dbc.Row([self.project_details()
                    ], className="g-4")
                ], fluid=True)
            ], style={"padding": "32px 0", "backgroundColor": "#f8fafc"}),
        
            # Workload section
            html.Div([
                dbc.Container([
                    dbc.Row([
                        dbc.Col([
                            dbc.Card([
                                dbc.CardBody([
                                    html.Div([
                                        html.H4("Plans de charges de l'équipe", style={
                                            "fontWeight": "600",
                                            "fontSize": "20px",
                                            "color": "#1f2937",
                                            "marginBottom": "8px"
                                        }),
                                        html.P("Suivi détaillé des charges de travail par équipe et par semaine", style={
                                            "color": "#6b7280",
                                            "fontSize": "14px",
                                            "marginBottom": "24px"
                                        })
                                    ]),
                                    self.plan_charge()
                                ])
                            ], className="shadow-sm", style={
                                "border": "1px solid #e5e7eb",
                                "borderRadius": "16px"
                            })
                        ], width=12)
                    ])
                ], fluid=True)
            ], style={"padding": "32px 0", "backgroundColor": "#f8fafc"})
            ,
     

        ], style={"backgroundColor": "#ffffff", "minHeight": "100vh"})


    def project_details(self):
        today = datetime.today()
        end_limit = today + timedelta(days=7)  
        start_of_month = today.replace(day=1)
        last_day = calendar.monthrange(today.year, today.month)[1]
        end_of_month = today.replace(day=last_day)

        # Requête : phases qui se terminent dans le mois courant
        ppf = ProjectPhase.query \
            .filter(ProjectPhase.end_date >= start_of_month) \
            .filter(ProjectPhase.end_date <= end_of_month) \
            .all()

        ProjectPhase.project_parent
        # Liste formatée des projets/phrases
        if not ppf:
            ppf = ProjectPhase.query \
                .filter(ProjectPhase.end_date >= today) \
                .order_by(ProjectPhase.end_date.asc()) \
                .limit(3) \
                .all()

        # Affichage
        if not ppf:
            items = [html.Div("Aucun projet à afficher.", style={"color": "#6b7280"})]
        else:
            items = []
            for phase in ppf:
                items.append(
                    html.Div([
                        html.Span("📌", style={"marginRight": "8px"}),
                        html.Span(f"{phase.project_parent.name} – Phase : {phase.phase.name} – Fin : {phase.end_date.strftime('%d/%m/%Y')}")
                    ], style={"marginBottom": "6px", "fontSize": "14px", "color": "#374151"})
                )

        # Card finale
        return dbc.Card(
            dbc.CardBody([
                html.H5("Projets terminant cette semaine", style={
                    "fontWeight": "600", "fontSize": "16px", "marginBottom": "12px", "color": "#1f2937"
                }),
                *items
            ]),
            className="shadow-sm h-100",
            style={
                "border": "1px solid #e5e7eb",
                "borderRadius": "16px",
                "padding": "16px",
                "backgroundColor": "white"
            }
        )


    def plan_charge(self):
        project_phase_info = pd.read_sql_query(
            """
            SELECT 
                project_phases.id AS project_phase_id,
                project_phases.project_id,
                phases.name AS phase_name,
                projects.name AS project_name,
                BimUsers.name as bim_manager_name

            FROM project_phases
            JOIN phases ON project_phases.phase_id = phases.id
            JOIN projects ON project_phases.project_id = projects.id
            JOIN BimUsers on BimUsers.id = project_phases.assigned_bimuser_id
            """,
            con=db.session.connection()
        )

        workload = pd.read_sql_query("SELECT * FROM workload", con=db.session.connection())
        workload = workload.drop(columns=["actual_days"])

        pivot = workload.pivot_table(
            index='project_phase_id',
            columns='week',
            values='planned_days',
            aggfunc='sum',
            fill_value=0
        ).reset_index()

        merged = pd.merge(project_phase_info, pivot, on="project_phase_id", how="inner")
        merged = merged.sort_values(by=["project_name", "phase_name"])
        merged = merged.drop(columns=["project_id" , "project_phase_id"])

        week_cols = [col for col in merged.columns if col not in ['phase_name', 'project_name', 'bim_manager_name']]
        total_row = merged[week_cols].sum().to_frame().T
        total_row.insert(0, "phase_name", "")
        total_row.insert(0, "project_name", "charges/semaines (j)")
        charge = total_row.copy()
        charge[week_cols] = (charge[week_cols] / 5)*100 / merged["bim_manager_name"].nunique()
        charge["project_name"] = "(% de charge sur affaires)"
        merged = pd.concat([charge ,total_row, merged], ignore_index=True)

        merged[week_cols] = merged[week_cols].round(2)

        
        merged.columns = [
            format_week_header(i) if i not in ['phase_name', 'project_name', 'bim_manager_name'] else i
            for i in merged.columns
        ]

        today = datetime.today()
        iso_year, iso_week, _ = today.isocalendar()
        monday = datetime.strptime(f'{iso_year} {iso_week} 1', '%G %V %u')
        target_column = monday.strftime('%d/%m/%Y')
    
        
        column_defs = [
            {
                "headerName": "Projet",
                "field": "project_name",
                "pinned": "left",
                "cellStyle": {
                    "fontWeight": "600",
                    "whiteSpace": "nowrap",
                    "overflow": "hidden",
                    "textOverflow": "ellipsis",
                    "color": "#1f2937"
                },
                "headerClass": "ag-header-custom",
                "width": 180,
                "maxWidth": 220,
                "tooltipField": "project_name",
            },
            {
                "headerName": "Phase", 
                "field": "phase_name",
                "pinned": "left",
                "width": 140,
                "headerClass": "ag-header-custom",
                "cellStyle": {"fontSize": "13px", "color": "#6b7280", "fontWeight": "500"}
            },
            {
                "headerName": "BIM Manager", 
                "field": "bim_manager_name",
                "pinned": "left",
                "width": 140,
                "headerClass": "ag-header-custom",
                "cellStyle": {"fontSize": "13px", "color": "#6b7280", "fontWeight": "500"}
            }
        ]
        column_defs.extend([{
                "field": x,
                "headerClass": "ag-header-week" + (" ag-header-current" if x == target_column else ""),
                "cellStyle": {
                    "fontWeight": "500",
                    "textAlign": "center",
                    "backgroundColor": "#EEF2FF" if x == target_column else "white",
                    "borderLeft": "2px solid #4F46E5" if x == target_column else "none"
                },
                "cellClassRules": {
                    "cell-green": "params.value < 60 && params.node.data.project_name === '(% de charge sur affaires)'",
                    "cell-orange": "params.value >= 60 && params.value <= 80 && params.node.data.project_name === '(% de charge sur affaires)'",
                    "cell-red": "params.value > 80 && params.node.data.project_name === '(% de charge sur affaires)'"
                }
            }for x in merged.columns if x not in ["project_name" , "phase_name","bim_manager_name"]])
        
        bim_managers = BimUsers.query.all()
        bim_managers = [i.name for i in bim_managers]

        self.initial_dict= merged
        
        layout = html.Div([
            dbc.Row([
                dbc.Col([
                    html.Label("Filtrer par BIM Manager", style={
                        "fontSize": "14px",
                        "fontWeight": "600",
                        "color": "#374151",
                        "marginBottom": "8px"
                    }),
                    dcc.Dropdown(
                        bim_managers,
                        multi=True,
                        clearable=True,
                        id="bimmanager-filter",
                        placeholder="Sélectionner des BIM Managers...",
                        style={"fontSize": "14px"},
                        className="custom-dropdown"
                    )
                ], width=12, lg=6)
            ], className="mb-4"),
            
            html.Div([
                dag.AgGrid(
                    id="project-workload-grid",
                    columnDefs=column_defs,
                    rowData=merged.to_dict("records"),            
                    className="ag-theme-alpine custom-ag-grid",
                    columnSize="autoSize",
                    defaultColDef={
                        "resizable": True,
                        "sortable": True,
                        "filter": True,
                        "minWidth": 80,
                        "wrapText": False,
                        "headerHeight": 50,
                    },
                    dashGridOptions={
                        "domLayout": "normal",
                        "suppressHorizontalScroll": False,
                        "rowHeight": 45,
                        "headerHeight": 50,
                        "animateRows": True,
                        "enableRangeSelection": True,
                    },
                    style={
                        "height": "600px",
                        "overflowX": "auto",
                        "border": "1px solid #e5e7eb",
                        "borderRadius": "12px"
                    }, 
                    scrollTo= {"column": target_column, "columnPosition": "middle"}
                )
            ], style={"position": "relative"}),
  
        ])

        return layout

    def projects_pie_chart(self):
        projects = Project.query.all()
        df = pd.DataFrame([{"Nom": project.name, "Statut": project.status} for project in projects])

        if df.empty:
            return html.Div(
                "Aucun projet à afficher",
                style={
                    "textAlign": "center",
                    "color": "#8e9ba5",
                    "fontSize": "14px",
                    "padding": "40px 20px"
                }
            )

        # Modern color palette
        color_map = {
            "En cours": "#4F46E5",         # Indigo
            "Terminé": "#059669",          # Emerald  
            "Non commencé": "#6B7280",     # Gray
        }

        status_counts = df["Statut"].value_counts().reset_index()
        status_counts.columns = ["Statut", "Nombre"]

        fig = px.pie(
            status_counts,
            values="Nombre",
            names="Statut",
            hole=0.7
        )

        fig.update_traces(
            textinfo="none",
            marker=dict(
                colors=[color_map.get(s, "#CCCCCC") for s in status_counts["Statut"]],
                line=dict(color='rgba(255,255,255,0.8)', width=2)
            ),
            hovertemplate="<b>%{label}</b><br>Projets: %{value}<extra></extra>"
        )

        fig.update_layout(
            showlegend=False,
            margin=dict(l=0, r=0, t=0, b=0),
            height=200,
            width=200,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter, system-ui, sans-serif")
        )

        # Enhanced legend with modern styling
        labels = []
        total = status_counts["Nombre"].sum()
        for _, row in status_counts.iterrows():
            color = color_map.get(row["Statut"], "#CCC")
            percentage = round((row["Nombre"] / total) * 100, 1)
            labels.append(
                html.Div([
                    html.Div(style={
                        "backgroundColor": color,
                        "width": "12px",
                        "height": "12px",
                        "borderRadius": "3px",
                        "marginRight": "12px",
                        "flexShrink": "0"
                    }),
                    html.Div([
                        html.Span(row['Statut'], style={
                            "fontSize": "14px",
                            "fontWeight": "500",
                            "color": "#1f2937"
                        }),
                    
                    ])
                ], style={
                    "display": "flex", 
                    "alignItems": "flex-start", 
                    "marginBottom": "12px",
                    "padding": "8px 0"
                })
            )

        return dbc.Card(
            dbc.CardBody([

                # Titre + flèche
                html.Div([
                    html.H5("Aperçu des Projets", className="mb-0", style={
                        "fontWeight": "600",
                        "fontSize": "18px",
                        "color": "#1f2937"
                    }),
                    html.Span("↗", style={
                        "color": "#9ca3af", "fontSize": "18px", "cursor": "pointer"
                    })
                ], style={
                    "display": "flex",
                    "justifyContent": "space-between",
                    "alignItems": "center",
                    "marginBottom": "16px"
                }),

                dbc.Row([
                    dbc.Col(
                        dcc.Graph(
                            figure=fig,
                            config={
                                "displaylogo": False,
                                "modeBarButtonsToRemove": ["toImage", "pan2d", "select2d", "lasso2d", "resetScale2d"],
                                "displayModeBar": False
                            },
                        ),
                        width=8
                    ),
                    dbc.Col(
                        html.Div(labels, style={"paddingLeft": "12px", "paddingTop": "10px"}),
                        width=4 
                    ),
                ], align="center", className="g-0"),

            ]),
            className="shadow-sm h-100",
            style={
                "border": "1px solid #e5e7eb",
                "borderRadius": "16px",
                "padding": "16px",
                "backgroundColor": "white"
            }
        )


    def users_chart(self):
        project_phase_info = pd.read_sql_query(
            """
            SELECT 
                project_phases.id AS project_phase_id,
                project_phases.project_id,
                phases.name AS phase_name,
                projects.name AS project_name,
                BimUsers.name as bim_manager_name

            FROM project_phases
            JOIN phases ON project_phases.phase_id = phases.id
            JOIN projects ON project_phases.project_id = projects.id
            JOIN BimUsers on BimUsers.id = project_phases.assigned_bimuser_id
            """,
            con=db.session.connection()
        )

        workload = pd.read_sql_query("SELECT * FROM workload", con=db.session.connection())
        workload = workload.drop(columns=["actual_days"])

        pivot = workload.pivot_table(
            index='project_phase_id',
            columns='week',
            values='planned_days',
            aggfunc='sum',
            fill_value=0
        ).reset_index()

        merged = pd.merge(project_phase_info, pivot, on="project_phase_id", how="inner")
        merged = merged.sort_values(by=["project_name", "phase_name"])
        merged = merged.drop(columns=["project_id" , "project_phase_id"])
        
        merged.columns = [
            format_week_header(i) if i not in ['phase_name', 'project_name', 'bim_manager_name'] else i
            for i in merged.columns
        ]

        today = datetime.today()
        iso_year, iso_week, _ = today.isocalendar()
        monday = datetime.strptime(f'{iso_year} {iso_week} 1', '%G %V %u')

        week_columns = []
        for offset in [-2,-1, 0, 1 ,2]:
            week_date = monday + timedelta(weeks=offset)
            week_str = week_date.strftime('%d/%m/%Y')
            week_columns.append(week_str)

        selected_columns = ['project_name', 'phase_name', 'bim_manager_name'] + week_columns
        merged = merged[selected_columns]
        for col in week_columns:
            merged[col] = round((merged[col] / 5) * 100, 1)
            
        weekly_summary = (
            merged
            .groupby('bim_manager_name')[week_columns]
            .sum()
            .reset_index()
        )
        
        df_long = weekly_summary.melt(
            id_vars='bim_manager_name',
            var_name='Semaine',
            value_name='Charge (%)'
        )

        # Modern color palette for lines
        colors = ['#4F46E5', '#059669', '#DC2626', '#7C3AED', '#EA580C', '#0891B2']
        
        fig = px.line(
            df_long,
            x='Semaine',
            y='Charge (%)',
            color='bim_manager_name',
            markers=True,
            line_shape="spline",
            color_discrete_sequence=colors
        )

        fig.update_traces(
            line=dict(width=3),
            marker=dict(size=8, line=dict(width=2, color='white')),
            hovertemplate="<b>%{fullData.name}</b><br>Semaine: %{x}<br>Charge: %{y}%<extra></extra>"
        )

        fig.update_layout(
            legend=dict(
                title="BIM Manager",
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                font=dict(size=12)
            ),
            template="plotly_white",
            height=320,
            margin=dict(l=40, r=40, t=60, b=40),
            font=dict(family="Inter, system-ui, sans-serif"),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(
                showgrid=True,
                gridwidth=1,
                gridcolor='rgba(0,0,0,0.1)',
                title_font_size=12
            ),
            yaxis=dict(
                showgrid=True,
                gridwidth=1,
                gridcolor='rgba(0,0,0,0.1)',
                title_font_size=12
            )
        )

        return dbc.Card([
            dbc.CardBody([
                html.H5("Charge de Travail par BIM Manager", className="mb-3", style={
                    "fontWeight": "600",
                    "fontSize": "18px",
                    "color": "#1f2937"
                }),
                dcc.Graph(
                    figure=fig,
                    config={
                        "displaylogo": False,
                        "modeBarButtonsToRemove": ["toImage"],
                        "displayModeBar": "hover"
                    }
                )
            ])
        ], className="shadow-sm", style={
            "border": "1px solid #e5e7eb",
            "borderRadius": "16px"
        })

    def register_callbacks(self):
        """Enhanced callbacks with better error handling and UX"""
        
        @self.app.callback(
            Output("project-workload-grid", "filterModel"),
            Output("project-workload-grid", "rowData"),

            Input("bimmanager-filter", "value"),
            State("project-workload-grid", "filterModel"),   
            State("project-workload-grid", "rowData"),

            prevent_initial_call=True

            )
        
        def update_filter_model(select_bim_managers, model,data):
            model["bim_manager_name"] = {
                "filterType": "string",
                "operator": "OR",
                "conditions": [
                    {"filterType": "string", "type": "equals", "filter": bim}
                    for bim in select_bim_managers
                ].extend([{"filterType": "string", "type": "equals", "filter": ""}]),
            }
           
            data = self.initial_dict
            if select_bim_managers :
                data = data[data["bim_manager_name"].isin(select_bim_managers)]
                week_cols = [col for col in data.columns if col not in ['phase_name', 'project_name', 'bim_manager_name']]
                total_row = data[week_cols].sum().to_frame().T
                total_row.insert(0, "phase_name", "")
                total_row.insert(0, "project_name", "charges/semaines (j)")
                charge = total_row.copy()
                charge[week_cols] = (charge[week_cols] / 5)*100
                charge["project_name"] = "(% de charge sur affaires)"
                data = pd.concat([charge,total_row, data], ignore_index=True)

            return model , data.to_dict("records")