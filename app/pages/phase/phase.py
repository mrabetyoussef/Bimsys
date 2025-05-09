import dash_bootstrap_components as dbc
from dash import html
from sqlalchemy.orm import joinedload
from database.model import ProjectPhase as dbProjectPhase, Phase as dbPhase
from database.db import db
from dash import html, dcc, Input, Output, State, callback_context , no_update


class Phase:
    def __init__(self, app):
        self.app = app
        self.register_callback()

    def layout(self, project_phase_id):
        """Génère l'affichage d'une seule phase de projet."""
        self.project_phase_id = project_phase_id
        project_phase = dbProjectPhase.query.get(project_phase_id)
        if not project_phase:
            return dbc.Alert("Phase introuvable.", color="danger")

        phase = project_phase.phase
        if not phase:
            return dbc.Alert("Détail de la phase indisponible.", color="warning")

        return dbc.Card([
            dbc.CardHeader(dbc.Row([
                                        dbc.Col(html.H4(f"{phase.name}", className="mb-0"), width=10),
                                        dbc.Col(
                                            dbc.Button(
                                               html.I(className="fa fa-trash", style={"color": "blue"}),
                                                outline=True,
                                                color="primary",
                                                id="delete-phase-button"
                                            ),
                                            width=2,
                                            className="text-end"
                                        ),
                                        html.Div(id="delete-phase-dummy"),
                                        self.delete_phase_modal()
                                    ], align="center"),),

            
            dbc.CardBody([
                html.P(f"ID Phase : {phase.id}"),
                html.P(f"ID Lien Projet-Phase : {project_phase.id}"),
                html.P(f"Projet ID : {project_phase.project_id}"),
            ]), dcc.Location(id="redirect", refresh=True),
        ], style={"margin": "20px"})


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
            # 1) First output is the modal’s open state
            # 2) Second output is the redirect target
            [
                Output("delete-phases-modal", "is_open"),
                Output("redirect", "pathname"),
            ],
            # three Inputs for the three buttons
            [
                Input("delete-phase-button",        "n_clicks"),
                Input("cancel-delete-phase-button", "n_clicks"),
                Input("validate-delete-phase-button","n_clicks"),
            ],
            # one State for whether the modal is currently open
            [
                State("delete-phases-modal", "is_open"),
            ],
            prevent_initial_call=True,
        )
        def delete_phase(n_open, n_cancel, n_validate, is_open):
            ctx = callback_context.triggered_id

            # 1) Trash icon → open modal
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
