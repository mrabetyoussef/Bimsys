import dash_bootstrap_components as dbc
from dash import html, dcc
from flask_login import current_user
from database.db import db
from database.model import Project, ProjectPhase, Task
import plotly.express as px
import pandas as pd


class UserPage:
    def __init__(self, app):
        self.app = app

    def layout(self):
        user = current_user
        user_id = user.id

        # --- DATA EXTRACTION ---
        managed_projects = db.session.query(Project).filter_by(bim_manager_id=user_id).all()
        phases = db.session.query(ProjectPhase).filter_by(assigned_bimuser_id=user_id).all()
        tasks = db.session.query(Task).filter_by(assigned_to=user_id).all()
        all_projects = list({p.project_parent for p in phases} | set(managed_projects))

        tasks_done = [t for t in tasks if t.status == "Terminé"]
        tasks_progress = [t for t in tasks if t.status != "Terminé"]

        # --- KPI CARDS ---
        kpi_cards = dbc.Row([
            self.kpi_card("Projets", len(all_projects), "primary"),
            self.kpi_card("Phases assignées", len(phases), "info"),
            self.kpi_card("Tâches totales", len(tasks), "secondary"),
            self.kpi_card("Tâches terminées", len(tasks_done), "success"),
            self.kpi_card("Tâches restantes", len(tasks_progress), "warning"),
        ], className="mb-4")

        # --- GRAPHS ---
        fig_pie = self.pie_chart_task_status(tasks)
        fig_bar = self.bar_project_status(all_projects)

        # --- DETAILS ACCORDION ---
        project_details = self.build_project_accordion(all_projects, user_id)

        return html.Div([
            html.H2(f"Profil de {user.name}", className="my-4"),

            html.Div([
                html.P(f"Email : {user.email}"),
                html.P(f"Rôle : {user.role}")
            ], className="mb-4"),

            kpi_cards,

            dbc.Row([
                dbc.Col(dcc.Graph(figure=fig_pie), md=6),
                dbc.Col(dcc.Graph(figure=fig_bar), md=6),
            ]),

            html.H4("Détail des projets et missions", className="mt-5"),
            html.Div(project_details)
        ], style={"padding": "2rem"})

    def kpi_card(self, title, value, color):
        return dbc.Col(dbc.Card([
            dbc.CardBody([
                html.H5(title, className="card-title"),
                html.H3(str(value), className="card-text")
            ])
        ], color=color, inverse=True), md=2)

    def pie_chart_task_status(self, tasks):
        status_counts = pd.Series([t.status for t in tasks]).value_counts()
        fig = px.pie(values=status_counts.values, names=status_counts.index,
                     title="Répartition des tâches")
        fig.update_layout(margin=dict(t=30, b=0, l=0, r=0))
        return fig

    def bar_project_status(self, projects):
        df = pd.DataFrame([{"Nom": p.name, "Statut": p.status} for p in projects])
        fig = px.histogram(df, x="Statut", color="Statut", title="Projets par statut")
        fig.update_layout(margin=dict(t=30, b=0, l=0, r=0))
        return fig

    def build_project_accordion(self, projects, user_id):
        accordions = []

        for project in projects:
            project_phases = [p for p in project.phases if p.assigned_bimuser_id == user_id]
            items = []

            for phase in project_phases:
                tasks = phase.tasks
                task_list = html.Ul([
                    html.Li(f"{t.name} – {t.status} – Due: {t.due_date}")
                    for t in tasks
                ]) if tasks else html.P("Aucune tâche assignée.")

                items.append(
                    dbc.AccordionItem([
                        html.P(f"Phase: {phase.phase.name}"),
                        html.P(f"Budget jours: {phase.days_budget}"),
                        html.P(f"Budget €: {phase.euros_budget}"),
                        task_list
                    ], title=f"Phase: {phase.phase.name}")
                )

            if items:
                accordions.append(dbc.Card([
                    html.H5(project.name, className="card-header"),
                    dbc.Accordion(items, flush=True)
                ], className="mb-4"))

        return accordions
