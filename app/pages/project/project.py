import dash_bootstrap_components as dbc
from dash import html, dcc, Input, Output, State, callback_context, no_update
from flask import current_app
from database.db import db
from database.model import Project
from database.model import BimUsers as dbBimUsers
from database.model import Task as dbTask
import plotly.express as px
from datetime import datetime
import pandas as pd
import calendar
from datetime import date, timedelta
from math import ceil
from dash import Input, Output, State, ctx
from dash.exceptions import PreventUpdate
from sqlalchemy.orm import Session
from .project_phases import ProjectPhases
import feffery_antd_components as fac
import full_calendar_component as fcc
import random

class ProjectPage:
    def __init__(self, app):
        self.app = app
        self.register_callbacks()
        self.project_phases = ProjectPhases(self.app)
        
        # Enhanced color schemes for better visual hierarchy
        self.STATUS_COLORS = {
            "En cours": {"color": "#1976d2", "bg": "#e3f2fd", "badge": "primary"},
            "Terminé": {"color": "#388e3c", "bg": "#e8f5e9", "badge": "success"},
            "Non commencé": {"color": "#757575", "bg": "#f5f5f5", "badge": "secondary"},
            "En attente": {"color": "#f57c00", "bg": "#fff3e0", "badge": "warning"},
            "Suspendu": {"color": "#d32f2f", "bg": "#ffebee", "badge": "danger"}
        }
        
        self.PHASE_COLORS = [
            "#1976d2", "#388e3c", "#f57c00", "#d32f2f", 
            "#7b1fa2", "#303f9f", "#00796b", "#455a64"
        ]

    def generate_enhanced_calendar(self, project):
        """Generate an enhanced calendar with better styling and functionality"""
        formatted_date = datetime.now().date().isoformat()
        
        # Generate events from project phases with enhanced styling
        events = []
        for i, project_phase in enumerate(project.phases):
            if project_phase.start_date and project_phase.end_date:
                color = self.PHASE_COLORS[i % len(self.PHASE_COLORS)]
                events.append({
                    "title": project_phase.phase.name,
                    "start": datetime.strptime(str(project_phase.start_date), "%Y-%m-%d").date().isoformat(),
                    "end": datetime.strptime(str(project_phase.end_date), "%Y-%m-%d").date().isoformat(),
                    "backgroundColor": color,
                    "borderColor": color,
                    "textColor": "#ffffff",
                    "extendedProps": {
                        "phase_id": project_phase.id,
                        "description": getattr(project_phase.phase, 'description', '')
                    }
                })

        return html.Div([
            fcc.FullCalendarComponent(
                id="project-calendar",
                initialView="dayGridMonth",
                headerToolbar={
                    "left": "prev,next today",
                    "center": "title",
                    "right": "listWeek,timeGridWeek,dayGridMonth"
                },
                initialDate=formatted_date,
                editable=True,
                selectable=True,
                events=events,
                nowIndicator=True,
                navLinks=True,

        
            )
        ], style={
            "background": "white",
            "border-radius": "12px",
            "box-shadow": "0 2px 12px rgba(0,0,0,0.08)",
            "padding": "20px",
            "min-height": "600px"
        })

    def create_project_header(self, project):
        """Create an enhanced project header with key metrics"""
        # Calculate project progress
        total_phases = len(project.phases)
        completed_phases = len([p for p in project.phases if getattr(p, 'status', '') == 'Terminé'])
        progress = (completed_phases / total_phases * 100) if total_phases > 0 else 0
        
        # # Calculate days remaining
        # if project.end_date:
        #     days_remaining = (project.end_date - datetime.now().date()).days
        #     days_text = f"{days_remaining} jours restants" if days_remaining > 0 else "Projet terminé"
        # else:
        days_text = "Date de fin non définie"

        status_config = self.STATUS_COLORS.get(project.status, self.STATUS_COLORS["Non commencé"])

        return dbc.Card([
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.Div([
                            html.H2(project.name, className="mb-2", 
                                   style={"color": "#2c3e50", "font-weight": "600"}),
                            dbc.Badge(
                                project.status, 
                                color=status_config["badge"],
                                className="mb-3",
                                style={"font-size": "0.9rem", "padding": "8px 16px"}
                            ),
                        ])
                    ], md=8),
                    dbc.Col([
                        html.Div([
                            html.H4(f"{progress:.0f}%", 
                                   style={"color": status_config["color"], "margin": "0"}),
                            html.Small("Progression", style={"color": "#6c757d"}),
                            dbc.Progress(
                                value=progress,
                                color="primary" if progress < 100 else "success",
                                className="mt-2",
                                style={"height": "8px"}
                            )
                        ], className="text-center")
                    ], md=4)
                ], className="mb-4"),
                            html.Hr(className="my-3"),

                dbc.Row([
                
           
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Code Akuiteo", className="fw-semibold mb-2"),
                            dbc.Input(
                                type="text", 
                                value=project.code_akuiteo, 
                                id="input-code-akuiteo", 
                                disabled=True,
                                style={
                                    "background": "#f8f9fa",
                                    "border": "1px solid #dee2e6",
                                    "border-radius": "8px"
                                }
                            )
                        ], md=6),
                        
                        dbc.Col([
                            dbc.Label("Statut", className="fw-semibold mb-2"),
                            dbc.Select(
                                options=[
                                    {"label": "📋 Non commencé", "value": "Non commencé"},
                                    {"label": "🔄 En cours", "value": "En cours"},
                                    {"label": "⏸️ En attente", "value": "En attente"},
                                    {"label": "✅ Terminé", "value": "Terminé"},
                                    {"label": "🚫 Suspendu", "value": "Suspendu"}
                                ],
                                value=project.status,
                                id="input-status",
                                style={"border-radius": "8px"}
                            )
                        ], md=6)
                    ], className="mb-3"),
                ])
            ])
        ], style={
            "background": f"linear-gradient(135deg, {status_config['bg']} 0%, #ffffff 100%)",
            "border-radius": "16px",
            "box-shadow": "0 4px 20px rgba(0,0,0,0.08)",
            "margin-bottom": "24px"
        })

    def create_project_details_card(self, project):
        """Create enhanced project details form"""
        return dbc.Card([
            dbc.CardHeader([
                html.Div([
                    html.I(className="fas fa-info-circle me-2"),
                    html.H5("Détails du Projet", className="mb-0 d-inline")
                ], style={"color": "#495057"})
            ], style={"background": "#f8f9fa", "border-bottom": "1px solid #e9ecef"}),
            
            dbc.CardBody([
             
            ])
        ], style={
            "border": "none",
            "border-radius": "12px",
            "box-shadow": "0 2px 12px rgba(0,0,0,0.08)",
            "margin-bottom": "24px"
        })

    def create_planning_card(self, project):
        """Create enhanced planning card with calendar"""
        return dbc.Card([
          

            dbc.CardBody([
                html.H5("Planning Prévisonnel", className="mb-0 d-inline"),

                html.Div(id="calendar-container", children=[
                    self.generate_enhanced_calendar(project)
                ])
            ], style={"padding": "20px"})
        ], style={
            "border-radius": "12px",
            "box-shadow": "0 2px 12px rgba(0,0,0,0.08)"
        })

    def layout(self, project_id):
        """Main layout with enhanced UI/UX"""
        self.project_id = project_id
        
        with current_app.app_context():
            project = Project.query.get(self.project_id)
            
            if not project:
                return self.project_not_found_ui()
            
            self.project = project
            
            return dbc.Row([
            
                    dbc.Breadcrumb(
                        items=[
                            {"label": "Projets", "href": "/BIMSYS/projects", "external_link": True},
                            {
                                "label": project.name,
                                "href": f"/BIMSYS/project/{project.id}",
                                "external_link": True,
                            },
                        ],
                        className="mb-3"
                    ),
                    
                    dbc.Col([
                        dbc.Row(self.create_project_header(project)),
                        dbc.Row([self.create_planning_card(project)                           
                        ]),
                    ],className="g-4"),

                    dbc.Col([
                            self.project_phases.layout(project)
                        ],className="g-4" ,style={"margin-left" : "20px"}) ,
                    
               ])

    def project_not_found_ui(self):
        """Enhanced 404 page"""
        return html.Div([
            dbc.Container([
                dbc.Row([
                    dbc.Col([
                        html.Div([
                            html.I(className="fas fa-exclamation-triangle", 
                                  style={"font-size": "4rem", "color": "#dc3545", "margin-bottom": "20px"}),
                            html.H1("Projet Non Trouvé", 
                                   style={"color": "#495057", "margin-bottom": "15px"}),
                            html.P("Le projet demandé n'existe pas ou a été supprimé.", 
                                  style={"color": "#6c757d", "font-size": "1.1rem", "margin-bottom": "30px"}),
                            dbc.Button(
                                [html.I(className="fas fa-arrow-left me-2"), "Retour aux Projets"],
                                href="/BIMSYS/projects",
                                color="primary",
                                size="lg",
                                style={"border-radius": "25px", "padding": "12px 30px"}
                            )
                        ], className="text-center")
                    ], width=12)
                ], justify="center", style={"margin-top": "100px"})
            ], fluid=True)
        ], style={
            "background": "linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)",
            "min-height": "100vh"
        })

    def register_callbacks(self):
        """Enhanced callbacks with better error handling and UX"""
        
        @self.app.callback(
            Output("calendar-container", "children"),
            Input("input-status", "value"),
            [State("input-code-akuiteo", "value")],
            prevent_initial_call=True
        )
        def update_project_and_calendar(status, code):
            if not ctx.triggered_id:
                raise PreventUpdate

            try:
                project = db.session.query(Project).filter(Project.id == self.project_id).first()
                if not project:
                    raise PreventUpdate

                # Update project fields
                if ctx.triggered_id == "input-status":
                    project.status = status               
    

                db.session.commit()

                # Calculate new budget display
                budget_display = f"{(project.days_budget * 750):,.0f} €" if project.days_budget else "0 €"
                
                # Refresh calendar
                new_calendar = self.generate_enhanced_calendar(project)
                
                return new_calendar, budget_display

            except Exception as e:
                print(f"Error updating project: {e}")
                raise PreventUpdate

        @self.app.callback(
            Output("project-calendar", "events"),
            [Input("refresh-calendar", "n_clicks")],
            prevent_initial_call=True
        )
        def refresh_calendar_events(n_clicks):
            if not n_clicks:
                raise PreventUpdate
                
            try:
                project = Project.query.get(self.project_id)
                if not project:
                    raise PreventUpdate
                
                # Generate fresh events
                events = []
                for i, project_phase in enumerate(project.phases):
                    if project_phase.start_date and project_phase.end_date:
                        color = self.PHASE_COLORS[i % len(self.PHASE_COLORS)]
                        events.append({
                            "title": project_phase.phase.name,
                            "start": datetime.strptime(str(project_phase.start_date), "%Y-%m-%d").date().isoformat(),
                            "end": datetime.strptime(str(project_phase.end_date), "%Y-%m-%d").date().isoformat(),
                            "backgroundColor": color,
                            "borderColor": color,
                            "textColor": "#ffffff"
                        })
                
                return events
                
            except Exception as e:
                print(f"Error refreshing calendar: {e}")
                raise PreventUpdate