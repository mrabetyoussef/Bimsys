import dash_bootstrap_components as dbc
from dash import html, dcc
from flask_login import current_user
from database.db import db
from database.model import Project, ProjectPhase, Task, Workload, Phase
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import dash_table
from flask_login import current_user
from database.db import db
from collections import defaultdict
import logging
from datetime import datetime, timedelta

class UserPage:
    def __init__(self, app):
        self.app = app

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
            # Header avec informations utilisateur
            self.render_user_header(user),
            
            # Section KPI
            self.render_kpi_section(all_projects, phases, tasks, tasks_done, tasks_progress, tasks_urgent),
            
            # Section graphiques
            self.render_charts_section(tasks, all_projects),
            
            # Section détails des projets
            self.render_projects_section(all_projects, user_id),
            
            # Section plan de charge
            self.render_workload_section(user_id)
            
        ], className="user-dashboard")

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
            html.H3([
                html.I(className="fas fa-chart-line me-2"),
                "Vue d'ensemble"
            ], className="mb-4 text-dark fw-bold"),
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
            html.H3([
                html.I(className="fas fa-chart-pie me-2"),
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

        # Calcul des totaux
        total_row = {"Projet": "📊 Total", "Phase": ""}
        charge_row = {"Projet": "⚡ Taux de charge (%)", "Phase": ""}
        
        for week in sorted_weeks:
            total_days = sum(week_data.get(week, 0) for week_data in pivot_data.values())
            total_row[week] = round(total_days, 2)
            charge_row[week] = round((total_days / 7.8) * 100, 1)

        table_data = [charge_row, total_row]

        # Ajout des lignes par projet/phase
        for (projet, phase), week_data in pivot_data.items():
            row = {"Projet": projet, "Phase": phase}
            for week in sorted_weeks:
                row[week] = round(week_data.get(week, 0), 2)
            table_data.append(row)

        columns = [
            {"name": "Projet", "id": "Projet", "type": "text"},
            {"name": "Phase", "id": "Phase", "type": "text"}
        ] + [{"name": w, "id": w, "type": "numeric"} for w in sorted_weeks]

        return dash_table.DataTable(
            columns=columns,
            data=table_data,
            page_size=15,
            style_table={"overflowX": "auto"},
            style_cell={
                "textAlign": "center",
                "padding": "12px",
                "fontFamily": "Arial, sans-serif"
            },
            style_header={
                "fontWeight": "bold",
                "backgroundColor": "#f8f9fa",
                "color": "#495057"
            },
            style_data_conditional=[
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