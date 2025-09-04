import dash_bootstrap_components as dbc
from dash import html, dcc
from flask_login import current_user
from database.db import db
from database.model import Project, ProjectPhase, Task, Workload, Phase , DailyWorkload ,RealWorkload
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import dash_table
from flask_login import current_user
from database.db import db
from collections import defaultdict
import logging
from datetime import datetime, timedelta
from dash import html, dcc
import dash_bootstrap_components as dbc
import dash_ag_grid as dag
import full_calendar_component as fcc
import dash_mantine_components as dmc
from dash import html, dcc, Input, Output, State, callback_context, no_update 
import dash
import shortuuid
import plotly.graph_objs as go



class UserPage:
    def __init__(self, app):
        self.app = app
        self.register_callbacks()

    def layout(self):
        user = current_user
        user_id = user.id

        # --- DATA EXTRACTION ---
        managed_projects = [pp.project_parent for pp in db.session.query(ProjectPhase).filter_by(assigned_bimuser_id=user_id).all()]
        phases = db.session.query(ProjectPhase).filter_by(assigned_bimuser_id=user_id).all()
        tasks = db.session.query(Task).filter_by(assigned_to=user_id).all()
        all_projects = list({p.project_parent for p in phases} | set(managed_projects))

        tasks_done = [t for t in tasks if t.status == "Terminé"]
        tasks_progress = [t for t in tasks if t.status != "Terminé"]
        tasks_urgent = [t for t in tasks_progress if self.is_urgent(t)]

        return html.Div([

            self.render_user_header(user),
            dbc.Row(id="workload_comparaison" ,  children=  self.workload_comparaison()),
            dbc.Row(  children=              self.real_workload(), style={"margin-top" : "20px","margin-bottom" : "20px"}),


            self.render_kpi_section(all_projects, phases, tasks, tasks_done, tasks_progress, tasks_urgent),
            
            # Section graphiques
            self.render_charts_section(tasks, all_projects),
            
            # Section détails des projets
            self.render_projects_section(all_projects, user_id),
            
            # Section plan de charge
            self.user_workload_layout_aggrid(user_id)
            
        ], className="user-dashboard")
    
    def workload_comparaison(self, hours_per_day=8):

        def iso_week_str(dt) -> str:
            y, w, _ = dt.isocalendar()
            return f"{y}-W{w:02d}"

        def week_to_monday_date(week_iso: str):
            year, week = week_iso.split("-W")
            return datetime.strptime(f"{year} {week} 1", "%G %V %u").date()

        q_daily = DailyWorkload.query.filter(DailyWorkload.user_id == current_user.id)
        daily = q_daily.all()

        rows_actual = []
        for d in daily:
            rows_actual.append({
                "bimuser_id": d.user_id,                               
                "week": iso_week_str(d.date),
                "actual_days": float(d.hours or 0.0) / float(hours_per_day)
            })

        df_actual = pd.DataFrame(rows_actual)
        if df_actual.empty:
            df_actual_weekly = pd.DataFrame(columns=["bimuser_id", "week", "actual_days"])
        else:
            df_actual_weekly = (
                df_actual.groupby(["bimuser_id", "week"], as_index=False)
                        .agg(actual_days=("actual_days", "sum"))
            )

        workloads = Workload.query.filter(Workload.bimuser_id == current_user.id).all()
        rows_forecast = []
        for w in workloads:
            rows_forecast.append({
                "bimuser_id": w.bimuser_id,
                "week": w.week,                   
                "planned_days": float(w.planned_days or 0.0)
            })

        df_forecast = pd.DataFrame(rows_forecast)
        if df_forecast.empty:
            df_forecast_weekly = pd.DataFrame(columns=["bimuser_id", "week", "planned_days"])
        else:
            df_forecast_weekly = (
                df_forecast.groupby(["bimuser_id", "week"], as_index=False)
                        .agg(planned_days=("planned_days", "sum"))
            )

        df = pd.merge(
            df_forecast_weekly,
            df_actual_weekly,
            on=["bimuser_id", "week"],
            how="outer"
        ).fillna(0.0)

        if not df.empty:
            df["_monday"] = df["week"].apply(week_to_monday_date)
            df = df.sort_values(["_monday"]).drop(columns="_monday")

        
        if not df.empty:
            df["delta_days"] = df["actual_days"] - df["planned_days"]

       
    

        return dbc.Card([
            dbc.CardBody([
                html.H5("Charge Prévu Vs réelle", className="mb-3", style={
                    "fontWeight": "600",
                    "fontSize": "18px",
                    "color": "#1f2937"
                }),
                dcc.Graph(id="forecast-vs-actual-graph", figure=self.plot_forecast_vs_actual_line(df))
            ])
        ], className="shadow-sm", style={
            "border": "1px solid #e5e7eb",
            "borderRadius": "16px"
        })


    def plot_forecast_vs_actual_line(self,df):
        # df contient : week, planned_days, actual_days

        # Transformation en format long
        df_long = df.melt(
            id_vars=["week"],
            value_vars=["planned_days", "actual_days"],
            var_name="Type",
            value_name="Jours"
        )

        # Renommer pour lisibilité
        df_long["Type"] = df_long["Type"].map({
            "planned_days": "Prévu",
            "actual_days": "Réel"
        })

        # Couleurs personnalisées
        colors = ["steelblue", "seagreen"]

        fig = px.line(
            df_long,
            x="week",
            y="Jours",
            color="Type",
            markers=True,
            line_shape="spline",
            color_discrete_sequence=colors
        )

        fig.update_traces(
            line=dict(width=3),
            marker=dict(size=8, line=dict(width=2, color="white")),
            hovertemplate="<b>%{fullData.name}</b><br>Semaine: %{x}<br>Jours: %{y:.2f}<extra></extra>"
        )

        fig.update_layout(
            legend=dict(
                title="",
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
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(
                showgrid=True,
                gridwidth=1,
                gridcolor="rgba(0,0,0,0.1)",
                title_font_size=12
            ),
            yaxis=dict(
                showgrid=True,
                gridwidth=1,
                gridcolor="rgba(0,0,0,0.1)",
                title_font_size=12
            )
        )

        return fig

        


    def real_workload(self):
        projects = Project.query.all()
        events = DailyWorkload.query.filter(DailyWorkload.user_id == current_user.id).all()
      
        events  = [{
                "id":event.id,
               "start": datetime.combine(event.date, event.start_time),
                  "end": datetime.combine(event.date, event.end_time),
                "title": f"{event.project.name} - {event.phase.phase.name}",
                "extendedProps": {
                    "project_name":event. project.name,
                    "phase_name": event.phase.phase.name,
                }
            }for event in events]
        formatted_date = datetime.now().date().isoformat()
        component =  html.Div(
            [
                fcc.FullCalendarComponent(
                    id="calendar",  # Unique ID for the component
                    initialView="timeGridWeek",  # dayGridMonth, timeGridWeek, timeGridDay, listWeek,
                    # dayGridWeek, dayGridYear, multiMonthYear, resourceTimeline, resourceTimeGridDay, resourceTimeLineWeek
                    headerToolbar={
                        "left": "prev,next today",
                        "center": "",
                        "right": "listWeek,timeGridDay,timeGridWeek,dayGridMonth",
                    },  # Calendar header
                    initialDate=f"{formatted_date}",  # Start date for calendar
                    editable=True,  # Allow events to be edited
                    selectable=True,  # Allow dates to be selected
                    events=events,
                    nowIndicator=True,  # Show current time indicator
                    navLinks=True,  # Allow navigation to other dates
                ),
                dmc.MantineProvider(
                    theme={"colorScheme": "dark"},
                    children=[
                    dmc.Modal(
                        id="modal",
                        size="xl",
                        title="Event Details",
                        zIndex=10000,
                        centered=True,
                        children=[
                            html.Div(id="modal_event_display_context"),
                            dmc.Space(h=20),
                            dmc.Group(
                                [
                                    dmc.Button(
                                        "Delete",
                                        id="modal-delete-button",
                                        color="red",
                                    ),
                                    dmc.Button(
                                        "Close",
                                        id="modal-close-button",
                                        color="gray",
                                        variant="outline",
                                    ),
                                ],
                                align="right",
                            ),
                        ],
                    ),
                    ],
                ),
                dmc.MantineProvider(
                    theme={"colorScheme": "dark"},
                    children=[
                        dcc.Store(id="selected-event-id", data=None),

                        dmc.Modal(
                            id="add_modal",
                            title="New Event",
                            size="xl",
                            centered=True,
                            children=[
                                dmc.Grid(
                                    children=[
                                        dmc.GridCol(
                                            html.Div(
                                                dmc.DatePickerInput(
                                                    id="start_date",
                                                    label="Start Date",
                                                    value=datetime.now().date(),
                                                    styles={"width": "100%"},
                                                    disabled=True,
                                                ),
                                                style={"width": "100%"},
                                            ),
                                            span=6,
                                        ),
                                        dmc.GridCol(
                                           html.Div(
                                            dmc.Select(
                                                label="Start Time",
                                                id="start_time",
                                                data=[
                                                    {"label": f"{h:02d}:{m:02d}", "value": f"{h:02d}:{m:02d}"}
                                                    for h in range(0, 24)
                                                    for m in (0, 30)  # 30 min increments; you can change to (0, 15, 30, 45)
                                                ],
                                                value=datetime.now().strftime("%H:%M"),  # default = current time
                                                searchable=True,
                                                style={"width": "100%"},
                                            )
                                        ),
                                            span=6,
                                        ),
                                    ],
                                    gutter="xl",
                                ),
                                dmc.Grid(
                                    children=[
                                        dmc.GridCol(
                                            html.Div(
                                                dmc.DatePickerInput(
                                                    id="end_date",
                                                    label="End Date",
                                                    value=datetime.now().date(),
                                                    styles={"width": "100%"},
                                                ),
                                                style={"width": "100%"},
                                            ),
                                            span=6,
                                        ),
                                        dmc.GridCol(
                                            html.Div(
                                            dmc.Select(
                                                label="end Time",
                                                id="end_time",
                                                data=[
                                                    {"label": f"{h:02d}:{m:02d}", "value": f"{h:02d}:{m:02d}"}
                                                    for h in range(0, 24)
                                                    for m in (0, 30)  # 30 min increments; you can change to (0, 15, 30, 45)
                                                ],
                                                value=datetime.now().strftime("%H:%M"),  # default = current time
                                                searchable=True,
                                                style={"width": "100%"},
                                            )
                                        ),
                                            span=6,
                                        ),
                                    ],
                                    gutter="xl",
                                ),
                            dbc.Label("Projet", className="fw-semibold mb-2"),
                            dbc.Select(
                                options=[
                                    {"label": project.name , "value":project.id } for project in projects
                                ],
                                id="input-project-name",
                                style={"border-radius": "8px"}
                            ),
                            dbc.Label("Phase de projet", className="fw-semibold mb-2"),

                            dbc.Select(
                                options=[
                                ],
                                id="input-project-phase",
                                style={"border-radius": "8px"}
                            ),
                         
                                dmc.Space(h=20),
                                dmc.Group(
                                    [
                                        dmc.Button(
                                            "Submit",
                                            id="modal_submit_new_event_button",
                                            color="green",
                                        ),
                                        dmc.Button(
                                            "Close",
                                            color="red",
                                            variant="outline",
                                            id="modal_close_new_event_button",
                                        ),
                                    ],
                                    align="right",
                                ),
                            ],
                        ),
                    ],
                ),
            ],
        )
        return dbc.Card([
            dbc.CardBody([
                html.H5("Heures passées", className="mb-3", style={
                    "fontWeight": "600",
                    "fontSize": "18px",
                    "color": "#1f2937"
                }),
                component
            ])
        ], className="shadow-sm", style={
            "border": "1px solid #e5e7eb",
            "borderRadius": "16px"
        })


    def render_user_header(self, user):
        """Render le header avec les informations utilisateur"""
        return dbc.Container([
            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.Div([
                            html.I(className="fas fa-user-circle fa-3x text-primary mb-2"),
                            html.H2(f"{user.name}", className="mb-1 fw-bold text-dark"),
                            html.P(f"{user.email}", className="text-muted mb-1"),
                            dbc.Badge(user.role, color="primary", className="fs-6")
                        ], className="text-center text-md-start")
                    ], className="d-flex align-items-center")
                ], md=8),
                dbc.Col([
                    html.Div([
                        html.Small("Dernière connexion", className="text-muted d-block"),
                        html.Strong(datetime.now().strftime("%d/%m/%Y à %H:%M"), className="text-dark")
                    ], className="text-end d-none d-md-block")
                ], md=4)
            ], className="align-items-center")
        ], fluid=True, className="bg-light py-4 mb-4 rounded-3 shadow-sm")

    def render_kpi_section(self, all_projects, phases, tasks, tasks_done, tasks_progress, tasks_urgent):
        """Render la section des KPI avec un design moderne"""
        kpi_data = [
            ("Projets actifs", len(all_projects), "fas fa-project-diagram", "primary", "Projets en cours de gestion"),
            ("Phases assignées", len(phases), "fas fa-tasks", "info", "Phases dont vous êtes responsable"),
            ("Tâches totales", len(tasks), "fas fa-list-check", "secondary", "Toutes vos tâches"),
            ("Tâches terminées", len(tasks_done), "fas fa-check-circle", "success", f"{self.get_completion_rate(tasks_done, tasks)}% complété"),
            ("Tâches en cours", len(tasks_progress), "fas fa-clock", "warning", "Tâches à finaliser"),
            ("Tâches urgentes", len(tasks_urgent), "fas fa-exclamation-triangle", "danger", "Nécessitent une attention immédiate")
        ]

        kpi_cards = dbc.Row([
            self.create_modern_kpi_card(title, value, icon, color, subtitle)
            for title, value, icon, color, subtitle in kpi_data
        ], className="g-4 mb-5")


        
        return dbc.Container([
            html.H5(["Vue générale"  ], className="mb-4 text-dark fw-bold"),
            kpi_cards
        ], fluid=True)

    def create_modern_kpi_card(self, title, value, icon, color, subtitle):
        """Créer une carte KPI moderne"""
        return dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.Div([
                            html.I(className=f"{icon} fa-2x text-{color} mb-2"),
                            html.H4(str(value), className="fw-bold text-dark mb-1"),
                            html.P(title, className="text-muted mb-1 fw-semibold"),
                            html.Small(subtitle, className="text-muted")
                        ], className="text-center")
                    ])
                ])
            ], className="h-100 shadow-sm border-0 hover-shadow")
        ], lg=2, md=4, sm=6, className="mb-3")

    def render_charts_section(self, tasks, all_projects):
        """Render la section des graphiques avec un design amélioré"""
        return dbc.Container([
            html.H5([
                "Analyses visuelles"
            ], className="mb-4 text-dark fw-bold"),
            
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader([
                            html.H5([
                                html.I(className="fas fa-pie-chart me-2"),
                                "Répartition des tâches"
                            ], className="mb-0 text-dark")
                        ]),
                        dbc.CardBody([
                            dcc.Graph(
                                figure=self.create_modern_pie_chart(tasks),
                                config={'displayModeBar': False}
                            )
                        ])
                    ], className="shadow-sm border-0 h-100")
                ], md=6),
                
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader([
                            html.H5([
                                html.I(className="fas fa-bar-chart me-2"),
                                "Projets par statut"
                            ], className="mb-0 text-dark")
                        ]),
                        dbc.CardBody([
                            dcc.Graph(
                                figure=self.create_modern_bar_chart(all_projects),
                                config={'displayModeBar': False}
                            )
                        ])
                    ], className="shadow-sm border-0 h-100")
                ], md=6)
            ], className="g-4 mb-5")
        ], fluid=True)

    def render_projects_section(self, all_projects, user_id):
        """Render la section des détails des projets"""
        if not all_projects:
            return self.render_empty_state(
                "fas fa-project-diagram",
                "Aucun projet assigné",
                "Vous n'avez actuellement aucun projet assigné."
            )

        return dbc.Container([
            html.H3([
                html.I(className="fas fa-folder-open me-2"),
                "Détail des projets et missions"
            ], className="mb-4 text-dark fw-bold"),
            
            html.Div([
                self.create_project_card(project, user_id)
                for project in all_projects
            ])
        ], fluid=True, className="mb-5")

    def create_project_card(self, project, user_id):
        """Créer une carte projet moderne"""
        project_phases = [p for p in project.phases if p.assigned_bimuser_id == user_id]
        
        if not project_phases:
            return html.Div()

        # Calculer les statistiques du projet
        total_tasks = sum(len(phase.tasks) for phase in project_phases)
        completed_tasks = sum(len([t for t in phase.tasks if t.status == "Terminé"]) for phase in project_phases)
        progress = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

        return dbc.Card([
            dbc.CardHeader([
                dbc.Row([
                    dbc.Col([
                        html.A([
                            html.I(className="fas fa-project-diagram me-2"),
                            project.name,
                            
                        ], href=f'project/{project.id}', className="mb-0 text-dark")
                    ], md=8),
                    dbc.Col([
                        dbc.Badge(project.status, color=self.get_status_color(project.status), className="fs-6")
                    ], md=4, className="text-end")
                ])
            ]),
            dbc.CardBody([
                # Barre de progression
                html.Div([
                    html.Small(f"Progression: {progress:.1f}%", className="text-muted"),
                    dbc.Progress(value=progress, color="success", className="mb-3")
                ]),
                
                # Accordion pour les phases
                dbc.Accordion([
                    self.create_phase_accordion_item(phase)
                    for phase in project_phases
                ], flush=True, start_collapsed=True)
            ])
        ], className="shadow-sm border-0 mb-4")

    def create_phase_accordion_item(self, phase):
        """Créer un item d'accordion pour une phase"""
        tasks = phase.tasks
        completed_tasks = [t for t in tasks if t.status == "Terminé" or t.status == "terminé"]
        phase_progress = (len(completed_tasks) / len(tasks) * 100) if tasks else 0

        return dbc.AccordionItem([
            html.Div([
                # Informations de la phase
                dbc.Row([
                    dbc.Col([
                        html.P([
                            html.I(className="fas fa-calendar-alt me-2"),
                            f"Budget: {phase.days_budget} jours"
                        ], className="mb-2"),
                        html.P([
                            html.I(className="fas fa-euro-sign me-2"),
                            f"Budget: {phase.euros_budget}€"
                        ], className="mb-2")
                    ], md=6),
                    dbc.Col([
                        html.P([
                            html.I(className="fas fa-tasks me-2"),
                            f"{len(tasks)} tâches ({len(completed_tasks)} terminées)"
                        ], className="mb-2"),
                        dbc.Progress(value=phase_progress, color="info", className="mb-2")
                    ], md=6)
                ]),
                
                # Liste des tâches
                html.Hr(),
                html.H6("Tâches assignées:", className="fw-bold mb-3"),
                
                html.Div([
                    self.create_task_item(task) for task in tasks
                ]) if tasks else html.P("Aucune tâche assignée.", className="text-muted")
            ])
        ], title=html.A([f"{phase.phase.name}  ({phase_progress:.1f}%)"],href=f"phase/{phase.id}"))

    def create_task_item(self, task):
        """Créer un item de tâche"""
        status_colors = {
            "Terminé": "success",
            "En cours": "warning",
            "À faire": "secondary",
            "En retard": "danger"
        }
        
        return dbc.Card([
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.H6(task.name, className="mb-1"),
                        html.Small(f"Échéance: {task.due_date}", className="text-muted")
                    ], md=8),
                    dbc.Col([
                        dbc.Badge(
                            task.status,
                            color=status_colors.get(task.status, "secondary"),
                            className="fs-6"
                        )
                    ], md=4, className="text-end")
                ])
            ])
        ], className="mb-2 border-start border-4 border-primary")

    def render_workload_section(self, user_id):
        """Render la section du plan de charge"""
        return dbc.Container([
            html.H3([
                html.I(className="fas fa-calendar-week me-2"),
                "Mon Plan de Charge"
            ], className="mb-4 text-dark fw-bold"),
            
            dbc.Card([
                dbc.CardBody([
                    html.Div(self.user_workload_layout(user_id))
                ])
            ], className="shadow-sm border-0")
        ], fluid=True, className="mb-5")

    def render_empty_state(self, icon, title, description):
        """Render un état vide avec un design moderne"""
        return dbc.Container([
            html.Div([
                html.I(className=f"{icon} fa-4x text-muted mb-3"),
                html.H4(title, className="text-muted mb-2"),
                html.P(description, className="text-muted")
            ], className="text-center py-5")
        ], fluid=True)

    def create_modern_pie_chart(self, tasks):
        """Créer un graphique en secteurs moderne"""
        if not tasks:
            return go.Figure().add_annotation(
                text="Aucune tâche disponible",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )

        status_counts = pd.Series([t.status for t in tasks]).value_counts()
        
        colors = {
            'Terminé': '#28a745',
            'En cours': '#ffc107',
            'À faire': '#6c757d',
            'En retard': '#dc3545'
        }
        
        fig = go.Figure(data=[go.Pie(
            labels=status_counts.index,
            values=status_counts.values,
            hole=0.4,
            marker=dict(colors=[colors.get(label, '#007bff') for label in status_counts.index])
        )])
        
        fig.update_layout(
            showlegend=True,
            margin=dict(t=20, b=20, l=20, r=20),
            font=dict(size=12),
            height=350
        )
        
        return fig

    def create_modern_bar_chart(self, projects):
        """Créer un graphique en barres moderne"""
        if not projects:
            return go.Figure().add_annotation(
                text="Aucun projet disponible",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )

        df = pd.DataFrame([{"Nom": p.name, "Statut": p.status} for p in projects])
        status_counts = df['Statut'].value_counts()
        
        colors = {
            'Actif': '#28a745',
            'En cours': '#007bff',
            'Terminé': '#6c757d',
            'Suspendu': '#ffc107',
            'Annulé': '#dc3545'
        }
        
        fig = go.Figure(data=[
            go.Bar(
                x=status_counts.index,
                y=status_counts.values,
                marker_color=[colors.get(status, '#007bff') for status in status_counts.index]
            )
        ])
        
        fig.update_layout(
            xaxis_title="Statut",
            yaxis_title="Nombre de projets",
            margin=dict(t=20, b=40, l=40, r=20),
            height=350
        )
        
        return fig


    def user_workload_layout(self, user_id=None):
        """Layout du plan de charge avec un design amélioré"""
        def iso_week_to_monday(iso_week_str):
            year, week = iso_week_str.split("-W")
            return datetime.strptime(f'{year} {week} 1', '%G %V %u').date()

        user_id = user_id or current_user.id

        entries = (
            db.session.query(Workload)
            .filter(Workload.bimuser_id == user_id)
            .join(ProjectPhase)
            .join(Project)
            .join(Phase)
            .order_by(Workload.week)
            .all()
        )

        if not entries:
            return self.render_empty_state(
                "fas fa-calendar-times",
                "Aucune donnée de plan de charge",
                "Aucune donnée de plan de charge disponible pour le moment."
            )

        pivot_data = defaultdict(lambda: defaultdict(float))
        all_weeks = set()

        for entry in entries:
            key = (entry.project_phase.project_parent.name, entry.project_phase.phase.name)
            pivot_data[key][entry.week] += entry.planned_days or 0
            all_weeks.add(entry.week)

        sorted_weeks = sorted(all_weeks)

        # Mapping des semaines ISO vers les lundis correspondants
        week_labels = {week: iso_week_to_monday(week).isoformat() for week in sorted_weeks}

        # Calcul des totaux
        total_row = {"Projet": "📊 Total", "Phase": ""}
        charge_row = {"Projet": "⚡ Taux de charge (%)", "Phase": ""}
        
        for week in sorted_weeks:
            total_days = sum(week_data.get(week, 0) for week_data in pivot_data.values())
            label = week_labels[week]
            total_row[label] = round(total_days, 2)
            charge_row[label] = round((total_days / 7.8) * 100, 1)

        table_data = [charge_row, total_row]

        # Ajout des lignes par projet/phase
        for (projet, phase), week_data in pivot_data.items():
            row = {"Projet": projet, "Phase": phase}
            for week in sorted_weeks:
                label = week_labels[week]
                row[label] = round(week_data.get(week, 0), 2)
            table_data.append(row)

        columns = [
            {"name": "Projet", "id": "Projet", "type": "text"},
            {"name": "Phase", "id": "Phase", "type": "text"}
        ] + [
            {"name": week_labels[week], "id": week_labels[week], "type": "numeric"}
            for week in sorted_weeks
        ]
        static_rows = table_data[:2]
        data_rows = sorted(table_data[2:], key=lambda row: row["Projet"])

        # Fusionner les lignes fixes et les données triées
        table_data = static_rows + data_rows
        return dash_table.DataTable(
            columns=columns,
            data=table_data,
            page_size=15,
            fixed_columns={"headers": True, "data": 2},  
            style_table={
                "maxWidth": "100%",
                "overflowX": "auto"
            },
            style_cell={
                "textAlign": "center",
                "padding": "12px",
                "fontFamily": "Arial, sans-serif",
                "minWidth": "100px",  # utile pour la lisibilité horizontale
                "width": "100px",
                "maxWidth": "120px",
            },
            style_header={
                "fontWeight": "bold",
                "backgroundColor": "#f8f9fa",
                "color": "#495057"
            },
            style_data_conditional=[
                {
                    "if": {"column_id": "Projet"},
                    "minWidth": "200px",
                    "width": "300px",
                    "maxWidth": "500px",
                    "whiteSpace": "normal",  # permet le retour à la ligne
                    "textAlign": "left"
                },
                {
                    "if": {"filter_query": "{Projet} = '📊 Total'"},
                    "backgroundColor": "#d4edda",
                    "fontWeight": "bold",
                    "color": "#155724"
                },
                {
                    "if": {"filter_query": "{Projet} = '⚡ Taux de charge (%)'"},
                    "backgroundColor": "#d1ecf1",
                    "fontWeight": "bold",
                    "color": "#0c5460"
                }
            ]
        )

    # Méthodes utilitaires
    def is_urgent(self, task):
        """Vérifier si une tâche est urgente"""
        if not task.due_date:
            return False
        try:
            due_date = datetime.strptime(str(task.due_date), "%Y-%m-%d")
            return due_date <= datetime.now() + timedelta(days=3)
        except:
            return False

    def get_completion_rate(self, completed_tasks, total_tasks):
        """Calculer le taux de completion"""
        if not total_tasks:
            return 0
        return round(len(completed_tasks) / len(total_tasks) * 100, 1)

    def get_status_color(self, status):
        """Obtenir la couleur selon le statut"""
        colors = {
            'Actif': 'success',
            'En cours': 'primary',
            'Terminé': 'secondary',
            'Suspendu': 'warning',
            'Annulé': 'danger'
        }
        return colors.get(status, 'secondary')
    

    def user_workload_layout_aggrid(self, user_id=None):
        """Plan de charge avec Dash AG Grid - Version améliorée du tableau"""
        
                
        def iso_week_to_monday(iso_week_str):
            year, week = iso_week_str.split("-W")
            # ici on parse l'année ISO correctement
            dt = datetime.strptime(f'{year} {week} 1', '%G %V %u')
            return dt

        def format_week_header(iso_week_str):
            monday = iso_week_to_monday(iso_week_str)
            iso_year, iso_week = iso_week_str.split("-W")
            # on affiche Semaine + Date du lundi + année ISO
            return f"S{iso_week} ({iso_year})\n{monday.strftime('%d/%m/%Y')}"

        user_id = user_id or current_user.id

        entries = (
            db.session.query(Workload)
            .filter(Workload.bimuser_id == user_id)
            .join(ProjectPhase)
            .join(Project)
            .join(Phase)
            .order_by(Workload.week)
            .all()
        )

        if not entries:
            return self.render_empty_state(
                "fas fa-calendar-times",
                "Aucune donnée de plan de charge",
                "Aucune donnée de plan de charge disponible pour le moment."
            )

        pivot_data = defaultdict(lambda: defaultdict(float))
        all_weeks = set()
        
        for entry in entries:
            key = (entry.project_phase.project_parent.name, entry.project_phase.phase.name)
            pivot_data[key][entry.week] += entry.planned_days or 0
            all_weeks.add(entry.week)

        sorted_weeks = sorted(all_weeks)
        week_labels = {week: format_week_header(week) for week in sorted_weeks}

        # Calcul des totaux
        total_row = {"Projet": "📊 TOTAL", "Phase": "", "rowType": "total"}
        charge_row = {"Projet": "⚡ TAUX DE CHARGE (%)", "Phase": "", "rowType": "charge"}
        
        total_global = 0
        for week in sorted_weeks:
            total_days = sum(week_data.get(week, 0) for week_data in pivot_data.values())
            label = week_labels[week]
            total_row[label] = round(total_days, 2)
            total_global += total_days
            
            charge_rate = round((total_days / 7.8) * 100, 1) if total_days > 0 else 0
            charge_row[label] = charge_rate

        # Total global
        total_row["Total"] = round(total_global, 2)
        avg_charge = round((total_global / (len(sorted_weeks) * 7.8)) * 100, 1) if sorted_weeks else 0
        charge_row["Total"] = f"{avg_charge}%"

        # Données des projets
        row_data = [charge_row, total_row]
        
        for (projet, phase), week_data in pivot_data.items():
            row = {
                "Projet": projet, 
                "Phase": phase, 
                "rowType": "data",
                "Total": 0
            }
            for week in sorted_weeks:
                label = week_labels[week]
                days = round(week_data.get(week, 0), 2)
                row[label] = days if days > 0 else ""
                row["Total"] += days
            row["Total"] = round(row["Total"], 2) if row["Total"] > 0 else ""
            row_data.append(row)

        # Configuration des colonnes
        column_defs = [
            {
                "headerName": "Projet",
                "field": "Projet",
                "pinned": "left",
                "width": 200,
                "cellStyle": {"fontWeight": "500"},
                "tooltipField": "Projet"
            },
            {
                "headerName": "Phase", 
                "field": "Phase",
                "pinned": "left",
                "width": 120,
                "cellStyle": {"fontSize": "12px", "color": "#6c757d"}
            }
        ]

        # Colonnes des semaines
        for week in sorted_weeks:
            label = week_labels[week]
            column_defs.append({
                "headerName": label,
                "field": label,
                "width": 80,
                "type": "numericColumn",
                "cellStyle": {
                    "params": {
                        "function": """
                        function(params) {
                            if (params.data.rowType === 'charge') {
                                const value = parseFloat(params.value);
                                if (value > 120) return {backgroundColor: '#f8d7da', color: '#721c24', fontWeight: 'bold'};
                                if (value > 100) return {backgroundColor: '#fff3cd', color: '#856404', fontWeight: 'bold'};
                                return {backgroundColor: '#d1ecf1', color: '#0c5460', fontWeight: 'bold'};
                            }
                            if (params.data.rowType === 'total') {
                                return {backgroundColor: '#d4edda', color: '#155724', fontWeight: 'bold'};
                            }
                            if (!params.value || params.value === 0) {
                                return {color: '#6c757d', fontStyle: 'italic'};
                            }
                            return {textAlign: 'center'};
                        }
                        """
                    }
                },
                "valueFormatter": {
                    "function": """
                    function(params) {
                        if (!params.value || params.value === 0) return '';
                        if (params.data.rowType === 'charge') return params.value + '%';
                        return typeof params.value === 'number' ? params.value.toFixed(1) : params.value;
                    }
                    """
                }
            })

        # Colonne Total
        column_defs.append({
            "headerName": "Total",
            "field": "Total", 
            "pinned": "right",
            "width": 80,
            "type": "numericColumn",
            "cellStyle": {
                "backgroundColor": "#f8f9fa",
                "fontWeight": "600",
                "border": "2px solid #dee2e6"
            },
            "valueFormatter": {
                "function": """
                function(params) {
                    if (!params.value || params.value === 0) return '';
                    return typeof params.value === 'number' ? params.value.toFixed(1) : params.value;
                }
                """
            }
        })

        return html.Div([
            # Header avec informations contextuelles
            dbc.Row([
                dbc.Col([
                    html.H4([
                        html.I(className="fas fa-calendar-alt me-2"),
                        "Plan de Charge"
                    ], className="mb-0"),
                    html.Small(f"Période: {format_week_header(sorted_weeks[0])} → {format_week_header(sorted_weeks[-1])}", 
                            className="text-muted")
                ], width=8),
                dbc.Col([
                    dbc.Badge(f"Charge moyenne: {avg_charge}%", 
                            color="success" if avg_charge <= 100 else "warning" if avg_charge <= 120 else "danger",
                            className="fs-6")
                ], width=4, className="text-end")
            ], className="mb-3"),

            # AG Grid
            dag.AgGrid(
                id="workload-aggrid",
                rowData=row_data,
                columnDefs=column_defs,
                
                # Configuration générale
                defaultColDef={
                    "sortable": True,
                    "filter": True,
                    "resizable": True,
                    "cellStyle": {"textAlign": "center"},
                },
                
                # Styles et thème
                className="ag-theme-alpine",
                
                # Configuration avancée
                dashGridOptions={
                    "rowHeight": 40,
                    "headerHeight": 60,
                    "animateRows": True,
                    "enableRangeSelection": True,
                    "suppressMovableColumns": True,
                    "suppressColumnVirtualisation": False,
                    
                    # Lignes fixes en haut
                    "pinnedTopRowData": [charge_row, total_row],
                    
                    # Style conditionnel
                    "getRowStyle": {
                        "function": """
                        function(params) {
                            if (params.data.rowType === 'charge') {
                                return {backgroundColor: '#e3f2fd', fontWeight: 'bold'};
                            }
                            if (params.data.rowType === 'total') {
                                return {backgroundColor: '#e8f5e8', fontWeight: 'bold'};
                            }
                            if (params.node.rowIndex % 2 === 0) {
                                return {backgroundColor: '#f8f9fa'};
                            }
                            return null;
                        }
                        """
                    },
                    
                    # Export
                    "enableExport": True,
                    "exportFileName": "plan_de_charge",
                    
                    # Pagination
                    "pagination": True,
                    "paginationPageSize": 20,
                    
                    # Grouping par projet
                    "autoGroupColumnDef": {
                        "headerName": "Projets",
                        "minWidth": 200,
                        "cellRendererParams": {"suppressCount": True}
                    }
                },
                
                # Taille
                style={"height": "600px", "width": "100%"}
            ),

            # Footer avec légende et outils
            html.Div([
                dbc.Row([
                    dbc.Col([
                        html.Div([
                            dbc.Badge("🟢 Normal (<100%)", color="success", className="me-2"),
                            dbc.Badge("🟡 Attention (100-120%)", color="warning", className="me-2"),
                            dbc.Badge("🔴 Surcharge (>120%)", color="danger", className="me-2"),
                        ])
                    ], width=8),
                    dbc.Col([
                        dbc.ButtonGroup([
                            dbc.Button([
                                html.I(className="fas fa-download me-1"),
                                "Export Excel"
                            ], color="outline-primary", size="sm", id="export-btn"),
                            dbc.Button([
                                html.I(className="fas fa-expand me-1"),
                                "Plein écran"
                            ], color="outline-secondary", size="sm", id="fullscreen-btn")
                        ])
                    ], width=4, className="text-end")
                ])
            ], className="mt-3 p-3 bg-light rounded"),

            # Tooltip d'aide
            dbc.Tooltip([
                html.Div([
                    html.Strong("💡 Astuces d'utilisation:"),
                    html.Ul([
                        html.Li("Clic droit sur les colonnes pour plus d'options"),
                        html.Li("Glisser-déposer pour réorganiser les colonnes"),
                        html.Li("Double-clic sur les bordures pour ajuster la taille"),
                        html.Li("Ctrl+C pour copier les cellules sélectionnées"),
                        html.Li("Utilisez les filtres pour affiner la vue")
                    ], className="mb-0 small")
                ])
            ], target="workload-aggrid", placement="top")
        ], className="workload-container p-3")



    def register_callbacks(self):

        # === Update project phases when project changes ===
        @self.app.callback(
            Output("input-project-phase", "options"),
            Input("input-project-name", "value"),
            prevent_initial_call=True,
        )
        def update_phase_options(project_id):
            if project_id: 
                phases = ProjectPhase.query.filter(ProjectPhase.project_id==project_id).all()

                return [{"label": p.phase.name, "value": p.id} for p in phases]
            return None

        # === Open event details modal when clicking event ===
        @self.app.callback(
            Output("modal", "opened"),
            Output("modal", "title"),
            Output("modal_event_display_context", "children"),
            Output("selected-event-id", "data"),
            [Input("modal-close-button", "n_clicks"), Input("calendar", "clickedEvent")],
            State("modal", "opened"),
            prevent_initial_call=True,
        )
        def toggle_event_modal(close_click, clicked_event, opened):
            ctx = callback_context
            if not ctx.triggered:
                return dash.no_update, dash.no_update, dash.no_update, dash.no_update

            trigger = ctx.triggered[0]["prop_id"].split(".")[0]

            if trigger == "calendar" and clicked_event:
                return (
                    True,
                    clicked_event["title"],
                    html.Div([
                        html.P(f"Project: {clicked_event['extendedProps'].get('project_name')}"),
                        html.P(f"Phase: {clicked_event['extendedProps'].get('phase_name')}"),
                        html.P(clicked_event["extendedProps"].get("context", "")),
                    ]),
                    clicked_event["id"],  # store event id
                )
            elif trigger == "modal-close-button":
                return False, dash.no_update, dash.no_update, None

            return opened, dash.no_update, dash.no_update, dash.no_update

        # === Open add modal when clicking on date ===
        @self.app.callback(
            Output("add_modal", "opened"),
            Output("start_date", "value"),
            Output("end_date", "value"),
            Output("start_time", "value"),
            Output("end_time", "value"),
            [Input("calendar", "dateClicked"), Input("modal_close_new_event_button", "n_clicks")],
            State("add_modal", "opened"),
            prevent_initial_call=True,
        )
        def toggle_add_modal(dateClicked, close_clicks, opened):
            ctx = callback_context
            if not ctx.triggered:
                return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

            trigger = ctx.triggered[0]["prop_id"].split(".")[0]

            if trigger == "calendar" and dateClicked:
                try:
                    dt = datetime.strptime(dateClicked, "%Y-%m-%dT%H:%M:%S%z")
                except ValueError:
                    dt = datetime.strptime(dateClicked, "%Y-%m-%d")
                start_date = dt.strftime("%Y-%m-%d")
                end_date = start_date
                start_time = dt.strftime("%Y-%m-%d %H:%M:%S")
                end_time = (dt + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
                return True, start_date, end_date, start_time, end_time

            elif trigger == "modal_close_new_event_button":
                return False, dash.no_update, dash.no_update, dash.no_update, dash.no_update

            return opened, dash.no_update, dash.no_update, dash.no_update, dash.no_update

        # === Submit new workload ===
        @self.app.callback(
            Output("calendar", "events"),
            Output("add_modal", "opened", allow_duplicate=True),
            Output("input-project-phase", "value", allow_duplicate=True),
            Output("input-project-name", "value", allow_duplicate=True),
            Output("workload_comparaison", "children", allow_duplicate=True),            

            Input("modal_submit_new_event_button", "n_clicks"),
            State("start_date", "value"),
            State("start_time", "value"),
            State("end_date", "value"),
            State("end_time", "value"),
            State("input-project-name", "value"),
            State("input-project-phase", "value"),
            State("calendar", "events"),
            prevent_initial_call=True,
        )

        def add_new_event(n, start_date, start_time, end_date, end_time, project_id, phase_id, current_events):
            if not n:
                return no_update, no_update, no_update, no_update, no_update


            # Basic guards
            if not (start_date and start_time and end_date and end_time and project_id and phase_id):
                return no_update, no_update, no_update, no_update, no_update


            project = Project.query.get(project_id)
            phase = ProjectPhase.query.get(phase_id)
            if not project or not phase:
                return no_update, no_update, no_update, no_update, no_update


            # Combine date + time (no seconds) -> parse
            # start_time / end_time expected like "HH:MM"
            try:
                start_dt_obj = datetime.strptime(f"{start_date} {start_time}", "%Y-%m-%d %H:%M")
                end_dt_obj   = datetime.strptime(f"{end_date} {end_time}", "%Y-%m-%d %H:%M")
            except ValueError:
                # Bad format; keep UI unchanged
                return no_update, no_update, no_update, no_update, no_update


            # Sanity: end after start
            if end_dt_obj <= start_dt_obj:
                # You could also surface a toast elsewhere; here we just do not update.
                return no_update, no_update, no_update, no_update, no_update


            start_dt = start_dt_obj.strftime("%Y-%m-%dT%H:%M")
            end_dt   = end_dt_obj.strftime("%Y-%m-%dT%H:%M")

            new_event = {
                "id": str(shortuuid.uuid()),
                "start": start_dt,
                "end": end_dt,
                "title": f"{project.name} - {phase.phase.name}",
                "extendedProps": {
                    "project_name": project.name,
                    "phase_name": phase.phase.name,
                    "project_id": project_id,
                    "project_phase_id": phase_id,
                },
                # Optional: ensure FullCalendar treats it as timed (not all-day)
                "allDay": False,
            }

            hours = round((end_dt_obj - start_dt_obj).total_seconds() / 3600, 2)

            dw = DailyWorkload(
                id=new_event["id"],
                project_id=project_id,
                project_phase_id=phase_id,
                user_id=current_user.id,
                date=start_dt_obj.date(),
                hours=hours,
                start_time=start_dt_obj.time(),   
                end_time=end_dt_obj.time(),   )
            db.session.add(dw)
            db.session.commit()


            week = start_dt_obj.strftime("%Y-W%W")

            rw = RealWorkload.query.filter_by(
                bimuser_id=current_user.id,
                project_phase_id=phase_id,
                week=week
            ).first()

            if rw:
                # Mise à jour (ajouter les heures converties en jours)
                rw.actual_days = (rw.actual_days or 0) + (hours / 7.0)
            else:
                # Création nouvelle ligne
                rw = RealWorkload(
                    bimuser_id=current_user.id,
                    project_phase_id=phase_id,
                    week=week,
                    actual_days=hours / 7.0
                )
                db.session.add(rw)

            db.session.commit()

            return current_events + [new_event], False, None, None , self.workload_comparaison()

        @self.app.callback(
            Output("calendar", "events",allow_duplicate=True),
            Output("modal", "opened", allow_duplicate=True),
            Output("workload_comparaison", "children", allow_duplicate=True),            

            Input("modal-delete-button", "n_clicks"),
            State("selected-event-id", "data"),
            State("calendar", "events"),
            prevent_initial_call=True,
        )
        def delete_event(n, event_id, current_events):
            if not n or not event_id:
                return no_update, no_update

            # remove from calendar events
            updated_events = [e for e in current_events if e.get("id") != event_id]            
            logging.warning(event_id)
            DailyWorkload.query.filter_by(id=event_id).delete()

            db.session.commit()

            return updated_events, False , self.workload_comparaison()
