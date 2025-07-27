import dash_bootstrap_components as dbc
from dash import html, Input, Output, State, callback_context, dcc, no_update, ALL, MATCH
from flask import current_app
from database.model import StandardTask
from database.db import db

class StandardTaskView:
    def __init__(self, app):
        self.app = app
        self.register_callbacks()

    def layout(self):
        with current_app.app_context():
            tasks = StandardTask.query.order_by(StandardTask.id.desc()).all()

        return dbc.Container([
            # Header section avec style moderne
            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.H2("Gestion des tâches standard", 
                               className="mb-0 text-primary fw-bold"),
                        html.P("Gérez vos tâches standards et leurs paramètres", 
                               className="text-muted mb-0")
                    ], className="d-flex flex-column")
                ], width=8),
                dbc.Col([
                    dbc.Button([
                        html.I(className="fas fa-plus me-2"),
                        "Nouvelle tâche"
                    ], 
                    id="add-std-task", 
                    color="primary", 
                    className="float-end shadow-sm",
                    style={"borderRadius": "8px"})
                ], width=4, className="align-items-center mb-4")
            ], className="mb-4 pb-3 border-bottom"),

            # Stores pour la gestion des états
            dcc.Store(id="editing-task-ids", data=[]),
            dcc.Store(id="temp-task-ids", data=[]),  # Pour les tâches temporaires
            dcc.Store(id="deleted-task-id"),

            # Zone d'affichage des tâches
            html.Div(id="std-task-container", children=[
                self.render_task_list(tasks, [])
            ]),

            # Modal de confirmation de suppression
            dbc.Modal([
                dbc.ModalHeader([
                    html.I(className="fas fa-exclamation-triangle text-warning me-2"),
                    "Confirmer la suppression"
                ]),
                dbc.ModalBody([
                    html.P("Êtes-vous sûr de vouloir supprimer cette tâche standard ?"),
                    html.Small("Cette action est irréversible.", className="text-muted")
                ]),
                dbc.ModalFooter([
                    dbc.Button("Annuler", id="cancel-delete", 
                             color="secondary", className="me-2"),
                    dbc.Button([
                        html.I(className="fas fa-trash me-2"),
                        "Supprimer"
                    ], id="confirm-delete", color="danger")
                ])
            ], id="delete-modal", is_open=False, centered=True, size="sm")
        ], fluid=True, className="py-4")

    def render_task_list(self, tasks, editing_ids, temp_ids=None):
        """Render la liste complète des tâches avec un style moderne"""
        if temp_ids is None:
            temp_ids = []
            
        if not tasks:
            return html.Div([
                html.Div([
                    html.I(className="fas fa-tasks fa-3x text-muted mb-3"),
                    html.H5("Aucune tâche standard", className="text-muted mb-2"),
                    html.P("Commencez par ajouter une nouvelle tâche standard.", 
                           className="text-muted")
                ], className="text-center py-5")
            ], className="border rounded bg-light")

        return html.Div([
            html.Div([
                self.render_task(task, 
                               is_editing=(task.id in editing_ids),
                               is_temp=(task.id in temp_ids)) 
                for task in tasks
            ], className="task-list")
        ])

    def render_task(self, task, is_editing=False, is_temp=False):
        """Render une tâche individuelle avec un design moderne"""
        if is_editing:
            return self.render_editing_task(task, is_temp)
        else:
            return self.render_display_task(task)

    def render_editing_task(self, task, is_temp=False):
        """Render une tâche en mode édition"""
        card_class = "border-primary shadow-sm" if is_temp else "border-info shadow-sm"
        header_color = "primary" if is_temp else "info"
        
        return dbc.Card([
            dbc.CardHeader([
                html.Div([
                    html.I(className=f"fas fa-edit me-2 text-{header_color}"),
                    html.Span("Nouvelle tâche" if is_temp else "Modification", 
                             className=f"fw-bold text-{header_color}")
                ])
            ], className="py-2"),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Nom de la tâche *", className="fw-semibold"),
                        dbc.Input(
                            id={"type": "std-name", "index": task.id},
                            value=task.name,
                            placeholder="Ex: Analyse des besoins",
                            className="mb-3"
                        )
                    ], width=8),
                    dbc.Col([
                        dbc.Label("Durée estimée (jours)", className="fw-semibold"),
                        dbc.Input(
                            id={"type": "std-days", "index": task.id},
                            value=task.estimated_days,
                            type="number",
                            min=0,
                            step=0.5,
                            placeholder="Ex: 2.5",
                            className="mb-3"
                        )
                    ], width=4)
                ]),
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Description", className="fw-semibold"),
                        dbc.Textarea(
                            id={"type": "std-desc", "index": task.id},
                            value=task.description or "",
                            placeholder="Décrivez cette tâche standard...",
                            rows=3,
                            className="mb-3"
                        )
                    ], width=12)
                ]),
                
                # Boutons d'action
                html.Hr(),
                dbc.Row([
                    dbc.Col([
                        dbc.ButtonGroup([
                            dbc.Button([
                                html.I(className="fas fa-check me-2"),
                                "Valider"
                            ], 
                            id={"type": "save-std-task", "index": task.id},
                            color="success",
                            className="shadow-sm"
                            ),
                            dbc.Button([
                                html.I(className="fas fa-times me-2"),
                                "Annuler"
                            ], 
                            id={"type": "cancel-edit-task", "index": task.id},
                            color="secondary",
                            outline=True,
                            className="shadow-sm"
                            )
                        ])
                    ], width=12, className="text-end")
                ])
            ])
        ], className=f"mb-3 {card_class}", style={"borderRadius": "10px"})

    def render_display_task(self, task):
        """Render une tâche en mode affichage"""
        return dbc.Card([
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.Div([
                            html.H5(task.name, className="mb-2 text-dark fw-semibold"),
                            html.P(task.description or "Aucune description", 
                                   className="text-muted mb-2 small"),
                            dbc.Badge([
                                html.I(className="fas fa-clock me-1"),
                                f"{task.estimated_days or 'Non définie'} jour(s)"
                            ], color="light", text_color="dark", className="border")
                        ])
                    ], width=10),
                    dbc.Col([
                        dbc.DropdownMenu([
                            dbc.DropdownMenuItem([
                                html.I(className="fas fa-edit me-2"),
                                "Modifier"
                            ], id={"type": "modify-task-btn", "index": task.id}),
                            dbc.DropdownMenuItem(divider=True),
                            dbc.DropdownMenuItem([
                                html.I(className="fas fa-trash me-2 text-danger"),
                                "Supprimer"
                            ], id={"type": "delete-task-btn", "index": task.id})
                        ],
                        label=html.I(className="fas fa-ellipsis-vertical"),
                        toggle_style={
                            "border": "none",
                            "background": "transparent",
                            "color": "#6c757d",
                            "padding": "0.25rem 0.5rem"
                        },
                        align_end=True,
                        className="float-end"
                        )
                    ], width=2, className="text-end")
                ])
            ])
        ], className="mb-3 shadow-sm border-0", 
           style={"borderRadius": "10px", "transition": "all 0.2s ease"})

    def register_callbacks(self):
        # Callback pour ajouter une nouvelle tâche
        @self.app.callback(
            Output("std-task-container", "children", allow_duplicate=True),
            Output("editing-task-ids", "data", allow_duplicate=True),
            Output("temp-task-ids", "data", allow_duplicate=True),
            Input("add-std-task", "n_clicks"),
            State("editing-task-ids", "data"),
            State("temp-task-ids", "data"),
            prevent_initial_call=True
        )
        def add_standard_task(n_clicks, editing_ids, temp_ids):
            if not n_clicks:
                return no_update, no_update, no_update
                
            # Créer une nouvelle tâche temporaire
            new_task = StandardTask(
                name="Nouvelle tâche", 
                description="", 
                estimated_days=None,
                category1='autre', 
                category2="autre"
            )
            db.session.add(new_task)
            db.session.commit()
            
            # Ajouter aux listes d'édition et temporaires
            editing_ids.append(new_task.id)
            temp_ids.append(new_task.id)
            
            # Récupérer toutes les tâches avec la nouvelle en premier
            other_tasks = StandardTask.query.filter(StandardTask.id != new_task.id).all()     
            all_tasks = [new_task] + other_tasks
      
            return self.render_task_list(all_tasks, editing_ids, temp_ids), editing_ids, temp_ids

        # Callback pour sauvegarder les modifications
        @self.app.callback(
            Output("std-task-container", "children", allow_duplicate=True),
            Output("editing-task-ids", "data", allow_duplicate=True),
            Output("temp-task-ids", "data", allow_duplicate=True),
            Input({"type": "save-std-task", "index": ALL}, "n_clicks"),
            State({"type": "std-name", "index": ALL}, "value"),
            State({"type": "std-desc", "index": ALL}, "value"),
            State({"type": "std-days", "index": ALL}, "value"),
            State({"type": "save-std-task", "index": ALL}, "id"),
            State("editing-task-ids", "data"),
            State("temp-task-ids", "data"),
            prevent_initial_call=True
        )
        def save_task_edits(n_clicks_list, names, descs, days_list, btn_ids, editing_ids, temp_ids):
            if not any(n_clicks_list):
                return no_update, no_update, no_update
                
            # Trouver quelle tâche a été sauvegardée
            saved_id = None
            for idx, (n_clicks, btn_id) in enumerate(zip(n_clicks_list, btn_ids)):
                if n_clicks:
                    task_id = btn_id["index"]
                    task = StandardTask.query.get(task_id)
                    if task and names[idx] and names[idx].strip():
                        task.name = names[idx].strip()
                        task.description = descs[idx] if descs[idx] else ""
                        try:
                            task.estimated_days = float(days_list[idx]) if days_list[idx] else None
                        except (ValueError, TypeError):
                            task.estimated_days = None
                        db.session.commit()
                        saved_id = task_id
                        break
            
            if saved_id:
                # Retirer de la liste d'édition et temporaire
                if saved_id in editing_ids:
                    editing_ids.remove(saved_id)
                if saved_id in temp_ids:
                    temp_ids.remove(saved_id)
            
            tasks = StandardTask.query.order_by(StandardTask.id.desc()).all()
            return self.render_task_list(tasks, editing_ids, temp_ids), editing_ids, temp_ids

        # Callback pour annuler l'édition
        @self.app.callback(
            Output("std-task-container", "children", allow_duplicate=True),
            Output("editing-task-ids", "data", allow_duplicate=True),
            Output("temp-task-ids", "data", allow_duplicate=True),
            Input({"type": "cancel-edit-task", "index": ALL}, "n_clicks"),
            State({"type": "cancel-edit-task", "index": ALL}, "id"),
            State("editing-task-ids", "data"),
            State("temp-task-ids", "data"),
            prevent_initial_call=True
        )
        def cancel_task_edit(n_clicks_list, btn_ids, editing_ids, temp_ids):
            if not any(n_clicks_list):
                return no_update, no_update, no_update
                
            # Trouver quelle tâche a été annulée
            cancelled_id = None
            for idx, (n_clicks, btn_id) in enumerate(zip(n_clicks_list, btn_ids)):
                if n_clicks:
                    cancelled_id = btn_id["index"]
                    break
            
            if cancelled_id:
                # Si c'est une tâche temporaire, la supprimer définitivement
                if cancelled_id in temp_ids:
                    task = StandardTask.query.get(cancelled_id)
                    if task:
                        db.session.delete(task)
                        db.session.commit()
                    temp_ids.remove(cancelled_id)
                
                # Retirer de la liste d'édition
                if cancelled_id in editing_ids:
                    editing_ids.remove(cancelled_id)
            
            tasks = StandardTask.query.order_by(StandardTask.id.desc()).all()
            return self.render_task_list(tasks, editing_ids, temp_ids), editing_ids, temp_ids

        # Callback pour passer en mode édition
        @self.app.callback(
            Output("std-task-container", "children", allow_duplicate=True),
            Output("editing-task-ids", "data", allow_duplicate=True),
            Input({"type": "modify-task-btn", "index": ALL}, "n_clicks"),
            State({"type": "modify-task-btn", "index": ALL}, "id"),
            State("editing-task-ids", "data"),
            State("temp-task-ids", "data"),
            prevent_initial_call=True
        )
        def modify_task(n_clicks_list, btn_ids, editing_ids, temp_ids):
            if not any(n_clicks_list):
                return no_update, no_update
                
            # Trouver quelle tâche modifier
            modify_id = None
            for idx, (n_clicks, btn_id) in enumerate(zip(n_clicks_list, btn_ids)):
                if n_clicks:
                    modify_id = btn_id["index"]
                    break
            
            if modify_id and modify_id not in editing_ids:
                editing_ids.append(modify_id)
            
            tasks = StandardTask.query.order_by(StandardTask.id.desc()).all()
            return self.render_task_list(tasks, editing_ids, temp_ids), editing_ids

        # Callback pour ouvrir le modal de suppression
        @self.app.callback(
            Output("delete-modal", "is_open"),
            Output("deleted-task-id", "data"),
            Input({"type": "delete-task-btn", "index": ALL}, "n_clicks"),
            State({"type": "delete-task-btn", "index": ALL}, "id"),
            prevent_initial_call=True
        )
        def open_delete_modal(n_clicks_list, btn_ids):
            if not any(n_clicks_list):
                return no_update, no_update
                
            # Trouver quelle tâche supprimer
            delete_id = None
            for idx, (n_clicks, btn_id) in enumerate(zip(n_clicks_list, btn_ids)):
                if n_clicks:
                    delete_id = btn_id["index"]
                    break
            
            if delete_id:
                return True, delete_id
            return no_update, no_update

        # Callback pour gérer la suppression
        @self.app.callback(
            Output("std-task-container", "children", allow_duplicate=True),
            Output("delete-modal", "is_open", allow_duplicate=True),
            Output("editing-task-ids", "data", allow_duplicate=True),
            Output("temp-task-ids", "data", allow_duplicate=True),
            Input("confirm-delete", "n_clicks"),
            Input("cancel-delete", "n_clicks"),
            State("deleted-task-id", "data"),
            State("editing-task-ids", "data"),
            State("temp-task-ids", "data"),
            prevent_initial_call=True
        )
        def handle_delete_confirmation(confirm, cancel, task_id, editing_ids, temp_ids):
            triggered = callback_context.triggered_id
            
            if triggered == "cancel-delete":
                return no_update, False, no_update, no_update
                
            if triggered == "confirm-delete" and task_id:
                # Supprimer la tâche
                task = StandardTask.query.get(task_id)
                if task:
                    db.session.delete(task)
                    db.session.commit()
                
                # Nettoyer les listes
                if task_id in editing_ids:
                    editing_ids.remove(task_id)
                if task_id in temp_ids:
                    temp_ids.remove(task_id)
                
                tasks = StandardTask.query.order_by(StandardTask.id.desc()).all()
                return self.render_task_list(tasks, editing_ids, temp_ids), False, editing_ids, temp_ids
                
            return no_update, False, no_update, no_update