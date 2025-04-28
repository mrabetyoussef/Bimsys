import dash_bootstrap_components as dbc
from dash import html, dcc, Input, Output, State, callback_context
from flask import current_app
from database.db import db
from database.model import Project
from database.model import BimUsers as dbBimUsers
from database.model import Task as  dbTask
from database.model import ProjectPhase as  dbProjectPhase , Phase as dbPhases

from dash import html, dcc, Input, Output, State, callback_context, no_update
import plotly.express as px
from datetime import datetime
import pandas as pd
import calendar
from datetime import date, timedelta
from dash import html
import dash_bootstrap_components as dbc
from math import ceil
from dash import Input, Output, State, ctx
from dash.exceptions import PreventUpdate
from flask import session as Session


class ProjectPhases() :

    def __init__(self,app):
      self.app = app
      self.register_callback()

    def layout(self,project):
        self.project = project
        return dbc.Row([dbc.Row(self.get_project_phases(project) , id="phases-display"),self.add_phase_model()])

    def get_project_phases(self, project):
        if project.phases:
            print(len(project.phases))

            phases = [dbc.Row(
                html.A(
                    dbc.Card(
                        dbc.CardBody([
                            html.H5(t.phase.name if t.phase is not None else "test", className="card-title"),

                        ]),
                    className="card-hover", 
                    style={
                        "margin-bottom": "20px",
                        "box-shadow": "0px 4px 6px rgba(0, 0, 0, 0.1)"
                    }
                ),
                href=f"/BIMSYS/phase/{t.id}",
                style={"textDecoration": "none", "color": "inherit"}
                    ),
                )
                for t in project.phases
            ]
        else : 
            phases = "Pas encore de phases sur ce projet"
        ui = dbc.Card([dbc.CardHeader(["Phases", 
                        dbc.Button(
                                                html.I(className="fa fa-plus", style={"color": "blue"}),
                                                outline=True,
                                                color="primary",
                                                id="open-add-project-phase"
                                            ),]),
                       
                        dbc.CardBody(phases)])
        return ui
    
    def add_phase_model(self):
        all_phases = dbPhases.query.all() 
        op = [ {"label": p.name, "value": p.id} for p in all_phases ]
        op.append(   {"label" :"ajouter une nouvelle phase" ,"value" : "add-new-phase" })
        ui = dbc.Modal([dbc.ModalHeader("Ajouter une phase"),
                        dbc.ModalBody(
                           [dbc.Label("Nom la phase"),
                            dbc.Select(
                                        options=op,
                                        id="input-prject-phases",
                                        className="mb-3",
                                        placeholder="Choissisez une phase",
                                    ),
                               
                           ],
                            


        ) ], is_open=False,id="add-project-phases-modal")
        return ui
    
    def register_callback(self):
        @self.app.callback(
           [ 
            Output("add-project-phases-modal", "is_open"),
            Output("add-project-phases-modal", "children"),
            Output("phases-display", "children"),],

            Input("open-add-project-phase","n_clicks"),
            Input("input-prject-phases","value"),
            State("add-project-phases-modal", "is_open"),
            State("add-project-phases-modal", "children"),


            prevent_initial_call=True,
            
        )
        def toggle_task_modal(add_phases_click,project_phase_id,modal_state , add_phase_modal_children ,):
            ctx =  callback_context.triggered_id
            if ctx in "open-add-project-phase":
                return not modal_state , no_update , no_update
            if ctx in "input-prject-phases" and modal_state :
                if project_phase_id == "add-new-phase" :
                    add_phase_modal_children.append(dbc.Col([dbc.Label("Nom de la phase") , dbc.Input(type="text")]))
                    return (no_update , add_phase_modal_children , no_update)
                self.add_project_phase(phase_id=project_phase_id)
                ui =  self.get_project_phases(self.project)
                return not modal_state , no_update, ui


                
    def add_project_phase(self,**kwargs):
        new_element = dbProjectPhase(self.project.id , **kwargs)
        db.session.add(new_element)
        db.session.commit()
        self.project = Project.query.get(self.project.id)

        
            