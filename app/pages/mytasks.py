# pages/user_tasks.py

import calendar
from datetime import date, datetime, timedelta

import pandas as pd
import dash_ag_grid as dag
import feffery_antd_components as fac
import dash_bootstrap_components as dbc
from dash import html, dcc, Input, Output, State, no_update
from flask_login import current_user

from database.db import db
from database.model import Project, ProjectPhase, Phase, Task, BimUsers

# --- Helpers UI ---
STATUS_ORDER = ["Urgente", "À faire", "En cours", "Bloquée", "Terminée"]
PRIORITIES = ["Basse", "Normale", "Haute", "Critique"]

def _safe_str(x, default="-"):
    return default if x is None else str(x)

class UserTasksPage:
    def __init__(self, app):
        self.app = app
        # cache léger (optionnel)
        self._project_options = None
        self.register_callbacks()

    # ---------------------------
    # Layout
    # ---------------------------
    def layout(self):
        return html.Div(
            [
                # En-tête + fil d’Ariane
                dbc.Container(
                    [
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        fac.AntdBreadcrumb(
                                            items=[
                                                {
                                                    "title": "Accueil",
                                                    "href": "/",
                                                    "target": "_self",
                                                    "icon": "antd-home",
                                                },
                                                {
                                                    "title": _safe_str(current_user.name, "Utilisateur"),
                                                    "href": "/BIMSYS/user",
                                                    "target": "_self",
                                                    "icon": "antd-user",
                                                },
                                                {
                                                    "title": "Mes tâches",
                                                    "icon": "antd-check-square",
                                                },
                                            ],
                                            style={"marginBottom": "16px"},
                                        ),
                                        html.H2(
                                            "Mes tâches",
                                            style={
                                                "color": "#1f2937",
                                                "marginBottom": "8px",
                                                "fontWeight": "700",
                                                "fontSize": "28px",
                                            },
                                        ),
                                        html.P(
                                            "Liste des tâches qui me sont assignées, avec filtres et recherche.",
                                            style={"color": "#6b7280", "fontSize": "14px", "marginBottom": "0"},
                                        ),
                                    ],
                                    width=12,
                                ),
                            ]
                        )
                    ],
                    fluid=True,
                    className="px-0",
                ),

                # Filtres
                html.Div(
                    [
                        dbc.Container(
                            [
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            fac.AntdSpace(
                                                [
                                                   
                                                    fac.AntdSelect(
                                                        id="ut-status",
                                                        mode="multiple",
                                                        placeholder="Statuts",
                                                        allowClear=True,
                                                        options=[
                                                            {"label": s, "value": s}
                                                            for s in ["À faire", "En cours", "Bloquée", "Urgente", "Terminée"]
                                                        ],
                                                        style={"width": 220},
                                                    ),
                                                  
                                                    fac.AntdSelect(
                                                        id="ut-project",
                                                        mode="multiple",
                                                        placeholder="Projets",
                                                        allowClear=True,
                                                        options=self._get_project_options(),  # initial
                                                        style={"width": 260},
                                                    ),
                                             
                                                    fac.AntdButton("Réinitialiser", id="ut-reset", type="default"),
                                                ],
                                                wrap=True,
                                            ),
                                            width=12,
                                        )
                                    ],
                                    className="mb-3",
                                )
                            ],
                            fluid=True,
                        )
                    ],
                    style={"padding": "16px 0", "backgroundColor": "#ffffff", "borderBottom": "1px solid #e5e7eb"},
                ),

                # Tableau
                html.Div(
                    [
                        dbc.Container(
                            [
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            dbc.Card(
                                                dbc.CardBody(
                                                    [
                                                        dag.AgGrid(
                                                            id="ut-grid",
                                                            columnDefs=self._columns(),
                                                            rowData=[],
                                                            className="ag-theme-alpine custom-ag-grid",
                                                            columnSize="autoSize",
                                                            defaultColDef={
                                                                "resizable": True,
                                                                "sortable": True,
                                                                "filter": True,
                                                                "minWidth": 100,
                                                                "wrapText": False,
                                                                "headerHeight": 48,
                                                            },
                                                            dashGridOptions={
                                                                "domLayout": "normal",
                                                                "suppressHorizontalScroll": False,
                                                                "rowHeight": 42,
                                                                "headerHeight": 48,
                                                                "animateRows": True,
                                                                "enableRangeSelection": True,
                                                                "pagination": True,
                                                                "paginationPageSize": 10,
                                                                "rowSelection": "single",
                                                            },
                                                        )
                                                    ]
                                                ),
                                                className="shadow-sm",
                                                style={
                                                    "border": "1px solid #e5e7eb",
                                                    "borderRadius": "16px",
                                                    "backgroundColor": "white",
                                                },
                                            ),
                                            width=12,
                                        )
                                    ]
                                )
                            ],
                            fluid=True,
                        )
                    ],
                    style={"padding": "24px 0"},
                ),
            ],
            style={"backgroundColor": "#ffffff", "minHeight": "100vh"},
        )

    def _columns(self):
        return [
          
            {
                "headerName": "Projet",
                "field": "project_name",
                "pinned": "left",
                "tooltipField": "project_name",
                "cellStyle": {"color": "#374151"},
                "flex": 1,
            },
            {
                "headerName": "Phase",
                "field": "phase_name",
                "tooltipField": "phase_name",
                "cellStyle": {"color": "#6b7280"},
                "flex": 0.8,
            },
            {
                "headerName": "Statut",
                "field": "status",
                "flex": 0.7,
                "cellClassRules": {
                    "tag-blue": 'value === "À faire"',
                    "tag-gold": 'value === "En cours"',
                    "tag-red": 'value === "Bloquée"',
                    "tag-volcano": 'value === "Urgente"',
                    "tag-green": 'value === "Terminée"',
                },
            },
          
            {
                "headerName": "Échéance",
                "field": "due_date",
                "sort": "asc",
                "flex": 0.7,
                "cellClassRules": {
                    "date-overdue": '(data.status !== "Terminée") && value && (new Date(value) < new Date().setHours(0,0,0,0))',
                },
            },
             {
                "headerName": "assigned_by",
                "field": "assigned_by",
                "flex": 0.7,
                "cellClassRules": {
                },
            },
               {
                "headerName": "assigned_to",
                "field": "assigned_to",
                "flex": 0.7,
                "cellClassRules": {
                },
            },
        ]

   
    def _query_tasks(self, search=None, statuses=None, priorities=None, project_ids=None, due_range=None):
        q = (
            db.session.query(Task, Project, Phase)
            .join(ProjectPhase, Task.project_phase_id == ProjectPhase.id)
            .join(Project, ProjectPhase.project_id == Project.id)
            .join(Phase, ProjectPhase.phase_id == Phase.id)

            .filter(Task.assigned_to == current_user.id)
        )

        if search:
            q = q.filter(Task.title.ilike(f"%{search}%"))

        if statuses:
            q = q.filter(Task.status.in_(statuses))

     

        if project_ids:
            q = q.filter(Project.id.in_(project_ids))

      

        q = q.order_by(Task.due_date.asc().nulls_last())
        rows = []
        import logging
        logging.warning(q.all())
        for t, p, ph in q.all():
            logging.warning((t.assigned_to))
            logging.warning((BimUsers.query.get( t.assigned_to).name))

            rows.append(
                {
                    "id": t.id,
                    "status": t.status or "-",
                    "project_name": p.name,
                    "phase_name": ph.name,
                    "due_date": t.due_date.isoformat() if getattr(t, "due_date", None) else None,
                    "assigned_to": BimUsers.query.get( t.assigned_to).name  if BimUsers.query.get( t.assigned_to) else None,
                    "assigned_by": BimUsers.query.get( t.assigned_by).name  if BimUsers.query.get( t.assigned_by) else None

                    

                }
            )
        return rows

    def _get_project_options(self):
        if self._project_options is not None:
            return self._project_options

        q = (
            db.session.query(Project.id, Project.name)
            .join(ProjectPhase, Project.id == ProjectPhase.project_id)
            .join(Task, Task.project_phase_id == ProjectPhase.id)
            .filter(Task.assigned_to == current_user.id)
            .distinct()
            .order_by(Project.name.asc())
        )
        self._project_options = [{"label": name, "value": pid} for pid, name in q.all()]
        return self._project_options

  
    def register_callbacks(self):
        @self.app.callback(
            Output("ut-project", "options"),
            Input("ut-project", "id"),  # mount
            prevent_initial_call=False,
        )
        def _populate_projects(_):
            self._project_options = None
            return self._get_project_options()

        @self.app.callback(
            Output("ut-grid", "rowData"),
            Input("ut-status", "value"),
            Input("ut-project", "value"),
            Input("ut-reset", "nClicks"),
            prevent_initial_call=False,
        )
        def _load_rows( statuses, project_ids,  reset_clicks):
            ctx = getattr(__import__("dash"), "ctx", None)
            trigger = getattr(ctx, "triggered_id", None) if ctx else None
            if trigger == "ut-reset":
                return self._query_tasks()

            return self._query_tasks(
                statuses=statuses or [],
                project_ids=project_ids or [],
            )

    