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
            tasks = StandardTask.query.all()

        return dbc.Container([
            html.H2("Gestion des tâches standard", className="mb-4"),

            dbc.Button("➕ Ajouter une tâche standard", id="add-std-task", color="success", className="mb-4"),

            dcc.Store(id="editing-task-ids", data=[]),  # ← mémorise les IDs en édition

            dbc.Row([
                dbc.Col([
                       dbc.Accordion(id="std-task-list", children=[
                        self.render_task(task, is_editing=False) for task in tasks
                    ])
                ], width=12)
            ]),

            dcc.Store(id="deleted-task-id"),

            dbc.Modal(
                [
                    dbc.ModalHeader("Confirmation"),
                    dbc.ModalBody("Supprimer cette tâche standard ?"),
                    dbc.ModalFooter([
                        dbc.Button("Annuler", id="cancel-delete", className="me-2"),
                        dbc.Button("Supprimer", id="confirm-delete", color="danger")
                    ])
                ],
                id="delete-modal",
                is_open=False,
                centered=True,
            )
        ], fluid=True)

    def render_task(self, task, is_editing=False):
        if is_editing:
            return dbc.Card([
                dbc.CardBody([
                    dbc.Label("Nom"),
                    dbc.Input(id={"type": "std-name", "index": task.id}, value=task.name, type="text", className="mb-2"),
                    dbc.Label("Description"),
                    dbc.Textarea(id={"type": "std-desc", "index": task.id}, value=task.description or "", className="mb-2"),
                    dbc.Label("Durée estimée (jours)"),
                    dbc.Input(id={"type": "std-days", "index": task.id}, value=task.estimated_days, type="number", className="mb-3"),

                    # Ligne contenant les deux boutons côte à côte
                    dbc.Row([
                        dbc.Col(
                              dbc.Col(
                                  
                                dbc.Button(
                                    html.I(className="fa fa-plus", style={"color": "blue"}),
                                    outline=True,
                                    color="primary",
                                id={"type": "save-std-task", "index": task.id},
                                ),
                                width=2,
                                className="text-end"
                                        ),
                         
                            width="auto"
                        ),
                        dbc.Col(
                              dbc.Col(
                                dbc.Button( 
                                    html.I(className="fa fa-times", style={"color": "red"}),

                                    id={"type": "delete-task-btn", "index": task.id},
                                    color="outline-danger", 
                                    className="float-end"),
                            
                                width=2,
                                className="text-end"
                                  ),
                           
                            width="auto"
                        )
                    ], justify="end", className="mt-3")
                ])
            ], className="mb-3")

        else:
           return dbc.Row([
    dbc.Col(
        dbc.AccordionItem(
            title=dbc.Row([
                dbc.Col(
                    html.H5(task.name, className="mb-0"),
                    style={"maxWidth": "300px", "overflow": "hidden", "textOverflow": "ellipsis", "whiteSpace": "nowrap"}
                ),
                dbc.Col(
                    html.Small(
                        f"Durée estimée : {task.estimated_days if task.estimated_days is not None else 'Non définie'} j",
                        className="text-muted"
                    ),
                    width="auto",
                    className="d-flex align-items-center"
                )
            ], align="center", className="w-100"),
            children=dbc.CardBody([
                html.P(task.description or ""),
               
            ]),
            className="mb-2"
        ),
    ),
    dbc.Col(
        dbc.DropdownMenu(
            label=html.I(className="fas fa-ellipsis-vertical"),
            class_name="dropdown-hover",
            caret=False,
            toggle_style={
                "padding": "0",
                "border": "none",
                "background": "transparent",
                "color": "grey"
            },
            children=[
           dbc.Col([
                dbc.ButtonGroup([
                    dbc.Button(
                         "Modifier",
                        id={"type": "modify-task-btn", "index": task.id},
                        color="primary",
                        className="me-2"
                    ),
                    dbc.Button(
                        "Supprimer",
                        id={"type": "delete-task-btn", "index": task.id},
                        color="danger"
                    )
                ], size="sm", className="float-end")
            ], width="auto", className="d-flex justify-content-end")
            ]
        ),
        width="auto",
        className="d-flex align-items-start justify-content-end",
    )
], align="start", className="mb-2")




    def register_callbacks(self):
        @self.app.callback(
            Output("std-task-list", "children", allow_duplicate=True),
            Output("editing-task-ids", "data", allow_duplicate=True),
            Input("add-std-task", "n_clicks"),
            State("editing-task-ids", "data"),
            prevent_initial_call=True
        )
        def add_standard_task(n_clicks, editing_ids):
            new_task = StandardTask(name="Nouvelle tâche", description="", estimated_days=None)
            db.session.add(new_task)
            db.session.commit()
            editing_ids.append(new_task.id)
            tasks = StandardTask.query.all()
            return [self.render_task(t, is_editing=(t.id in editing_ids)) for t in tasks], editing_ids

        @self.app.callback(
            Output("std-task-list", "children"),
            Output("editing-task-ids", "data"),
            Input({"type": "save-std-task", "index": ALL}, "n_clicks"),
            State({"type": "std-name", "index": ALL}, "value"),
            State({"type": "std-desc", "index": ALL}, "value"),
            State({"type": "std-days", "index": ALL}, "value"),
            State({"type": "save-std-task", "index": ALL}, "id"),
            State("editing-task-ids", "data"),
            prevent_initial_call=True
        )
        def save_edits(n_clicks_list, names, descs, days_list, btn_ids, editing_ids):
            updated_id = None
            for idx, btn in enumerate(btn_ids):
                if n_clicks_list[idx]:
                    task_id = btn["index"]
                    task = StandardTask.query.get(task_id)
                    if task:
                        task.name = names[idx]
                        task.description = descs[idx]
                        try:
                            task.estimated_days = float(days_list[idx]) if days_list[idx] is not None else None
                        except ValueError:
                            task.estimated_days = None
                        db.session.commit()
                        updated_id = task_id
                        break

            if updated_id and updated_id in editing_ids:
                editing_ids.remove(updated_id)

            tasks = StandardTask.query.all()
            return [self.render_task(t, is_editing=(t.id in editing_ids)) for t in tasks], editing_ids

        @self.app.callback(
            Output("delete-modal", "is_open"),
            Output("deleted-task-id", "data"),
            Input({"type": "delete-task-btn", "index": ALL}, "n_clicks"),
            State("deleted-task-id", "data"),
            prevent_initial_call=True
        )
        def open_delete_modal(n_clicks_list, current_id):
            triggered = callback_context.triggered_id

            # Ne réagit que si le bouton a été réellement cliqué
            if triggered and isinstance(triggered, dict):
                index = triggered["index"]
                triggered_idx = next(
                    (i for i, btn in enumerate(n_clicks_list) if btn and isinstance(btn, int) and btn > 0),
                    None
                )
                if triggered_idx is not None:
                    return True, index

            return no_update, no_update

        @self.app.callback(
            Output("std-task-list", "children", allow_duplicate=True),
            Output("delete-modal", "is_open", allow_duplicate=True),
            Output("editing-task-ids", "data", allow_duplicate=True),
            Input("confirm-delete", "n_clicks"),
            Input("cancel-delete", "n_clicks"),
            State("deleted-task-id", "data"),
            State("editing-task-ids", "data"),
            prevent_initial_call=True
        )
        def handle_delete(confirm, cancel, task_id, editing_ids):
            triggered = callback_context.triggered_id
            if triggered == "cancel-delete":
                return no_update, False, editing_ids
            if triggered == "confirm-delete" and task_id:
                task = StandardTask.query.get(task_id)
                if task:
                    db.session.delete(task)
                    db.session.commit()
                if task_id in editing_ids:
                    editing_ids.remove(task_id)
                tasks = StandardTask.query.all()
                return [self.render_task(t, is_editing=(t.id in editing_ids)) for t in tasks], False, editing_ids
            return no_update, False, editing_ids
