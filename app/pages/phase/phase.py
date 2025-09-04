import dash_bootstrap_components as dbc
from dash import html, ctx, ALL, callback_context, dcc
from sqlalchemy.orm import joinedload
from database.model import ProjectPhase as dbProjectPhase, Phase as dbPhase, Task as dbTask, BimUsers as dbBimusers, CustomTask, StandardTask, Workload 
from database.db import db
from dash import Input, Output, State, no_update
from datetime import datetime, date, timedelta
from collections import defaultdict
import logging
import feffery_antd_components as fac
from flask_login import current_user

logging.basicConfig(
    level=logging.DEBUG,
    format='[%(levelname)s] %(asctime)s - %(name)s - %(message)s'
)

logger = logging.getLogger(__name__)

class Phase:
    def __init__(self, app):
        self.app = app
        self.register_callback()

    def layout(self, project_phase_id):
        self.project_phase_id = project_phase_id
        project_phase = dbProjectPhase.query.get(project_phase_id)
        if not project_phase:
            return self._create_error_alert("Phase introuvable.", "danger")

        phase = project_phase.phase
        if not phase:
            return self._create_error_alert("Détail de la phase indisponible.", "warning")

        return dbc.Container([
            # Enhanced header with breadcrumb
            self._create_header(phase, project_phase),
            
            # Main content with improved layout
            dbc.Row([
                # Left sidebar - Phase information
                dbc.Col([
                    self._create_phase_info_card(project_phase),
                    self._create_calendar_card(project_phase)
                ], width=4, className="pe-3"),

                # Main content area - Tasks
                dbc.Col([
                    self._create_tasks_card(project_phase),
                    self._create_analytics_card(project_phase)
                ], width=8)
            ], className="g-0"),

            # Modals
            self._create_delete_phase_modal(),
            self._create_enhanced_task_modal(project_phase),
            
            # Hidden components
            dcc.Location(id="redirect", refresh=True),
            html.Div(id="delete-phase-dummy"),
            
            # Toast notifications
            dbc.Toast(
                id="notification-toast",
                header="Notification",
                is_open=False,
                dismissable=True,
                duration=4000,
                style={"position": "fixed", "top": 20, "right": 20, "z-index": 9999}
            )
        ], fluid=True, className="py-4")

    def _create_error_alert(self, message, color):
        return dbc.Container([
            dbc.Alert([
                html.I(className="fas fa-exclamation-triangle me-2"),
                message
            ], color=color, className="d-flex align-items-center")
        ])

    def _create_header(self, phase, project_phase):
        return dbc.Row([
            dbc.Col([
                # Breadcrumb
         dbc.Breadcrumb(
    items=[
        {"label": "Projets", "href": "/BIMSYS/projects", "external_link": True},
        {
            "label": project_phase.project_parent.name if project_phase and project_phase.project_parent else "Projet inconnu",
            "href": f"/BIMSYS/project/{project_phase.project_id}" if project_phase else "#",
            "external_link": True,
        },
        {"label": phase.name if phase else "Phase inconnue", "active": True},
    ],
    className="mb-3"
),

                
                # Page title with actions
                dbc.Row([
                    dbc.Col([
                        html.H2([
                            html.I(className="fas fa-layer-group me-3 text-primary"),
                            f"Phase : {phase.name}"
                        ], className="mb-0 fw-bold")
                    ]),
                    dbc.Col([
                        dbc.ButtonGroup([
                            dbc.Button([
                                html.I(className="fas fa-edit me-2"),
                                "Modifier"
                            ], color="outline-primary", size="sm", id="edit-phase-btn"),
                            dbc.Button([
                                html.I(className="fas fa-trash me-2"),
                                "Supprimer"
                            ], color="outline-danger", size="sm", id="delete-phase-button")
                        ])
                    ], width="auto", className="text-end")
                ], align="center")
            ])
        ], className="mb-4")

    def _create_phase_info_card(self, project_phase):
        progress_value = self._calculate_progress(project_phase)
        
        return dbc.Card([
            dbc.CardHeader([
                html.H5([
                    html.I(className="fas fa-info-circle me-2"),
                    "Informations de la phase"
                ], className="mb-0 text-primary")
            ]),
            dbc.CardBody([
                # Project info (read-only)
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Projet associé", className="fw-semibold text-muted small"),
                        dbc.InputGroup([
                            dbc.InputGroupText(html.I(className="fas fa-project-diagram")),
                            dbc.Input(
                                value=project_phase.project_parent.name,
                                disabled=True,
                                className="bg-light"
                            )
                        ], className="mb-3")
                    ])
                ]),

                # Date inputs with better styling
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Date de début", className="fw-semibold text-muted small"),
                        dbc.InputGroup([
                            dbc.InputGroupText(html.I(className="fas fa-calendar-alt")),
                            dbc.Input(
                                type="date",
                                value=str(project_phase.start_date) if project_phase.start_date else "",
                                id="input-phase-start-date"
                            )
                        ], className="mb-3")
                    ], width=6),
                    dbc.Col([
                        dbc.Label("Date de fin", className="fw-semibold text-muted small"),
                        dbc.InputGroup([
                            dbc.InputGroupText(html.I(className="fas fa-calendar-check")),
                            dbc.Input(
                                type="date",
                                value=str(project_phase.end_date) if project_phase.end_date else "",
                                id="input-phase-end-date"
                            )
                        ], className="mb-3")
                    ], width=6)
                ]),

                # Duration and progress
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Durée (semaines)", className="fw-semibold text-muted small"),
                        dbc.InputGroup([
                            dbc.InputGroupText(html.I(className="fas fa-clock")),
                            dbc.Input(
                                value=str(len(self.get_weeks_number(project_phase)) if self.get_weeks_number(project_phase) else 0),
                                disabled=True,
                                className="bg-light"
                            )
                        ], className="mb-3")
                    ], width=6),
                    dbc.Col([
                        dbc.Label("Progression", className="fw-semibold text-muted small"),
                        dbc.Progress(
                            value=progress_value,
                            color="success" if progress_value == 100 else "info",
                            striped=True,
                            animated=progress_value < 100,
                            className="mb-2"
                        ),
                        html.Small(f"{progress_value}% complété", className="text-muted")
                    ], width=6)
                ]),

                # BIM Manager selection
                self._create_bim_manager_section(project_phase),

                # Budget section with better visualization
                self._create_budget_section(project_phase)
            ])
        ], className="shadow-sm mb-4")

    def _create_bim_manager_section(self, project_phase):
        bim_users = dbBimusers.query.filter(dbBimusers.role == "BIM MANAGER").all()
        options = [{"label": u.name, "value": u.id} for u in bim_users]
        options.append({"label": "Non assigné", "value": "None"})

        return dbc.Row([
            dbc.Col([
                dbc.Label("BIM Manager", className="fw-semibold text-muted small"),
                dbc.InputGroup([
                    dbc.InputGroupText(html.I(className="fas fa-user-tie")),
                    dbc.Select(
                        id="input-phase-bim-manager",
                        options=options,
                        value=project_phase.assigned_bimuser.id if project_phase.assigned_bimuser else "None"
                    )
                ], className="mb-3")
            ])
        ])

    def _create_budget_section(self, project_phase):
        return html.Div([
            html.Hr(className="my-3"),
            html.H6("Budget et ressources", className="text-primary mb-3"),
            
            dbc.Row([
                dbc.Col([
                    dbc.Label("Jours tâches", className="fw-semibold text-muted small"),
                    dbc.InputGroup([
                        dbc.InputGroupText(html.I(className="fas fa-tasks")),
                        dbc.Input(
                            id="input-task-days-budget",
                            value=project_phase.tasks_days_budget or 0,
                            disabled=True,
                            className="bg-light"
                        ),
                        dbc.InputGroupText("j")
                    ], className="mb-3")
                ], width=6),
                dbc.Col([
                    dbc.Label("Jours additionnels", className="fw-semibold text-muted small"),
                    dbc.InputGroup([
                        dbc.InputGroupText(html.I(className="fas fa-plus")),
                        dbc.Input(
                            id="input-costum-days-budget",
                            type="number",
                            value=project_phase.costum_days_budget or 0,
                            min=0
                        ),
                        dbc.InputGroupText("j")
                    ], className="mb-3")
                ], width=6)
            ]),

            dbc.Row([
                dbc.Col([
                    dbc.Label("Budget total (jours)", className="fw-semibold text-muted small"),
                    dbc.InputGroup([
                        dbc.InputGroupText(html.I(className="fas fa-calendar-day")),
                        dbc.Input(
                            id="input-phase-days-budget",
                            value=project_phase.days_budget or 0,
                            disabled=True,
                            className="bg-light fw-bold"
                        ),
                        dbc.InputGroupText("j")
                    ], className="mb-3")
                ], width=6),
                dbc.Col([
                    dbc.Label("Budget (euros)", className="fw-semibold text-muted small"),
                    dbc.InputGroup([
                        dbc.InputGroupText(html.I(className="fas fa-euro-sign")),
                        dbc.Input(
                            id="input-phase-euros-budget",
                            type="number",
                            value=project_phase.euros_budget or 0,
                            min=0
                        ),
                        dbc.InputGroupText("€")
                    ], className="mb-3")
                ], width=6)
            ]),

            dbc.Row([
                dbc.Col([
                    dbc.Label("Répartition hebdomadaire", className="fw-semibold text-muted small"),
                    dbc.InputGroup([
                        dbc.InputGroupText(html.I(className="fas fa-chart-line")),
                        dbc.Input(
                            id="weekly-partition",
                            value=str(self.calculate_weekly_partition(project_phase)) + " j/sem" if self.calculate_weekly_partition(project_phase) else "N/A",
                            disabled=True,
                            className="bg-light"
                        )
                    ], className="mb-3")
                ], width=6),
                dbc.Col([
                    dbc.Label("Nombre de tâches", className="fw-semibold text-muted small"),
                    dbc.InputGroup([
                        dbc.InputGroupText(html.I(className="fas fa-list-check")),
                        dbc.Input(
                            value=len(project_phase.tasks),
                            disabled=True,
                            className="bg-light"
                        )
                    ], className="mb-3")
                ], width=6)
            ])
        ])

    def _create_calendar_card(self, project_phase):
        return dbc.Card([
            dbc.CardHeader([
                html.H5([
                    html.I(className="fas fa-calendar me-2"),
                    "Calendrier des semaines"
                ], className="mb-0 text-primary")
            ]),
            dbc.CardBody([
                html.Div(
                    self.construire_calendrier_dash(project_phase),
                    id='phase-calendar-container',
                    style={
                        "overflowX": "auto",
                        "overflowY": "hidden",
                        "border": "1px solid #e9ecef",
                        "borderRadius": "0.375rem",
                        "backgroundColor": "#f8f9fa"
                    }
                )
            ])
        ], className="shadow-sm mb-4")

    def _create_tasks_card(self, project_phase):
        return dbc.Card([
            dbc.CardHeader([
                dbc.Row([
                    dbc.Col([
                        html.H5([
                            html.I(className="fas fa-tasks me-2"),
                            "Tâches associées"
                        ], className="mb-0 text-primary")
                    ]),
                    dbc.Col([
                        dbc.Button([
                            html.I(className="fas fa-plus me-2"),
                            "Ajouter une tâche"
                        ], color="primary", size="sm", id="add-project-task")
                    ], width="auto")
                ], align="center")
            ]),
            dbc.CardBody([
                html.Div(
                    self.get_project_phase_tasks(project_phase),
                    id='tasks-display'
                )
            ])
        ], className="shadow-sm mb-4")

    def _create_analytics_card(self, project_phase):
        return dbc.Card([
            dbc.CardHeader([
                html.H5([
                    html.I(className="fas fa-chart-pie me-2"),
                    "Analyse des tâches"
                ], className="mb-0 text-primary")
            ]),
            dbc.CardBody([
                self._create_task_analytics(project_phase)
            ])
        ], className="shadow-sm")

    def _create_task_analytics(self, project_phase):
        if not project_phase.tasks:
            return html.P("Aucune donnée disponible", className="text-muted text-center py-4")

        # Calculate task statistics
        tasks = project_phase.tasks
        total_tasks = len(tasks)
        completed_tasks = len([t for t in tasks if t.status == "Terminée"])
        in_progress_tasks = len([t for t in tasks if t.status == "En cours"])
        todo_tasks = len([t for t in tasks if t.status == "À faire"])
        urgent_tasks = len([t for t in tasks if t.status == "Urgente"])

        return dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4(str(total_tasks), className="text-center mb-0 fw-bold text-primary"),
                        html.P("Total", className="text-center text-muted mb-0 small")
                    ])
                ], color="light", outline=True)
            ], width=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4(str(completed_tasks), className="text-center mb-0 fw-bold text-success"),
                        html.P("Terminées", className="text-center text-muted mb-0 small")
                    ])
                ], color="light", outline=True)
            ], width=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4(str(in_progress_tasks), className="text-center mb-0 fw-bold text-warning"),
                        html.P("En cours", className="text-center text-muted mb-0 small")
                    ])
                ], color="light", outline=True)
            ], width=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4(str(urgent_tasks), className="text-center mb-0 fw-bold text-danger"),
                        html.P("Urgentes", className="text-center text-muted mb-0 small")
                    ])
                ], color="light", outline=True)
            ], width=3)
        ])

    def _calculate_progress(self, project_phase):
        if not project_phase.tasks:
            return 0
        
        completed_tasks = len([t for t in project_phase.tasks if t.status == "Terminée"])
        total_tasks = len(project_phase.tasks)
        
        return round((completed_tasks / total_tasks) * 100) if total_tasks > 0 else 0

    def get_weeks_number(self, project_phase):
        if project_phase.start_date and project_phase.end_date and project_phase.start_date < project_phase.end_date:
            current = project_phase.start_date - timedelta(days=project_phase.start_date.weekday())
            lundis = []

            while current <= project_phase.end_date:
                lundis.append(current)
                current += timedelta(weeks=1)

            return lundis
        return []

    def construire_calendrier_dash(self, project_phase):
        lundis = self.get_weeks_number(project_phase)
        
        if not lundis or not project_phase.days_budget or not project_phase.start_date or not project_phase.end_date:
            return html.Div([
                html.I(className="fas fa-calendar-times fa-3x text-muted mb-3"),
                html.P("Calendrier indisponible", className="text-muted")
            ], className="text-center py-4")

        nb_semaines = len(lundis)

        # Enhanced header rows with better styling
        ligne_dates = html.Tr([
            html.Th("", className="bg-primary text-white"),
            *[html.Th(lundi.strftime("%d/%m"), className="bg-primary text-white text-center") for lundi in lundis]
        ])
        
        ligne_jours = html.Tr([
            html.Td("Jour", className="bg-light font-weight-bold"),
            *[html.Td("Lun", className="text-center text-muted") for _ in lundis]
        ])
        
        ligne_semaines = html.Tr([
            html.Td("Semaine", className="bg-light font-weight-bold"),
            *[html.Td(f"S{lundi.isocalendar()[1]}", className="text-center text-muted") for lundi in lundis]
        ])

        lignes = [ligne_dates, ligne_jours, ligne_semaines]

        if nb_semaines:
            charge_hebdo = round(project_phase.days_budget / nb_semaines, 2)
            ligne_charge = html.Tr([
                html.Td("Charge", className="bg-light font-weight-bold"),
                *[html.Td([
                    html.Span(f"{charge_hebdo}j", className="badge bg-info")
                ], className="text-center") for _ in lundis]
            ])
            lignes.append(ligne_charge)

        # Enhanced task visualization
        semaine_tasks = defaultdict(list)
        for task in (project_phase.tasks or []):
            if task.due_date:
                for idx, lundi in enumerate(lundis):
                    dimanche = lundi + timedelta(days=6)
                    if lundi <= task.due_date <= dimanche:
                        semaine_tasks[idx].append(task)
                        break

        max_tasks_in_week = max((len(tlist) for tlist in semaine_tasks.values()), default=0)

        for task_index in range(max_tasks_in_week):
            row = [html.Td("Tâches" if task_index == 0 else "", className="bg-light font-weight-bold")]
            for week_idx in range(nb_semaines):
                tasks = semaine_tasks.get(week_idx, [])
                if task_index < len(tasks):
                    task = tasks[task_index]
                    row.append(html.Td(self._create_task_circle(task), className="text-center"))
                else:
                    row.append(html.Td("", className="text-center"))
            lignes.append(html.Tr(row))

        table = html.Table(
            lignes,
            className="table table-sm table-hover",
            style={
                "minWidth": f"{max(len(lundis)*80, 600)}px",
                "fontSize": "0.85rem"
            }
        )

        return table

    def _create_task_circle(self, task):
        status_config = {
            "À faire": {"color": "#007bff", "icon": "far fa-circle"},
            "En cours": {"color": "#ffc107", "icon": "fas fa-play-circle"},
            "Terminée": {"color": "#28a745", "icon": "fas fa-check-circle"},
            "Urgente": {"color": "#dc3545", "icon": "fas fa-exclamation-circle"}
        }
        
        config = status_config.get(task.status, {"color": "#6c757d", "icon": "far fa-circle"})
        cercle_id = f"task_circle_{task.id}"
        
        task_info = dbc.Card([
            dbc.CardBody([
                html.H6(task.name, className="mb-2 text-primary"),
                html.P(task.description or "Aucune description", className="mb-2 small"),
                dbc.Row([
                    dbc.Col([
                        html.Strong("Statut: ", className="small"),
                        dbc.Badge(task.status, color="secondary", className="small")
                    ], width=12),
                    dbc.Col([
                        html.Strong("Assigné: ", className="small"),
                        html.Span(task.assigned_to or "Non assigné", className="small")
                    ], width=12),
                    dbc.Col([
                        html.Strong("Échéance: ", className="small"),
                        html.Span(task.due_date.strftime('%d/%m/%Y') if task.due_date else "Non définie", className="small")
                    ], width=12)
                ])
            ])
        ], style={"minWidth": "250px"})

        return html.Div([
            html.I(
                id=cercle_id,
                className=config["icon"],
                style={
                    "color": config["color"],
                    "fontSize": "16px",
                    "cursor": "pointer"
                }
            ),
            dbc.Tooltip(
                target=cercle_id,
                children=task_info,
                placement="top",
                style={"maxWidth": "300px"}
            )
        ])

    def _create_enhanced_task_modal(self, project_phase):
        standard_tasks = StandardTask.query.all()
        standard_tasks_options = [{"label": u.name, "value": u.id} for u in standard_tasks]
        bim_users = dbBimusers.query.filter(dbBimusers.role == "BIM MANAGER").all()
        user_options = [{"label": u.name, "value": u.id} for u in bim_users]

        # Standard task tab with enhanced UI
        standard_task_tab = dbc.Card([
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Tâche standard", className="fw-semibold"),
                        dbc.Select(
                            id="input-standrd-task",
                            options=standard_tasks_options,
                            placeholder="Sélectionner une tâche...",
                            className="mb-3"
                        )
                    ])
                ]),
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Assigné par", className="fw-semibold"),
                        dbc.Input(
                            
                            placeholder="Sélectionner un utilisateur...",
                            className="mb-3",
                            value= current_user.name, disabled=True
                            
                        )
                    ]),
                    dbc.Col([
                        dbc.Label("Assigné à", className="fw-semibold"),
                        dbc.Select(
                            id="input-task-bim-manager",
                            options=user_options,
                            placeholder="Sélectionner un utilisateur...",
                            className="mb-3"
                        )
                    ])
                ]),
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Échéance", className="fw-semibold"),
                        dbc.Input(
                            id="standard-task-due-date",
                            type="date",
                            className="mb-3",
                            min=project_phase.start_date if project_phase.start_date else None,
                            max=project_phase.end_date if project_phase.end_date else None
                        )
                    ])
                ])
            ])
        ], className="border-0")

        # Custom task tab with enhanced UI
        custom_task_tab = dbc.Card([
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Nom de la tâche", className="fw-semibold"),
                        dbc.Input(
                            id="costum-task-name",
                            type="text",
                            placeholder="Entrer le nom de la tâche...",
                            className="mb-3"
                        )
                    ])
                ]),
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Description", className="fw-semibold"),
                        dbc.Textarea(
                            id="costum-task-description",
                            placeholder="Description détaillée de la tâche...",
                            rows=3,
                            className="mb-3"
                        )
                    ])
                ]),
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Jours estimés", className="fw-semibold"),
                        dbc.Input(
                            id="costum-task-estimated-days",
                            type="number",
                            min=0.5,
                            step=0.5,
                            placeholder="Nombre de jours...",
                            className="mb-3"
                        )
                    ], width=6),
                    dbc.Col([
                        dbc.Label("Assigné à", className="fw-semibold"),
                        dbc.Select(
                            id="input-task-bim-manager-custom",
                            options=user_options,
                            placeholder="Sélectionner...",
                            className="mb-3"
                        )
                    ], width=6)
                ]),
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Échéance", className="fw-semibold"),
                        dbc.Input(
                            id="costum-task-due-date",
                            type="date",
                            className="mb-3",
                            min=project_phase.start_date if project_phase.start_date else None,
                            max=project_phase.end_date if project_phase.end_date else None
                        )
                    ])
                ])
            ])
        ], className="border-0")

        return dbc.Modal([
            dbc.ModalHeader([
                dbc.ModalTitle([
                    html.I(className="fas fa-plus-circle me-2"),
                    "Ajouter une nouvelle tâche"
                ])
            ]),
            dbc.ModalBody([
                dbc.Tabs([
                    dbc.Tab(standard_task_tab, label="Tâche standard", tab_id="standard"),
                    dbc.Tab(custom_task_tab, label="Tâche personnalisée", tab_id="custom")
                ], active_tab="standard")
            ]),
            dbc.ModalFooter([
                dbc.Button([
                    html.I(className="fas fa-times me-2"),
                    "Annuler"
                ], id="close-task-modal", color="secondary", outline=True),
                dbc.Button([
                    html.I(className="fas fa-check me-2"),
                    "Ajouter la tâche"
                ], id="submit-task", color="primary")
            ])
        ], id="task-modal", is_open=False, size="lg")

    def get_project_phase_tasks(self, project_phase):
        if not project_phase.tasks:
            return html.Div([
                html.Div([
                    html.I(className="fas fa-tasks fa-3x text-muted mb-3"),
                    html.H5("Aucune tâche", className="text-muted"),
                    html.P("Commencez par ajouter une tâche à cette phase.", className="text-muted")
                ], className="text-center py-5")
            ])

        # Group tasks by status for better organization
        tasks_by_status = defaultdict(list)
        for task in project_phase.tasks:
            tasks_by_status[task.status or "À faire"].append(task)

        status_order = ["Urgente", "En cours", "À faire", "Terminée"]
        status_colors = {
            "À faire": "primary",
            "En cours": "warning", 
            "Terminée": "success",
            "Urgente": "danger"
        }

        sections = []
        for status in status_order:
            if status in tasks_by_status:
                tasks = tasks_by_status[status]
                sections.append(
                    html.Div([
                        dbc.Row([
                            dbc.Col([
                                html.H6([
                                    dbc.Badge(
                                        f"{status} ({len(tasks)})",
                                        color=status_colors[status],
                                        className="mb-3"
                                    )
                                ], className="mb-2")
                            ])
                        ]),
                        html.Div([
                            self._create_enhanced_task_card(task) for task in tasks
                        ], className="mb-4")
                    ])
                )

        return html.Div(sections)

    def _create_enhanced_task_card(self, task):
        # Enhanced task card with modern design
        status_colors = {
            "À faire": "primary",
            "En cours": "warning",
            "Terminée": "success", 
            "Urgente": "danger"
        }
        
        priority_icons = {
            "À faire": "fas fa-circle",
            "En cours": "fas fa-play-circle",
            "Terminée": "fas fa-check-circle",
            "Urgente": "fas fa-exclamation-circle"
        }

        return dbc.Card([
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.Div([
                            html.H6([
                                html.I(className=f"{priority_icons.get(task.status, 'fas fa-circle')} me-2"),
                                task.name
                            ], className="mb-2 fw-bold"),
                            html.P(
                                task.description or "Aucune description disponible",
                                className="text-muted small mb-2",
                                style={"maxHeight": "40px", "overflow": "hidden"}
                            )
                        ])
                    ], width=8),
                    dbc.Col([
                        html.Div([
                            dbc.Badge(
                                task.status or "À faire",
                                color=status_colors.get(task.status, "secondary"),
                                className="mb-2"
                            ),
                            html.Br(),
                            fac.AntdTag(
                                content=f"{task.parent_task.estimated_days or 0} jrs",
                                color='magenta',
                                bordered=False,
                            ) if hasattr(task, 'parent_task') and task.parent_task else None
                        ], className="text-end")
                    ], width=4)
                ]),
                
                html.Hr(className="my-2"),
                
                dbc.Row([
                    dbc.Col([
                        html.Small([
                            html.I(className="fas fa-calendar-alt me-1"),
                            f"Échéance: {task.due_date.strftime('%d/%m/%Y') if task.due_date else 'Non définie'}"
                        ], className="text-muted")
                    ], width=6),
                    dbc.Col([
                        html.Small([
                            html.I(className="fas fa-user me-1"),
                            f"Assigné: {dbBimusers.query.filter(dbBimusers.id == task.assigned_to).one_or_none().name or 'Non assigné'}"
                        ], className="text-muted")
                    ], width=6)
                ]),
                
                dbc.Row([
                    dbc.Col([
                        dbc.ButtonGroup([
                            dbc.Button([
                                html.I(className="fas fa-eye me-1"),
                                "Voir"
                            ], 
                            href=f"/BIMSYS/task/{task.id}",
                            color="outline-primary",
                            size="sm",
                            external_link=True),
                            dbc.Button([
                                html.I(className="fas fa-edit me-1"),
                                "Modifier"
                            ], 
                            color="outline-secondary",
                            size="sm"),
                            dbc.Button([
                                html.I(className="fas fa-trash me-1")
                            ],
                            id={"type": "delete-task-btn", "index": task.id},
                            color="outline-danger",
                            size="sm",
                            title="Supprimer la tâche")
                        ], size="sm")
                    ], className="text-end")
                ], className="mt-2")
            ])
        ], className="shadow-sm mb-3 task-card-hover", style={
            "transition": "all 0.2s ease",
            "border": "1px solid #e9ecef"
        })

    def _create_delete_phase_modal(self):
        return dbc.Modal([
            dbc.ModalHeader([
                dbc.ModalTitle([
                    html.I(className="fas fa-exclamation-triangle text-warning me-2"),
                    "Confirmer la suppression"
                ])
            ]),
            dbc.ModalBody([
                dbc.Alert([
                    html.I(className="fas fa-info-circle me-2"),
                    "Cette action est irréversible. La phase et toutes ses données associées seront définitivement supprimées."
                ], color="warning"),
                html.P([
                    "Êtes-vous sûr de vouloir supprimer cette phase ? ",
                    html.Strong("Cette action ne peut pas être annulée.")
                ])
            ]),
            dbc.ModalFooter([
                dbc.Button([
                    html.I(className="fas fa-times me-2"),
                    "Annuler"
                ], id="cancel-delete-phase-button", color="secondary", outline=True),
                dbc.Button([
                    html.I(className="fas fa-trash me-2"),
                    "Supprimer définitivement"
                ], id="validate-delete-phase-button", color="danger")
            ])
        ], id="delete-phases-modal", is_open=False, centered=True)

    def calculate_weekly_partition(self, project_phase):
        try:
            weeks = self.get_weeks_number(project_phase)
            if weeks and project_phase.days_budget:
                return round(project_phase.days_budget / len(weeks), 2)
            return None
        except:
            return None

    def register_callback(self):
        # Delete phase callback
        @self.app.callback(
            [
                Output("delete-phases-modal", "is_open"),
                Output("redirect", "pathname"),
                Output("notification-toast", "is_open"),
                Output("notification-toast", "children"),
                Output("notification-toast", "header")
            ],
            [
                Input("delete-phase-button", "n_clicks"),
                Input("cancel-delete-phase-button", "n_clicks"),
                Input("validate-delete-phase-button", "n_clicks"),
            ],
            [State("delete-phases-modal", "is_open")],
            prevent_initial_call=True,
        )
        def delete_phase(n_open, n_cancel, n_validate, is_open):
            ctx = callback_context.triggered_id

            if ctx == "delete-phase-button":
                return True, no_update, no_update, no_update, no_update

            if ctx == "cancel-delete-phase-button":
                return False, no_update, no_update, no_update, no_update

            if ctx == "validate-delete-phase-button":
                try:
                    pp = dbProjectPhase.query.get(self.project_phase_id)
                    if pp:
                        parent_id = pp.project_id
                        db.session.delete(pp)
                        db.session.commit()
                        return False, f"/BIMSYS/project/{parent_id}", True, "Phase supprimée avec succès", "Succès"
                    return False, no_update, True, "Erreur: Phase introuvable", "Erreur"
                except Exception as e:
                    db.session.rollback()
                    return False, no_update, True, f"Erreur lors de la suppression: {str(e)}", "Erreur"

            return is_open, no_update, no_update, no_update, no_update

        # Task modal callback
        @self.app.callback(
            Output("task-modal", "is_open"),
            [
                Input("add-project-task", "n_clicks"),
                Input("close-task-modal", "n_clicks"),
                Input("submit-task", "n_clicks")
            ],
            [State("task-modal", "is_open")],
            prevent_initial_call=True
        )
        def toggle_task_modal(open_click, close_click, submit_click, is_open):
            if open_click or close_click or submit_click:
                return not is_open
            return is_open

        # Enhanced task management callback
        @self.app.callback(
            [
                Output("tasks-display", "children", allow_duplicate=True),
                Output("phase-calendar-container", "children", allow_duplicate=True),
                Output("input-task-days-budget", "value"),
                Output("input-phase-days-budget", "value", allow_duplicate=True),
                Output("notification-toast", "is_open", allow_duplicate=True),
                Output("notification-toast", "children", allow_duplicate=True),
                Output("notification-toast", "header", allow_duplicate=True),
                # Clear form fields
                Output("costum-task-estimated-days", "value"),
                Output("costum-task-description", "value"),
                Output("costum-task-name", "value"),
                Output("input-task-bim-manager", "value"),
                Output("input-task-bim-manager-custom", "value"),
                Output("input-standrd-task", "value"),
                Output("standard-task-due-date", "value"),
                Output("costum-task-due-date", "value"),
            ],
            [
                Input("submit-task", "n_clicks"),
                Input({"type": "delete-task-btn", "index": ALL}, "n_clicks"),
            ],
            [
                State("costum-task-estimated-days", "value"),
                State("costum-task-description", "value"), 
                State("costum-task-name", "value"),
                State("input-task-bim-manager", "value"),
                State("input-task-bim-manager-custom", "value"),
                State("input-standrd-task", "value"),
                State("standard-task-due-date", "value"),
                State("costum-task-due-date", "value"),
                State("url", "pathname"),
            ],
            prevent_initial_call=True
        )
        def handle_enhanced_task_actions(
            submit_click, delete_clicks, estimated_days, custom_description,
            custom_name, assigned_to_id, assigned_to_id_custom, standard_task_id,
            standard_task_due_date, custom_task_due_date, pathname
        ):
            import re
            from datetime import datetime

            triggered = ctx.triggered_id
            project_phase = dbProjectPhase.query.get(self.project_phase_id)
            
            if not project_phase:
                return (no_update, no_update, no_update, no_update, 
                       True, "Erreur: Phase introuvable", "Erreur",
                       None, None, None, None, None, None, None, None)

            # Handle task deletion
            if isinstance(triggered, dict) and triggered.get("type") == "delete-task-btn":
                task_id = triggered.get("index")
                try:
                    task_to_delete = db.session.query(dbTask).get(task_id)
                    if task_to_delete:
                        db.session.delete(task_to_delete)
                        
                        # Recalculate budgets
                        project_phase.tasks_days_budget = sum([
                            t.parent_task.estimated_days for t in project_phase.tasks 
                            if hasattr(t, 'parent_task') and t.parent_task and t.parent_task.estimated_days
                        ])
                        project_phase.days_budget = (
                            (project_phase.costum_days_budget or 0) + 
                            (project_phase.tasks_days_budget or 0)
                        )
                        
                        db.session.commit()
                        
                        return (
                            self.get_project_phase_tasks(project_phase),
                            self.construire_calendrier_dash(project_phase),
                            project_phase.tasks_days_budget,
                            project_phase.days_budget,
                            True, "Tâche supprimée avec succès", "Succès",
                            None, None, None, None, None, None, None, None
                        )
                except Exception as e:
                    db.session.rollback()
                    return (no_update, no_update, no_update, no_update,
                           True, f"Erreur lors de la suppression: {str(e)}", "Erreur",
                           None, None, None, None, None, None, None, None)

            # Handle task creation  
            if submit_click:
                try:
                    # Standard task creation
                    if standard_task_id and standard_task_due_date:
                        standard_task = StandardTask.query.get(standard_task_id)
                        if not standard_task:
                            return (no_update, no_update, no_update, no_update,
                                   True, "Erreur: Tâche standard introuvable", "Erreur",
                                   None, None, None, None, None, None, None, None)

                        due_date = datetime.strptime(standard_task_due_date, "%Y-%m-%d")
                        task = dbTask(
                            due_date=due_date,
                            project_phase_id=self.project_phase_id,
                            assigned_to=assigned_to_id,
                            standard_task=standard_task
                        )
                        success_message = f"Tâche standard '{standard_task.name}' ajoutée"

                    # Custom task creation
                    elif (custom_task_due_date and estimated_days and 
                          custom_description and custom_name):
                        due_date = datetime.strptime(custom_task_due_date, "%Y-%m-%d")
                        ct = CustomTask(
                            custom_name=custom_name,
                            custom_description=custom_description,
                            estimated_days=estimated_days
                        )
                        task = dbTask(
                            due_date=due_date,
                            project_phase_id=self.project_phase_id,
                            assigned_to=assigned_to_id_custom,
                            custom_task=ct
                        )
                        success_message = f"Tâche personnalisée '{custom_name}' ajoutée"
                    else:
                        return (no_update, no_update, no_update, no_update,
                               True, "Erreur: Champs requis manquants", "Erreur",
                               None, None, None, None, None, None, None, None)

                    # Save task and update budgets
                    db.session.add(task)
                    
                    # Recalculate budgets
                    project_phase.tasks_days_budget = sum([
                        t.parent_task.estimated_days for t in project_phase.tasks
                        if hasattr(t, 'parent_task') and t.parent_task and t.parent_task.estimated_days
                    ])
                    project_phase.days_budget = (
                        (project_phase.costum_days_budget or 0) + 
                        (project_phase.tasks_days_budget or 0)
                    )
                    
                    db.session.commit()

                    # Update workload if conditions are met
                    if (project_phase.assigned_bimuser_id and 
                        project_phase.start_date and project_phase.end_date):
                        Workload.update_workload(project_phase)

                    return (
                        self.get_project_phase_tasks(project_phase),
                        self.construire_calendrier_dash(project_phase),
                        project_phase.tasks_days_budget,
                        project_phase.days_budget,
                        True, success_message, "Succès",
                        None, None, None, None, None, None, None, None
                    )

                except Exception as e:
                    db.session.rollback()
                    return (no_update, no_update, no_update, no_update,
                           True, f"Erreur lors de la création: {str(e)}", "Erreur",
                           None, None, None, None, None, None, None, None)

            return (no_update, no_update, no_update, no_update, no_update, no_update, no_update,
                   None, None, None, None, None, None, None, None)

        # Enhanced phase data update callback
        @self.app.callback(
            [
                Output("delete-phase-dummy", "children"),
                Output("phase-calendar-container", "children", allow_duplicate=True),
                Output("input-phase-days-budget", "value", allow_duplicate=True),
                Output("input-phase-euros-budget", "value"),
                Output("weekly-partition", "value"),
                Output("input-costum-days-budget", "value"),
                Output("notification-toast", "is_open", allow_duplicate=True),
                Output("notification-toast", "children", allow_duplicate=True),
                Output("notification-toast", "header", allow_duplicate=True)
            ],
            [
                Input("input-phase-start-date", "value"),
                Input("input-phase-end-date", "value"),
                Input("input-phase-days-budget", "value"),
                Input("input-phase-euros-budget", "value"),
                Input("input-phase-bim-manager", "value"),
                Input("input-costum-days-budget", "value"),
            ],
            prevent_initial_call=True
        )
        def update_enhanced_phase_data(start_date, end_date, days_budget, 
                                     euros_budget, bim_manager_id, costum_days_budget):
            
            project_phase = dbProjectPhase.query.get(self.project_phase_id)
            if not project_phase:
                return ("", no_update, no_update, no_update, no_update, no_update,
                       True, "Erreur: Phase introuvable", "Erreur")

            ctx_id = callback_context.triggered_id
            
            try:
                # Handle custom days budget update
                if "input-costum-days-budget" in ctx_id:
                    if project_phase.assigned_bimuser:
                        taj = project_phase.assigned_bimuser.taj
                        project_phase.costum_days_budget = costum_days_budget or 0
                        project_phase.days_budget = (
                            (project_phase.costum_days_budget or 0) + 
                            (project_phase.tasks_days_budget or 0)
                        )
                        project_phase.euros_budget = (
                            (project_phase.costum_days_budget or 0) * taj + 
                            taj * (project_phase.tasks_days_budget or 0)
                        )
                        db.session.commit()
                        Workload.update_workload(project_phase)

                        return ("", self.construire_calendrier_dash(project_phase),
                               project_phase.days_budget, project_phase.euros_budget,
                               self.calculate_weekly_partition(project_phase), no_update,
                               True, "Budget personnalisé mis à jour", "Succès")

                # Handle start date update
                elif "input-phase-start-date" in ctx_id:
                    if start_date:
                        project_phase.start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
                        db.session.commit()
                        
                        if (bim_manager_id and bim_manager_id != "None" and 
                            start_date and end_date):
                            Workload.update_workload(project_phase)
                        
                        return ("", self.construire_calendrier_dash(project_phase),
                               no_update, no_update, self.calculate_weekly_partition(project_phase),
                               no_update, True, "Date de début mise à jour", "Succès")

                # Handle end date update  
                elif "input-phase-end-date" in ctx_id:
                    if end_date:
                        project_phase.end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
                        db.session.commit()
                        
                        if (bim_manager_id and bim_manager_id != "None" and 
                            start_date and end_date):
                            Workload.update_workload(project_phase)
                        
                        return ("", self.construire_calendrier_dash(project_phase),
                               no_update, no_update, self.calculate_weekly_partition(project_phase),
                               no_update, True, "Date de fin mise à jour", "Succès")

                # Handle euro budget update
                elif "input-phase-euros-budget" in ctx_id:
                    if euros_budget is not None and project_phase.assigned_bimuser:
                        project_phase.euros_budget = euros_budget
                        taj = project_phase.assigned_bimuser.taj
                        euro_budget_left = euros_budget - (
                            (project_phase.tasks_days_budget or 0) * taj
                        )
                        project_phase.costum_days_budget = max(0, euro_budget_left / taj)
                        project_phase.days_budget = (
                            project_phase.costum_days_budget + 
                            (project_phase.tasks_days_budget or 0)
                        )
                        db.session.commit()
                        
                        if (bim_manager_id and bim_manager_id != "None" and 
                            start_date and end_date):
                            Workload.update_workload(project_phase)
                        
                        return ("", self.construire_calendrier_dash(project_phase),
                               project_phase.days_budget, no_update,
                               self.calculate_weekly_partition(project_phase),
                               project_phase.costum_days_budget,
                               True, "Budget en euros mis à jour", "Succès")

                # Handle BIM manager assignment
                elif "input-phase-bim-manager" in ctx_id:
                    if bim_manager_id and bim_manager_id != "None":
                        project_phase.assigned_bimuser_id = bim_manager_id
                        if project_phase.assigned_bimuser:
                            project_phase.euros_budget = (
                                (project_phase.days_budget or 0) * 
                                project_phase.assigned_bimuser.taj
                            )
                        db.session.commit()
                        
                        if start_date and end_date:
                            Workload.update_workload(project_phase)
                        
                        return ("", no_update, no_update, project_phase.euros_budget,
                               self.calculate_weekly_partition(project_phase), no_update,
                               True, "BIM Manager assigné", "Succès")

                return ("", no_update, no_update, no_update, no_update, no_update,
                       no_update, no_update, no_update)
                
            except Exception as e:
                db.session.rollback()
                return ("", no_update, no_update, no_update, no_update, no_update,
                       True, f"Erreur lors de la mise à jour: {str(e)}", "Erreur")