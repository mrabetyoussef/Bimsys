import dash_bootstrap_components as dbc
from dash import html , ctx , ALL ,callback_context
from sqlalchemy.orm import joinedload
from database.model import ProjectPhase as dbProjectPhase, Phase as dbPhase , Task as dbTask , BimUsers as dbBimusers , CustomTask, StandardTask     , Workload 
from database.db import db
from dash import html, dcc, Input, Output, State, callback_context , no_update
from datetime import datetime
from datetime import date, timedelta
from collections import defaultdict
import logging
import feffery_antd_components as fac
logging.basicConfig(
    level=logging.DEBUG,  # Enables debug-level logs
    format='[%(levelname)s] %(asctime)s - %(name)s - %(message)s'
)

logger = logging.getLogger(__name__)
logger.debug("This is a debug message")

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
                                dbc.Col(html.H4(f"Phasesss : {phase.name}", className="mb-0")),
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
                    self.add_task_modal(project_phase)
                ])
            ])
        ], fluid=True)


    def get_weeks_number(self,project_phase) :
        if project_phase.start_date and project_phase.end_date and project_phase.start_date < project_phase.end_date : 
            current = project_phase.start_date - timedelta(days=project_phase.start_date.weekday())
            lundis = []

            while current <= project_phase.end_date:
                lundis.append(current)
                current += timedelta(weeks=1)

            return (lundis)




    def construire_calendrier_dash(self, project_phase):
        
        lundis = self.get_weeks_number(project_phase)
        print(lundis)
        if lundis and project_phase.days_budget and project_phase.start_date and project_phase.end_date :
            nb_semaines = len(lundis)



            # Lignes d'en-têtes
            ligne_dates = html.Tr([html.Th("Date")] + [html.Th(lundi.strftime("%d/%m")) for lundi in lundis])
            ligne_jours = html.Tr([html.Td("Jour")] + [html.Td("Lun") for _ in lundis])
            ligne_semaines = html.Tr([html.Td("Semaine")] + [html.Td(str(lundi.isocalendar()[1])) for lundi in lundis])

            lignes = [ligne_dates, ligne_jours, ligne_semaines]

            logging.debug(f"nb_semaines : {(nb_semaines)}")
            logging.debug(f"project_phase.days_budget : {(project_phase.days_budget)}")

            if nb_semaines:
                charge_hebdo = round(project_phase.days_budget / nb_semaines, 2)
                ligne_charge = html.Tr([html.Td("Charge")] + [html.Td(str(charge_hebdo)) for _ in lundis])
                lignes.append(ligne_charge)

            # Regrouper les tâches par semaine
            semaine_tasks = defaultdict(list)
            for task in (project_phase.tasks or []):
                if task.due_date:
                    for idx, lundi in enumerate(lundis):
                        dimanche = lundi + timedelta(days=6)
                        if lundi <= task.due_date <= dimanche:
                            semaine_tasks[idx].append(task)
                            break

            # Trouver le nombre maximum de tâches dans une semaine
            max_tasks_in_week = max((len(tlist) for tlist in semaine_tasks.values()), default=0)

            # Générer les lignes par index de tâche (task[0], task[1], ...)
            for task_index in range(max_tasks_in_week):
                row = [html.Td(f"Tâches" if task_index==0 else "")]
                for week_idx in range(nb_semaines):
                    tasks = semaine_tasks.get(week_idx, [])
                    if task_index < len(tasks):
                        task = tasks[task_index]
                        cercle_id = f"cp_{task.id}"
                        task_info = dbc.ListGroup([
                            dbc.ListGroupItem(f"Nom : {task.name}" ),
                            dbc.ListGroupItem(f"Description : {task.description or ''}"),
                            dbc.ListGroupItem(f"Statut : {task.status or 'N/A'}"),
                            dbc.ListGroupItem(f"Assigné à : {task.assigned_to or 'N/A'}"),
                            ])
                        status_color = {
                            "À faire": "#007bff",     # Bleu
                            "En cours": "#ffc107",    # Jaune (par exemple)
                            "Terminée": "#2c5524",    # Vert foncé
                            "Urgente": "#dc3545"      # Rouge, si utile
                        }

                        cercle = html.Div([
                            html.Div(id=cercle_id, style={
                                "width": "12px",
                                "height": "12px",
                                "borderRadius": "50%",
                                "backgroundColor": status_color.get(task.status, "#6c757d"),  # Gris par défaut
                                "display": "inline-block",
                                "margin": "auto"
                            }),
                            dbc.Tooltip(target=cercle_id, children=task_info, placement="top",style={"color":"grey"})
                        ])
                        row.append(html.Td(cercle))
                    else:
                        row.append(html.Td(""))  
                lignes.append(html.Tr(row))

            table = html.Table(
                lignes,
                className="table table-bordered",
                style={"minWidth": f"{len(lundis)*70}px", "textAlign": "center"}
            )

            return dbc.Row(dbc.Col(html.Div(table)), className="mb-4")



    def add_task_modal(self,project_phase):
        standard_tasks = StandardTask.query.all()
        standard_tasks_options =         [ {"label": u.name, "value": u.id} for u in standard_tasks  ]
        bim_users = dbBimusers.query.filter(dbBimusers.role == "BIM MANAGER").all()
        options=[ {"label": u.name, "value": u.id} for u in bim_users  ]

        st_task_ui =  html.Div([dbc.Label("Nom"),

            dbc.Select(    
                        id="input-standrd-task",
                        options=standard_tasks_options,
                        placeholder="Choisir une tâche",
                        className="mb-3"    
                    ),
            dbc.Label("assigné à "),
            dbc.Select(    
                id="input-task-bim-manager",
                options=options,                
                className="mb-3" ,
                placeholder="Assigner à "   
            ),
            dbc.Label("Échéance"),
                dbc.Input(id="standard-task-due-date", type="date", className="mb-3",
                              min = project_phase.start_date if project_phase.start_date else None,
                           max = project_phase.end_date if project_phase.start_date else None),])
        
        costum_task_ui =  html.Div([
            dbc.Label("Nom"),
                dbc.Input(id="costum-task-name", type="text", className="mb-3"),
            dbc.Label("Description"),
                dbc.Input(id="costum-task-description", type="text", className="mb-3"),
            dbc.Label("Nombre de jours estimés"),
                dbc.Input(id="costum-task-estimated-days", type="number", className="mb-3"),
            dbc.Label("assigné à "),
            dbc.Select(    
                id="input-task-bim-manager",
                options=options,                
                className="mb-3" ,
                placeholder="Assigner à "   
            ),
            dbc.Label("Échéance"),
                dbc.Input(id="costum-task-due-date", type="date", className="mb-3",
                            min = project_phase.start_date if project_phase.start_date else None,
                           max = project_phase.end_date if project_phase.start_date else None ),])


        return dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle("Ajouter une tâche")),
            dbc.ModalBody([
                dbc.Tabs(
                    [
                        dbc.Tab(st_task_ui, label="Tâche standard"),
                        dbc.Tab(costum_task_ui, label="Tâche Personalisé"),
                    ]
                    )
           
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
                    self.task_ui(task)
                )
                for task in project_phase.tasks
            ]
        else:
            task_cards = [html.P("Aucune tâche liée à cette phase.", className="text-muted")]

        return html.Div(task_cards)

    def task_ui(self, task):
        return dbc.Row(
            [
                dbc.Col(
                    html.A(
                        dbc.Card(
                            dbc.CardBody([
                                dbc.Row([
                                    dbc.Col(
                                        [
                                             dbc.Col(
                                            html.Strong(task.name, className="card-title mb-1"),), 
                                         dbc.Col(
                                        
                                            fac.AntdTag(
                                                        content=f"{task.parent_task.estimated_days} jrs ",
                                                        color='magenta',
                                                        bordered=False,
                                                    ),
                                    ),],
                                        width=100
                                    ),
                                  
                                ], align="center", className="mb-2"),


                                 dbc.Row([
                                    dbc.Col(
                                       html.P(
                                        f"Échéance : {task.due_date.strftime('%Y-%m-%d') if task.due_date else 'Non définie'}",
                                        className="card-text mb-0"
                                    ),
                                    style={"fontSize": "0.9rem", "color": "#6c757d"}
                                    ),
                                    dbc.Col(
                                      
                                             dbc.Badge(task.status, color="secondary", className="float-end"),
                                        width="auto",
                                        className="text-end"    


                                    ),
                                ], align="center", className="mb-2"),

                            
                            ]),
                            className="card-hover",
                            style={
                                "cursor": "pointer",
                                "boxShadow": "0px 4px 6px rgba(0, 0, 0, 0.1)",
                                "marginBottom": "20px",
                                "width": "100%",
                            }
                        ),
                        href=f"/BIMSYS/task/{task.id}",
                        style={"textDecoration": "none", "color": "inherit"}
                    ),
                    width=True
                ),

                # Colonne pour le bouton (en dehors de la carte, à droite)
                dbc.Col(
                    dbc.DropdownMenu(
                        label=html.I(className="fas fa-ellipsis-vertical"),
                        class_name="dropdown-hover",
                        caret=False,
                        toggle_style={
                            "padding": "0",
                            "border": "none",
                            "background": "transparent",
                            "color": "grey",
                            "fontSize": "1.2rem"
                        },
                        children=[
                            dbc.DropdownMenuItem("Supprimer", id={"type": "delete-task-btn", "index": task.id}),
                        ],
                        direction="left",
                        size="sm",
                    ),
                    width="auto",
                    className="d-flex align-items-start justify-content-end",
                    style={"paddingTop": "8px"}
                )
            ],
            align="start",
            className="mb-2"
        )


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
            dbc.Input(type="text", value=str(len(self.get_weeks_number(project_phase)) if self.get_weeks_number(project_phase) else None), disabled=True, className="mb-3"),
            dbc.Label("répartition par semaine"),
            dbc.Input(type="text", 
                      value=str(self.calculate_weekly_partition(project_phase)), 
                      disabled=True, 
                      className="mb-3",
                      id="weekly-partition"),
            dbc.Label("Bim Manager"),

            dbc.Select(    
                        id="input-phase-bim-manager",
                        options=options,
                        value=project_phase.assigned_bimuser.id if project_phase.assigned_bimuser else "None" ,
                        className="mb-3"    
                    ),

            dbc.Label("Budget en jours des tâches"),
            dbc.Input(id="input-task-days-budget", type="number", value=project_phase.tasks_days_budget, className="mb-3",disabled=True),
            dbc.Label("Budget en jours  adittionnel"),
            dbc.Input(id="input-costum-days-budget", type="number", value=project_phase.costum_days_budget, className="mb-3"),
            dbc.Label("Budget en nombre de jours"),
            dbc.Input(id="input-phase-days-budget", type="number", value=project_phase.days_budget, className="mb-3",disabled=True),

            dbc.Label("Budget en euros"),
            dbc.Input(id="input-phase-euros-budget", type="number", value=project_phase.euros_budget, className="mb-3"),

            dbc.Label("Nombre de tâches associées"),
            dbc.Input(type="number", value=len(project_phase.tasks), disabled=True, className="mb-3"),
        ])

    def calculate_weekly_partition(self, project_phase):
        try :
            return round(project_phase.days_budget/len(self.get_weeks_number(project_phase)),2)if self.get_weeks_number(project_phase) and project_phase.days_budget else None
        except:
            return no_update

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
    Output("tasks-display", "children", allow_duplicate=True),
    Output("phase-calendar-container", "children", allow_duplicate=True),
    Output("input-task-days-budget","value"),
    Output("input-phase-days-budget", "value", allow_duplicate=True),
    Output("costum-task-estimated-days", "value"),
    Output("costum-task-description", "value"),
    Output("costum-task-name", "value"),
    Output("input-task-bim-manager", "value"),
    Output("input-standrd-task", "value"),
    Output("standard-task-due-date", "value"),
    Output("costum-task-due-date", "value"),

    Input("submit-task", "n_clicks"),
    Input({"type": "delete-task-btn", "index": ALL}, "n_clicks"),
    [
        State("costum-task-estimated-days", "value"),
        State("costum-task-description", "value"),
        State("costum-task-name", "value"),
        State("input-task-bim-manager", "value"),
        State("input-standrd-task", "value"),
        State("standard-task-due-date", "value"),
        State("costum-task-due-date", "value"),
        State("url", "pathname"),
    ],
    prevent_initial_call=True
)
        def handle_task_actions(
            submit_click,
            delete_clicks,
            estimated_days,
            custom_description,
            custom_name,
            assigned_to_id,
            standard_task_id,
            standard_task_due_date,
            custom_task_due_date,
            pathname
        ):
            import re
            from datetime import datetime
            from dash import no_update

            triggered = ctx.triggered_id
            logging.debug("Action déclenchée par : %s", triggered)

            if isinstance(triggered, dict) and triggered.get("type") == "delete-task-btn":
                task_id = triggered.get("index")
                task_to_delete = db.session.query(dbTask).get(task_id)
                if task_to_delete:
                    db.session.delete(task_to_delete)
                    try :
                        project_phase = dbProjectPhase.query.get(self.project_phase_id)
                        project_phase.tasks_days_budget = sum([t.parent_task.estimated_days for t in project_phase.tasks if t.parent_task.estimated_days is not None])
                        project_phase.days_budget = (project_phase.costum_days_budget if project_phase.costum_days_budget else 0) +  project_phase.tasks_days_budget
                    except :
                        pass
                    db.session.commit()
                    logging.info("Tâche supprimée : ID %s", task_id)

                else:
                    logging.warning("Tâche à supprimer introuvable : ID %s", task_id)

                return (self.get_project_phase_tasks(project_phase),
                        self.construire_calendrier_dash(project_phase),
                        project_phase.tasks_days_budget,
                        project_phase.days_budget,None,None,None,None,None,None,None)

            # 🔻 Cas ajout
            if submit_click:
                match = re.search(r"/phase/([a-zA-Z0-9]+)", pathname)
                if not match:
                    logging.warning("Phase ID non trouvée dans l'URL : %s", pathname)
                    return no_update, no_update, no_update, no_update,None,None,None,None,None,None,None,None

                phase_id = match.group(1)
                project_phase = dbProjectPhase.query.get(phase_id)
                if not project_phase:
                    logging.warning("Aucune phase trouvée pour ID : %s", phase_id)
                    return no_update, no_update , no_update, no_update,None,None,None,None,None,None,None,None

                # Tâche standard
                if standard_task_id:
                    standard_task = StandardTask.query.get(standard_task_id)
                    if not standard_task:
                        logging.error("StandardTask introuvable pour ID %s", standard_task_id)
                        return no_update, no_update , no_update, no_update,None,None,None,None,None,None,None,None

                    due_date = None
                    if standard_task_due_date:
                        try:
                            due_date = datetime.strptime(standard_task_due_date, "%Y-%m-%d")
                        except ValueError:
                            logging.error("Date invalide pour tâche standard : %s", standard_task_due_date)
                            return no_update, no_update , no_update, no_update,None,None,None,None,None,None,None,None

                    task = dbTask(
                        due_date=due_date,
                        project_phase_id=phase_id,
                        assigned_to=assigned_to_id,
                        standard_task=standard_task
                    )
                    logging.info("Ajout tâche standard : %s", task)

                # Tâche personnalisée
                elif custom_task_due_date and estimated_days and custom_description and custom_name:
                    try:
                        due_date = datetime.strptime(custom_task_due_date, "%Y-%m-%d")
                    except ValueError:
                        logging.error("Date invalide pour tâche personnalisée : %s", custom_task_due_date)
                        return no_update, no_update , no_update, no_update,None,None,None,None,None,None,None,None

                    ct = CustomTask(
                        custom_name=custom_name,
                        custom_description=custom_description,
                        estimated_days=estimated_days
                    )
                    task = dbTask(
                        due_date=due_date,
                        project_phase_id=phase_id,
                        assigned_to=assigned_to_id,
                        custom_task=ct
                    )
                    values = [project_phase.tasks_days_budget, ct.estimated_days]
                    project_phase.tasks_days_budget = sum(v for v in values if v is not None)
                    logging.info("Ajout tâche personnalisée : %s", task)
                else:
                    logging.warning("Champs manquants pour création de tâche.")
                    return no_update, no_update , no_update, no_update,None,None,None,None,None,None,None,None

                # Enregistrement
                try:
                    db.session.add(task)
                    project_phase.tasks_days_budget = sum([t.parent_task.estimated_days for t in project_phase.tasks])
                    project_phase.days_budget = project_phase.costum_days_budget +  project_phase.tasks_days_budget

                    db.session.commit()
                except Exception as e:
                    logging.exception("Erreur en enregistrant la tâche")
                    db.session.rollback()
                    return no_update, no_update , no_update, no_update

                # Rafraîchir les composants
                updated_phase = dbProjectPhase.query.get(phase_id)

                return (self.get_project_phase_tasks(updated_phase), 
                        self.construire_calendrier_dash(project_phase=updated_phase),
                        updated_phase.tasks_days_budget,
                        project_phase.days_budget,None,None,None,None,None,None,None)

            return no_update, no_update , no_update, no_update,None,None,None,None,None,None,None




        @self.app.callback(
        Output("delete-phase-dummy", "children"), 
        Output("phase-calendar-container", "children", allow_duplicate=True),
        Output("input-phase-days-budget", "value", allow_duplicate=True),
        Output("input-phase-euros-budget", "value"),
        Output("weekly-partition", "value"),
        Output("input-costum-days-budget", "value"),



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
        def update_phase_data(start_date, end_date, days_budget, euros_budget, bim_manager_id, costum_days_budget):
            
            project_phase = dbProjectPhase.query.get(self.project_phase_id)
            if project_phase :
                
                ctx = callback_context.triggered_id

                if "input-costum-days-budget" in ctx : 
                    taj= project_phase.assigned_bimuser.taj 
                    project_phase.costum_days_budget = costum_days_budget
                    project_phase.days_budget = costum_days_budget +  project_phase.tasks_days_budget
                    project_phase.euros_budget = (project_phase.costum_days_budget * taj ) + (taj *   project_phase.tasks_days_budget)
                    db.session.commit()
                    return "" , self.construire_calendrier_dash(project_phase=project_phase) , project_phase.days_budget , project_phase.euros_budget  , self.calculate_weekly_partition(project_phase) , no_update





                if "input-phase-start-date" in ctx : 
                    try:
                        if start_date:
                            project_phase.start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
                    except Exception:
                        pass
                    db.session.commit()
                    if  bim_manager_id and start_date and end_date:
                        Workload.update_workload(project_phase)
                    return "" , self.construire_calendrier_dash(project_phase=project_phase) , no_update , no_update , self.calculate_weekly_partition(project_phase), no_update
                

                if "input-phase-end-date" in ctx : 
                    try:
                        if end_date:
                            project_phase.end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
                            db.session.commit()

                    except Exception:
                        pass
                    if  bim_manager_id and start_date and end_date:
                        Workload.update_workload(project_phase)
                    return "" , self.construire_calendrier_dash(project_phase=project_phase), no_update , no_update,self.calculate_weekly_partition(project_phase),no_update
                
                if "input-phase-days-budget" in ctx : 
            
                    if days_budget is not None:
                        project_phase.days_budget = days_budget
                        if project_phase.assigned_bimuser : 
                            project_phase.euros_budget = days_budget * project_phase.assigned_bimuser.taj
                            db.session.commit()
                        if  bim_manager_id and start_date and end_date:
                            Workload.update_workload(project_phase)
                        return "" , self.construire_calendrier_dash(project_phase=project_phase), no_update , project_phase.euros_budget,self.calculate_weekly_partition(project_phase), no_update
                    
                if "input-phase-euros-budget" in ctx : 
                    if euros_budget is not None:
                        project_phase.euros_budget = euros_budget
                        if project_phase.assigned_bimuser : 
                            euro_budget_left = project_phase.euros_budget - (project_phase.tasks_days_budget * project_phase.assigned_bimuser.taj )
                            

                            project_phase.costum_days_budget =  euro_budget_left / project_phase.assigned_bimuser.taj
                            db.session.commit()
                    if  bim_manager_id and start_date and end_date:
                        Workload.update_workload(project_phase)
                    return "" , self.construire_calendrier_dash(project_phase=project_phase), project_phase.days_budget , no_update,self.calculate_weekly_partition(project_phase),project_phase.costum_days_budget



                
                if "input-phase-bim-manager" in ctx : 
                    if bim_manager_id:                        
                        project_phase.assigned_bimuser_id = bim_manager_id
                        project_phase.euros_budget = project_phase.days_budget * project_phase.assigned_bimuser.taj
                        db.session.commit()
                        if  bim_manager_id and start_date and end_date:
                            Workload.update_workload(project_phase)
                        return "" , no_update, no_update, project_phase.euros_budget,self.calculate_weekly_partition(project_phase), no_update

              
                return no_update , no_update , no_update , no_update,no_update,no_update
            else :
                raise "probleme dans la phase"
            
        # @self.app.callback(
        #     Output("tasks-display", "children", allow_duplicate=True),  
        #     Input({"type": "delete-task-btn", "index": ALL}, "n_clicks"),
        #     prevent_initial_call=True
        # )
        # def delete_task(n_clicks_list):

        #     triggered = ctx.triggered_id
        #     if "delete-task-btn" in triggered:
        #         task_id = triggered["index"]
        #         # Suppression de la tâche dans la base de données
        #         task_to_delete = db.session.query(dbTask).get(task_id)
        #         if task_to_delete:
        #             db.session.delete(task_to_delete)
        #             db.session.commit()

        #         # Rechargement des tâches restantes
        #         project_phase = dbProjectPhase.query.get(self.project_phase_id)

        #         return self.get_project_phase_tasks(project_phase)