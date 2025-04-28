import dash_bootstrap_components as dbc
from dash import html
from sqlalchemy.orm import joinedload
from database.model import ProjectPhase as dbProjectPhase, Phase as dbPhase
from database.db import db

class Phase:
    def __init__(self, app):
        self.app = app

    def layout(self, project_phase_id):
        """Génère l'affichage d'une seule phase de projet."""
        project_phase = dbProjectPhase.query.get(project_phase_id)
        print(project_phase)
        if not project_phase:
            return dbc.Alert("Phase introuvable.", color="danger")

        phase = project_phase.phase
        print(phase)
        if not phase:
            return dbc.Alert("Détail de la phase indisponible.", color="warning")

        return dbc.Card([
            dbc.CardHeader(html.H4(f"Phase : {phase.name}")),
            dbc.CardBody([
                html.P(f"ID Phase : {phase.id}"),
                html.P(f"ID Lien Projet-Phase : {project_phase.id}"),
                html.P(f"Projet ID : {project_phase.project_id}"),
                # Tu peux ajouter ici d'autres infos selon ton modèle
            ])
        ], style={"margin": "20px"})

    def get_project_phase(self, project_phase_id):
        """Charge un ProjectPhase avec sa Phase associée."""
        return dbProjectPhase.query.options(
            joinedload(dbProjectPhase.phase)
        ).filter_by(id=project_phase_id).first()
