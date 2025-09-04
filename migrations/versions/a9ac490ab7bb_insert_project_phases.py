"""insert project phases

Revision ID: a9ac490ab7bb
Revises: c8d83600742e
Create Date: 2025-07-27 10:30:48.049339

"""
from alembic import op
import sqlalchemy as sa
from database.model import Phase , ProjectPhase , Project,BimUsers
from database.db import db
from datetime import datetime
import pandas as pd
from datetime import datetime
from collections import defaultdict
import re
# revision identifiers, used by Alembic.
revision = 'a9ac490ab7bb'
down_revision = 'c8d83600742e'
branch_labels = None
depends_on = None


def upgrade():
    #add phases 
    existing = Phase.query.all()
    ex_names= [p.name for p in existing]
    for name in ["ACT",
        "ACT(Soumission)",
        "AMO",
        "AOR",
        "APD",
        "APD MC",
        "APD2",
        "APO",
        "APS",
        "APS / OPTION",
        "APS MC",
        "ASB",
        "AVP",
        "CCR",
        "CON",
        "DCE",
        "DCE/PH2",
        "DET",
        "EP",
        "EPR",
        "ESQ",
        "EXE",
        "FAI",
        "GEN",
        "PASO",
        "PC",
        "PRO",
        "PRO (avenant)",
        "PRO BV SUD",
        "PRO-DCE",
        "PRO/PH2",
        "REA",
        "VISA",
        ] :
        if name not in ex_names:
            p = Phase(name=name)
            db.session.add(p)
        db.session.commit()



    import os
    curt = os.curdir
    print("Répertoire actuel :",curt,  os.path.abspath(curt))

    # Charger les données depuis le fichier Excel
    all_project_data = extract_project_phase_data_from_excel("/bimsys/exccel_modif.xlsx")


    for project_data in all_project_data:
        try :
            insert_project_phases(
                project_name=project_data["project_name"],
                bimuser_name=project_data["bimuser_name"],
                phases_data=project_data["phases_data"]
            )
        except Exception as ex :
            print("****************")
            print(ex)
            continue
    db.session.commit()
    pass



def insert_project_phases(project_name, bimuser_name, phases_data):
    """
    Insère plusieurs phases pour un projet donné en recherchant dynamiquement les IDs.

    :param project_name: Nom du projet dans la table Project
    :param bimuser_name: Nom (partiel ou complet) du BimUser assigné
    :param phases_data: Liste de dicts contenant phase, start_date, end_date, euros_budget, days_budget
    """

    project = Project.query.filter_by(name=project_name).first()
    if not project:
        raise ValueError(f"Projet '{project_name}' introuvable.")

    user = next((u for u in BimUsers.query.all() if bimuser_name.lower() in u.name.lower()), None)
    if not user:
        raise ValueError(f"Utilisateur contenant '{bimuser_name}' introuvable.")

    phase_names = list(set(entry["phase"] for entry in phases_data))
    phases = {p.name: p for p in Phase.query.filter(Phase.name.in_(phase_names)).all()}

    for entry in phases_data:
        phase_name = entry["phase"]
        if phase_name not in phases:
            raise ValueError(f"Phase '{phase_name}' introuvable.")

        project_phase = ProjectPhase(
            project_id=project.id,
            phase_id=phases[phase_name].id,
            start_date=datetime.strptime(entry["start_date"], "%d/%m/%Y") if entry["start_date"] else None,
            end_date=datetime.strptime(entry["end_date"], "%d/%m/%Y")if entry["start_date"] else None,
            euros_budget=float(entry["euros_budget"]),
            days_budget=round(entry["days_budget"],2),
            assigned_bimuser_id=user.id,
            costum_days_budget =round(entry["days_budget"],2),
        )
        db.session.add(project_phase)



def extract_project_phase_data_from_excel(file_path):
    """
    Lit un fichier Excel et retourne un dictionnaire structuré de projets avec phases à insérer.

    :param file_path: Chemin vers le fichier Excel (.xlsx ou .xls)
    :return: Liste de dictionnaires prêts pour insert_project_phases()
    """
    df = pd.read_excel(file_path)

    # Normalisation des noms de colonnes
    df.columns = [col.strip().lower().replace(" ", "_") for col in df.columns]

    # Nettoyage
    def clean_str(s):
        return str(s).strip() if pd.notna(s) else None

    from datetime import datetime

    def parse_date(s):
        """
        Convertit une chaîne de caractères de type 'YYYY-MM-DD HH:MM:SS'
        en objet datetime et la reformate en chaîne au format 'JJ/MM/AAAA'.
        Renvoie None si le format est invalide ou si la valeur est vide.
        """
        try:
            if pd.isna(s):  # si c'est un NaT ou NaN
                return None
            clean_s = str(s).split(" ")[0]  # extrait la date sans l'heure
            dt = datetime.strptime(clean_s, '%Y-%m-%d')  # parse au format ISO
            return dt.strftime('%d/%m/%Y')  # convertit en JJ/MM/AAAA
        except Exception as e:
            print(f"Erreur lors du parsing de la date '{s}': {e}")
            return None


    def parse_float(s):
        if pd.isna(s) or str(s).strip() == "" or str(s).strip() == "?":
            return None
        cleaned = re.sub(r"[^\d,\.]", "", str(s)).replace(",", ".")
        try:
            return float(cleaned)
        except ValueError:
            return None

    df["project_name"] = df["nom_projet"].apply(clean_str)
    df["phase"] = df["phase"].apply(clean_str)
    df["bimuser_name"] = df["bim_manager"].apply(clean_str)
    df["start_date"] = df["date_démarrage"].apply(parse_date)
    df["end_date"] = df["date_fin"].apply(parse_date)
    df["days_budget"] = df["days_budgets"].apply(parse_float)
    df["euros_budget"] = df["euros_budget"].apply(parse_float)

    # Construction du dictionnaire par projet / utilisateur
    project_dict = defaultdict(list)
    for _, row in df.iterrows():
        key = (row["project_name"], row["bimuser_name"])
        phase_entry = {
            "phase": row["phase"],
            "start_date": str(row["start_date"]),
            "end_date": str(row["end_date"]),
            "euros_budget": row["euros_budget"],
            "days_budget": row["days_budget"]
        }
        project_dict[key].append(phase_entry)

    final_data = [
        {
            "project_name": k[0],
            "bimuser_name": k[1],
            "phases_data": v
        }
        for k, v in project_dict.items()
    ]
    print(final_data)
    return final_data



def downgrade():
    pass
