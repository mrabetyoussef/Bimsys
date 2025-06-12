import dash_bootstrap_components as dbc
from dash import html
from sqlalchemy.orm import joinedload
from database.model import ProjectPhase as dbProjectPhase, Phase as dbPhase , Task as dbTask , BimUsers as dbBimusers
from database.db import db
from dash import html, dcc, Input, Output, State, callback_context , no_update
from datetime import datetime
from datetime import date, timedelta

class Phase:
    def __init__(self, app):
        self.app = app
        self.register_callback()

    def layout(self, project_phase_id):
        self.project_phase_id = project_phase_id
        project_phase = dbProjectPhase.query.get(project_phase_id)
        if not project_phase:
            return dbc.Alert("Phase introuvable.", color="danger")

        phase = project_phase.phase
        if not phase:
            return dbc.Alert("Détail de la phase indisponible.", color="warning")

        return dbc.Container([
            dbc.Row([
                # === Colonne Phase ===
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader(
                            dbc.Row([
                                dbc.Col(html.H4(f"Phase : {phase.name}", className="mb-0")),
                                dbc.Col(
                                    dbc.Button(
                                        html.I(className="fa fa-trash"),
                                        color="outline-danger",
                                        id="delete-phase-button",
                                        title="Supprimer la phase"
                                    ),
                                    width="auto",
                                    className="text-end"
                                ),
                                html.Div(id="delete-phase-dummy"),
                                self.delete_phase_modal()
                            ], align="center")
                        ),
                        dbc.CardBody(self.phase_info(project_phase)),
                        dcc.Location(id="redirect", refresh=True),
                    ], style={"margin": "20px"}),

                    # === Calendrier sous la colonne Phase ===
                    dbc.Card([
                        dbc.CardHeader(html.H5("Calendrier des semaines")),
                        dbc.CardBody(
                            html.Div(
                                self.construire_calendrier_dash(project_phase),
                                style={
                                    "overflowX": "auto",
                                    "whiteSpace": "nowrap",
                                    "border": "1px solid #ddd",
                                    "padding": "10px"
                                } , id='phase-calendar-container'
                            )
                        )
                    ], style={"margin": "20px"})
                ], width=4),

                # === Colonne Tâches liées ===
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader(
                            dbc.Row([
                                dbc.Col(html.H4("Tâches liées", className="mb-0")),
                                dbc.Col(
                                    dbc.Button(
                                        html.I(className="fa fa-plus"),
                                        color="outline-primary",
                                        id="add-project-task",
                                        title="Ajouter une tâche"
                                    ),
                                    width="auto",
                                    className="text-end"
                                )
                            ], align="center")
                        ),
                        dbc.CardBody(
                            children=self.get_project_phase_tasks(project_phase),
                            id='tasks-display'
                        )
                    ], style={"margin": "20px"}),
                    self.add_task_modal()
                ])
            ])
        ], fluid=True)


    def get_weeks_number(self,project_phase) :
        current = project_phase.start_date - timedelta(days=project_phase.start_date.weekday())
        lundis = []

        while current <= project_phase.end_date:
            lundis.append(current)
            current += timedelta(weeks=1)

        return (lundis)

    def construire_calendrier_dash(self,project_phase):

        lundis = self.get_weeks_number(project_phase)

        nb_semaines = len(lundis)

        ligne_dates = html.Tr(
            [html.Th("")] + [html.Th(lundi.strftime("%d/%m")) for lundi in lundis]
        )

        ligne_jours = html.Tr(
            [html.Td("sem")] + [html.Td("Lun") for _ in lundis]
        )

        ligne_semaines = html.Tr(
            [html.Td("")] + [html.Td(str(lundi.isocalendar()[1])) for lundi in lundis]
        )

        ligne_semaines = html.Tr(
            [html.Td("")] + [html.Td(str(lundi.isocalendar()[1])) for lundi in lundis]
        )
        if nb_semaines :
            charge_hebdo = round(project_phase.days_budget / nb_semaines, 2) 

            ligne_charge = html.Tr([html.Td("Charge")] + [
                html.Td(str(charge_hebdo)) for _ in lundis
            ])
        else: 
            ligne_charge = None


        tasks = project_phase.tasks or []
        ligne_cercles = html.Tr([html.Td("Tâches")])
        for lundi in lundis:
            dimanche = lundi + timedelta(days=6)

            # On récupère une tâche (la première) qui finit cette semaine
            tache_semaine = next(
                (task for task in tasks if task.due_date and lundi <= task.due_date <= dimanche),
                None
            )

            if tache_semaine:
                task_info =f"""
                        Nom de la tâche  : {tache_semaine.name}\n
                        description :{tache_semaine.description }\n
                        status :{tache_semaine.status }\n
                        assigned_to :{tache_semaine.assigned_to}\n

                """
                cercle_id = f"cp_{tache_semaine.id}"
                cercle = html.Div([
                    html.Div(id=cercle_id, style={
                        "width": "12px",
                        "height": "12px",
                        "borderRadius": "50%",
                        "backgroundColor": "#007bff",
                        "display": "inline-block",
                        "margin": "auto"
                    }),
                    dbc.Tooltip(
                        target=cercle_id,
                        children=task_info,
                        placement="top"
                    )
                ])
            else:
                cercle = ""

            ligne_cercles.children.append(
                html.Td(cercle, style={"color": "#007bff", "fontSize": "18px"})
            )



        lignes = [ligne_dates, ligne_jours, ligne_semaines]
        if ligne_charge:
            lignes.append(ligne_charge)
        lignes.append(ligne_cercles)

        table = html.Table(
            lignes,
            className="table table-bordered",
            style={"minWidth": f"{len(lundis)*70}px", "textAlign": "center"}
        )

        scrollable_container = html.Div(
            table,
          
        )

        return dbc.Row(
            dbc.Col(scrollable_container),
            className="mb-4"
        )



    def add_task_modal(self):
        return dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle("Ajouter une tâche")),
            dbc.ModalBody([
                dbc.Label("Nom de la tâche"),
                dbc.Input(id="task-name", type="text", className="mb-3"),

                dbc.Label("Description"),
                dbc.Textarea(id="task-desc", className="mb-3"),

                dbc.Label("Échéance"),
                dbc.Input(id="task-due-date", type="date", className="mb-3"),
            ]),
            dbc.ModalFooter([
                dbc.Button("Annuler", id="close-task-modal", color="secondary", className="me-2"),
                dbc.Button("Ajouter", id="submit-task", color="primary"),
            ])
        ], id="task-modal", is_open=False)

    def get_project_phase_tasks(self, project_phase):
        if project_phase.tasks:
            task_cards = [
                dbc.Row(
                    html.A(
                        dbc.Card(
                            dbc.CardBody([
                                dbc.Row([
                                    dbc.Col(html.H5(task.name, className="card-title"), width=8),
                                    dbc.Col(
                                        dbc.Badge(task.status, color="secondary", className="float-end"),
                                        width=4,
                                        className="text-end"
                                    )
                                ]),
                                html.P(f"Échéance : {task.due_date.strftime('%Y-%m-%d') if task.due_date else 'Non définie'}", className="card-text mb-0"),
                            ]),
                            className="card-hover",
                            style={
                                "cursor": "pointer",
                                "box-shadow": "0px 4px 6px rgba(0, 0, 0, 0.1)",
                                                        "margin-bottom": "20px",

                            }
                        ),
                        href=f"/BIMSYS/task/{task.id}",
                        style={"textDecoration": "none", "color": "inherit"}
                    )
                )
                for task in project_phase.tasks
            ]
        else:
            task_cards = [html.P("Aucune tâche liée à cette phase.", className="text-muted")]

        return html.Div(task_cards)



    def phase_info(self, project_phase):

        bim_users = dbBimusers.query.filter(dbBimusers.role == "BIM MANAGER").all()
        options=[ {"label": u.name, "value": u.id} for u in bim_users  ]
        options.append( {"label": "None", "value":"None"} )
        return html.Div([
            dbc.Label("Projet associé"),
            dbc.Input(type="text", value=project_phase.project_parent.name, disabled=True, className="mb-3"),

            dbc.Row([
                dbc.Col([
                    dbc.Label("Date de début"),
                    dbc.Input(type="date", value=str(project_phase.start_date), id="input-phase-start-date", className="mb-3")
                ]),
                dbc.Col([
                    dbc.Label("Date de fin"),
                    dbc.Input(type="date", value=str(project_phase.end_date), id="input-phase-end-date", className="mb-3")
                ])
            ]),

            dbc.Label("Durée (sem.)"),
            dbc.Input(type="text", value=str(len(self.get_weeks_number(project_phase))), disabled=True, className="mb-3"),
            dbc.Label("répartition par semaine"),
            dbc.Input(type="text", value=str(round(project_phase.days_budget/len(self.get_weeks_number(project_phase)),2)), disabled=True, className="mb-3"),
            dbc.Label("Bim Manager"),

            dbc.Select(    
                        id="input-phase-bim-manager",
                        options=options,
                        value=project_phase.assigned_bimuser.id if project_phase.assigned_bimuser else "None" ,
                        className="mb-3"    
                    ),

            dbc.Label("Budget en nombre de jours"),
            dbc.Input(id="input-phase-days-budget", type="number", value=project_phase.days_budget, className="mb-3"),

            dbc.Label("Budget en euros"),
            dbc.Input(id="input-phase-euros-budget", type="number", value=project_phase.euros_budget, className="mb-3"),

            dbc.Label("Nombre de tâches associées"),
            dbc.Input(type="number", value=len(project_phase.tasks), disabled=True, className="mb-3"),
        ])


    def delete_phase_modal(self):
        """
        Crée et retourne un modal Dash pour confirmer la suppression d'une phase.
        """
        modal = dbc.Modal(
            [
                dbc.ModalHeader(
                    dbc.ModalTitle("Supprimer la phase"),
                    close_button=True,
                ),

                dbc.ModalBody(
                    dbc.Row(
                        [
                            dbc.Col(
                                html.I(
                                    className="fas fa-exclamation-triangle fa-2x text-warning",
                                    title="Attention"
                                ),
                                width="auto"
                            ),
                            dbc.Col(
                                html.P(
                                    "La phase et ses données seront supprimées définitivement. Voulez-vous confirmer ?",
                                    className="mb-0"
                                ),
                                className="ms-3"
                            ),
                        ],
                        className="align-items-center"
                    )
                ),

                dbc.ModalFooter(
                    [
                        dbc.Button(
                            "Annuler",
                            id="cancel-delete-phase-button",
                            color="secondary",
                            outline=True,
                        ),
                        dbc.Button(
                            "Valider",
                            id="validate-delete-phase-button",
                            color="danger",
                            className="ms-2",
                        ),
                    ]
                ),
            ],
            id="delete-phases-modal",
            centered=True,
            backdrop="static",
            is_open=False,
        )

        return modal
    
    def get_project_phase(self, project_phase_id):

        """Charge un ProjectPhase avec sa Phase associée."""
        return dbProjectPhase.query.options(
            joinedload(dbProjectPhase.phase)
        ).filter_by(id=project_phase_id).first()
    
    def register_callback(self):
        @self.app.callback(
            [
                Output("delete-phases-modal", "is_open"),
                Output("redirect", "pathname"),
            ],
            [
                Input("delete-phase-button",        "n_clicks"),
                Input("cancel-delete-phase-button", "n_clicks"),
                Input("validate-delete-phase-button","n_clicks"),
            ],
            [
                State("delete-phases-modal", "is_open"),
            ],
            prevent_initial_call=True,
        )
        def delete_phase(n_open, n_cancel, n_validate, is_open):
            ctx = callback_context.triggered_id

            if ctx == "delete-phase-button":
                return True, no_update

            # 2) “Annuler” → just close modal
            if ctx == "cancel-delete-phase-button":
                return False, no_update

            # 3) “Valider” → delete from DB, then close & redirect
            if ctx == "validate-delete-phase-button":
                pp = dbProjectPhase.query.get(self.project_phase_id)
                print(pp)
                if pp:
                    parent_id = pp.project_id
                    print(parent_id)
                    db.session.delete(pp)
                    db.session.commit()
                    # close modal (False) and go to /project/<parent_id>
                    return False, f"BIMSYS//project/{parent_id}"
                # if somehow not found, just close
                return False, no_update

            # fallback (shouldn't happen)
            return is_open, no_update
        @self.app.callback(
            Output("task-modal", "is_open"),
            [Input("add-project-task", "n_clicks"), Input("close-task-modal", "n_clicks"), Input("submit-task", "n_clicks")],
            [State("task-modal", "is_open")]
        )
        def toggle_task_modal(open_click, close_click, submit_click, is_open):
            if open_click or close_click or submit_click:
                return not is_open
            return is_open
        

        @self.app.callback(
            # Output("redirect", "pathname", allow_duplicate=True),  # Pour forcer le refresh ou rediriger
            Output("tasks-display", "children"),  

            Input("submit-task", "n_clicks"),
            [
                State("task-name", "value"),
                State("task-desc", "value"),
                State("task-due-date", "value"),
                State("url", "pathname")  # récupère l'ID de la phase depuis l'URL
            ],
            prevent_initial_call=True
        )
        def add_task(n_clicks, name, desc, due_date, pathname):
            import re
            from datetime import datetime
            if not name:
                raise no_update

            match = re.search(r"/phase/([a-zA-Z0-9]+)", pathname)
            if not match:
                raise no_update


            phase_id = match.group(1)
            project_phase = dbProjectPhase.query.get(phase_id)
            if not project_phase:
                raise no_update


            task = dbTask(
                name=name,
                description=desc,
                due_date=datetime.strptime(due_date, "%Y-%m-%d") if due_date else None,
                project_phase_id=phase_id
            )

            db.session.add(task)
            db.session.commit()

            return self.get_project_phase_tasks(project_phase)


        @self.app.callback(
        Output("delete-phase-dummy", "children"), 
         Output("phase-calendar-container", "children"), 
        [
            Input("input-phase-start-date", "value"),
            Input("input-phase-end-date", "value"),
            Input("input-phase-days-budget", "value"),
            Input("input-phase-euros-budget", "value"),
            Input("input-phase-bim-manager", "value"),
        ],
        prevent_initial_call=True
)
        def update_phase_data(start_date, end_date, days_budget, euros_budget, bim_manager_id):
            project_phase = dbProjectPhase.query.get(self.project_phase_id)
           
            try:
                if start_date:
                    project_phase.start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
            except Exception:
                pass

            try:
                if end_date:
                    project_phase.end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
            except Exception:
                pass

            if days_budget is not None:
                project_phase.days_budget = days_budget
                # db.session.commit()
                # return "" , self.construire_calendrier_dash(project_phase=project_phase)
                
            if euros_budget is not None:
                project_phase.euros_budget = euros_budget

            if bim_manager_id:
                project_phase.assigned_bimuser_id = bim_manager_id
            db.session.commit()

            return "" , self.construire_calendrier_dash(project_phase=project_phase)
