"""tasks table insetion

Revision ID: 4b00c803a58f
Revises: 41ff2e295ed3
Create Date: 2025-07-01 16:10:44.252566

"""
from alembic import op
import sqlalchemy as sa
from database.model import StandardTask
from database.db import db


# revision identifiers, used by Alembic.
revision = '4b00c803a58f'
down_revision = '41ff2e295ed3'
branch_labels = None
depends_on = None


def upgrade():

    tasks_data = [
        ("Prise de connaissance des pièces marchés, cahier des charges BIM, conseil auprès MOE", 0.5, "Contractualisation", "NC"),
        ("Estimation mission (transfert interne) / Rédaction PM (affaire pilote)", 0.5, "Contractualisation", "NC"),
        ("Gestion / vérifications d'affaire", 1, "Contractualisation", "NC"),
        ("Participation RIAFF", 0.25, "Contractualisation", "NC"),
        ("Administration de la plateforme collaborative (arborescence / droits)", 0.5, "Mise en place démarche BIM", "NC"),
        ("Rédaction et mise à jour (pendant la phase) de la convention BIM / inclut :", 4, "Mise en place démarche BIM", "Convention BIM"),
        ("Définition des cas d'usages BIM", 0, "Mise en place démarche BIM", "Convention BIM"),
        ("Définition du processus de production et d'enrichissement des maquettes", 0, "Mise en place démarche BIM", "Convention BIM"),
        ("Définition des processus d'échange", 0, "Mise en place démarche BIM", "Convention BIM"),
        ("Définition du découpage des maquettes", 0, "Mise en place démarche BIM", "Convention BIM"),
        ("Configuration des exports IFC", 0, "Mise en place démarche BIM", "Convention BIM"),
        ("Création du fichier de correspondance des classifications SNCF", 0, "Mise en place démarche BIM", "Convention BIM"),
        ("Définition d'une procédure de détection de clash / coordination technique BIM", 0, "Mise en place démarche BIM", "Convention BIM"),
        ("Co-écriture de la convention BIM", 1, "Mise en place démarche BIM", "Convention BIM"),
        ("Mise à jour de la convention BIM de la phase précédente", 1, "Mise en place démarche BIM", "Convention BIM"),
        ("Réunion de démarrage BIM (prépa + animation + CR)", 1, "Mise en place démarche BIM", "Convention BIM"),
        ("Analyse et traitement des données d'entrée BIM", 3, None, "Préparation des fichiers"),
        ("Création et géoréférencement des fichiers conteneurs", 0.5, None, "Préparation des fichiers"),
        ("Chargement des données d'entrée dans conteneur", 0.5, None, "Préparation des fichiers"),
        ("Création et géoréférencement d'un fichier RVT de référence (axes et niveaux)", 0.5, None, "Préparation des fichiers"),
        ("Préparation des fichiers de paramètres partagés communs", 0.5, "Production de la maquette", "NC"),
        ("Revue de projet (assemblage des maquettes + détection/analyse + animation + rapport + affectation)", 2, "Production de la maquette", "NC"),
        ("Gestion des échanges entre maquettes issues de logiciels différents", 1, "Collaboration", "Interopérabilité"),
        ("Gestion des problèmes de géoréférencement", 1, "Collaboration", "Interopérabilité"),
        ("Assemblage et création de vues sur Plateforme", 0.25, "Collaboration", "Échanges de maquettes et données"),
        ("Téléchargement des maquettes des intervenants depuis la plateforme", 0.25, "Collaboration", "Échanges de maquettes et données"),
        ("Première insertion des liens IFC dans les maquettes", 0.5, "Collaboration", "Échanges de maquettes et données"),
        ("Animation de réunions BIM + CR", 0.5, "Collaboration", "Pilotage, animation de la cellule BIM du projet"),
        ("Participation aux réunions d'avancement MOE", 0.25, "Collaboration", "Pilotage, animation de la cellule BIM du projet"),
        ("Participation aux réunions de pilotage MOA", 0.25, "Collaboration", "Pilotage, animation de la cellule BIM du projet"),
        ("Audits intermédiaires des maquettes / Rapport d'audit", 1, "Contrôle qualité", "NC"),
        ("Création + diffusion cartouche", 0.5, "Production des livrables", "Organisation des livrables 2D"),
        ("Audit des maquettes natives et IFC / rapport d'audit", 1.5, "Production des livrables", "Organisation des livrables maquettes numériques"),
        ("Dépôt des maquettes livrables (natives et IFC) sur plateforme", 0.25, "Production des livrables", "Organisation des livrables maquettes numériques"),
        ("Assemblage définitif + vues associées", 0.25, "Production des livrables", "Organisation des livrables maquettes numériques"),
        ("Support BIM et logiciel Revit", 0.25, "Assistance", "NC"),
        ("Production vidéos ou visite virtuelle", 3, "Objectif communication", "NC"),
        ("Production vidéo animation 4D", 15, "BIM 4D", "NC"),
        ("Analyse des offres entreprises", 1, "ACT", "NC"),
    ]

    for name, estimated_days, category1, category2 in tasks_data:
        task = StandardTask(
            name=name,
            estimated_days=estimated_days,
            category1=category1,
            category2=category2,
            description="None"
        )
        db.session.add(task)

    db.session.commit()



def downgrade():
    pass
