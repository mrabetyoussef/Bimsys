import dash_bootstrap_components as dbc
from dash import html, dcc, Input, Output, State, callback_context, no_update
from flask import current_app
from database.db import db
from database.model import BimUsers as dbBimUsers
from datetime import datetime
import pandas as pd
from dash import dcc
from dash import callback, Output, Input, ctx, dcc, MATCH, ALL
import pdb
from mailjet_rest import Client


class BimUsers:
    def __init__(self, app):
        """Initialize Users Page and Register Callbacks"""
        self.app = app
        self.register_callbacks()
        self.view_type = "Vue Carte"
        
    def projects_by_users(self):
        """Enhanced projects by users display"""
        with current_app.app_context():
            users = dbBimUsers.query.all()
            users_with_projects = []
            
            for user in users:
                if hasattr(user, 'projects') and user.projects:
                    projects = [project.project_parent.name for project in user.projects if hasattr(project, 'project_parent')]
                    if projects:
                        users_with_projects.append({user.name: projects})
            
            if not users_with_projects:
                return dbc.Container([
                    dbc.Alert([
                        html.I(className="fas fa-info-circle me-2"),
                        "Aucun projet assigné aux collaborateurs pour le moment."
                    ], color="info", className="text-center")
                ], fluid=True)

            return dbc.Container([
                dbc.Row([
                    dbc.Col([
                        html.H3([
                            html.I(className="fas fa-tasks me-3"),
                            "Projets en cours par collaborateurs"
                        ], className="mb-4", style={"color": "#2c3e50", "font-weight": "600"}),
                        html.P("Aperçu des projets assignés à chaque collaborateur", 
                              className="text-muted mb-4", style={"font-size": "0.9rem"})
                    ])
                ]),
                dbc.Row([
                    dbc.Col(
                        dbc.Card([
                            dbc.CardHeader([
                                html.H5([
                                    html.I(className="fas fa-user me-2"),
                                    user_name
                                ], className="mb-0", style={"color": "#2c3e50"})
                            ], style={"background-color": "#f8f9fa", "border-bottom": "2px solid #e9ecef"}),
                            dbc.CardBody([
                                html.Div([
                                    dbc.Badge([
                                        html.I(className="fas fa-project-diagram me-2"),
                                        f"{len(projects)} projet{'s' if len(projects) > 1 else ''}"
                                    ], color="primary", className="mb-3"),
                                    html.Ul([
                                        html.Li([
                                            html.I(className="fas fa-folder me-2", style={"color": "#6c757d"}),
                                            project
                                        ], className="mb-2", style={"list-style": "none"}) 
                                        for project in projects
                                    ], className="ps-0")
                                ])
                            ])
                        ], className="shadow-sm border-0 h-100"),
                        xs=12, sm=6, md=4, lg=3, className="mb-4"
                    )
                    for user_dict in users_with_projects
                    for user_name, projects in user_dict.items()
                ])
            ], fluid=True, className="mt-5")

    def layout(self):
        """Enhanced User List with Add User Modal"""
        users_display = self.get_users_display()
        
        return dbc.Container([
            # Header with title and controls
            dbc.Row([
                dbc.Col([
                    html.H1([
                        html.I(className="fas fa-users me-3"),
                        "Collaborateurs"
                    ], className="mb-0", style={"color": "#2c3e50", "font-weight": "600"}),
                    html.P("Gérez votre équipe BIM et leurs rôles", 
                          className="text-muted mb-0", style={"font-size": "0.9rem"})
                ], width=6),
                dbc.Col([
                    dbc.ButtonGroup([
                        dbc.Button([
                            html.I(className="fas fa-th-large me-2"),
                            "Vue Carte"
                        ], id="btn-user-card-view", color="primary", outline=True, 
                           active=self.view_type == "Vue Carte", size="sm"),
                        dbc.Button([
                            html.I(className="fas fa-table me-2"),
                            "Vue Tableau"
                        ], id="btn-user-table-view", color="primary", outline=True, 
                           active=self.view_type == "Vue Tableau", size="sm"),
                    ], className="me-3"),
                    dbc.Button([
                        html.I(className="fas fa-user-plus me-2"),
                        "Nouveau Collaborateur"
                    ], id="open-add-user", color="success", size="sm", n_clicks=0)
                ], width=6, className="text-end d-flex justify-content-end align-items-center")
            ], className="mb-4 pb-3", style={"border-bottom": "1px solid #e9ecef"}),

            # Users display area
            dbc.Row(id="user-list", children=users_display, className="g-4"),
            
            # Projects by users section
            dbc.Row(id="user-projects-lst", children=self.projects_by_users(), className="g-4"),

            # Add user modal
            self.add_user_modal(),
            
            # Toast for notifications
            dbc.Toast(
                id="user-toast",
                header="Notification",
                is_open=False,
                dismissable=True,
                duration=4000,
                style={"position": "fixed", "top": 20, "right": 20, "width": 350, "z-index": 1050}
            )
        ], fluid=True, style={"padding": "30px", "background": "#f8f9fa", "min-height": "100vh"})

    def add_user_modal(self):
        """Enhanced modal for adding new users"""
        return dbc.Modal([
            dbc.ModalHeader([
                dbc.ModalTitle([
                    html.I(className="fas fa-user-plus me-2"),
                    "Ajouter un Nouveau Collaborateur"
                ], style={"color": "#2c3e50"})
            ]),
            dbc.ModalBody([
                dbc.Form([
                    # User Name
                    dbc.Row([
                        dbc.Col([
                            dbc.Label([
                                html.I(className="fas fa-user me-2"),
                                "Nom du Collaborateur *"
                            ], className="fw-bold"),
                            dbc.Input(
                                id="user-name", 
                                type="text", 
                                placeholder="Ex: Jean Dupont",
                                className="mb-3"
                            ),
                            dbc.FormFeedback("Veuillez saisir un nom", type="invalid")
                        ])
                    ]),
                    
                    # Email
                    dbc.Row([
                        dbc.Col([
                            dbc.Label([
                                html.I(className="fas fa-envelope me-2"),
                                "Adresse Email *"
                            ], className="fw-bold"),
                            dbc.Input(
                                id="user-email", 
                                type="email", 
                                placeholder="Ex: jean.dupont@entreprise.com",
                                className="mb-3"
                            ),
                            dbc.FormFeedback("Veuillez saisir une adresse email valide", type="invalid")
                        ])
                    ]),
                    
                    # Role
                    dbc.Row([
                        dbc.Col([
                            dbc.Label([
                                html.I(className="fas fa-user-tag me-2"),
                                "Rôle *"
                            ], className="fw-bold"),
                            dcc.Dropdown(
                                id="user-role",
                                options=[
                                    {"label": "🏗️ BIM MANAGER", "value": "BIM MANAGER"},
                                    {"label": "🔧 COORDINATEUR", "value": "COORDINATEUR"},
                                    {"label": "👨‍💼 CHEF DE PROJET", "value": "CHEF DE PROJET"},
                                    {"label": "📐 DESSINATEUR", "value": "DESSINATEUR"}
                                ],
                                placeholder="Sélectionnez un rôle",
                                className="mb-3"
                            )
                        ])
                    ]),
                    
                    # Info box
                    dbc.Alert([
                        html.I(className="fas fa-info-circle me-2"),
                        "Un email avec les identifiants de connexion sera automatiquement envoyé au collaborateur."
                    ], color="info", className="mt-3")
                ])
            ]),
            dbc.ModalFooter([
                dbc.Button([
                    html.I(className="fas fa-times me-2"),
                    "Annuler"
                ], id="close-add-user", color="secondary", outline=True),
                dbc.Button([
                    html.I(className="fas fa-paper-plane me-2"),
                    "Créer et Inviter"
                ], id="submit-add-user", color="success", className="ms-2"),
            ])
        ], id="add-user-modal", is_open=False, size="lg")

    def get_users_display(self):
        """Get users display based on current view type"""
        if self.view_type == "Vue Carte":
            return self.get_user_cards()
        else:
            return self.get_user_table()

    def get_user_cards(self):
        """Enhanced user cards display"""
        with current_app.app_context():
            users = dbBimUsers.query.all()
            
            if not users:
                return [
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.Div([
                                    html.I(className="fas fa-users", style={"font-size": "3rem", "color": "#6c757d"}),
                                    html.H5("Aucun collaborateur", className="mt-3 text-muted"),
                                    html.P("Commencez par ajouter votre premier collaborateur", className="text-muted")
                                ], className="text-center py-5")
                            ])
                        ], className="border-0 shadow-sm")
                    ], width=12)
                ]
            
            return [
                dbc.Col(
                    html.A(
                        dbc.Card([
                            dbc.CardBody([
                                dbc.Row([
                                    dbc.Col([
                                        html.Div([
                                            html.I(className="fas fa-user-circle", 
                                                   style={"font-size": "2.5rem", "color": "#6c757d"}),
                                        ], className="text-center mb-3"),
                                        html.H5(u.name, className="card-title text-center mb-2", 
                                               style={"color": "#2c3e50"}),
                                        html.P([
                                            html.I(className="fas fa-envelope me-2", style={"color": "#6c757d"}),
                                            u.email
                                        ], className="card-text text-muted text-center mb-2", 
                                           style={"font-size": "0.9rem"}),
                                        html.Div([
                                            dbc.Badge(
                                                [self.get_role_icon(u.role), " ", u.role],
                                                color=self.get_role_color(u.role),
                                                className="px-3 py-2"
                                            )
                                        ], className="text-center")
                                    ], width=12)
                                ]),
                                html.Hr(className="my-3"),
                                dbc.Row([
                                    dbc.Col([
                                        html.Small([
                                            html.I(className="fas fa-clock me-1"),
                                            "Membre depuis ", datetime.now().strftime("%m/%Y")
                                        ], className="text-muted text-center d-block")
                                    ], width=12)
                                ])
                            ])
                        ], className="h-100 shadow-sm border-0 card-hover", style={
                            "transition": "all 0.3s ease",
                            "cursor": "pointer",
                            "transform": "translateY(0)"
                        }),
                        href=f"/BIMSYS/bimuser/{u.id}",
                        style={"textDecoration": "none", "color": "inherit"}
                    ),
                    width=4, className="mb-4"
                )
                for u in users
            ]

    def get_user_table(self):
        """Enhanced table view for users"""
        with current_app.app_context():
            users = dbBimUsers.query.all()
            
            if not users:
                return [
                    dbc.Col([
                        dbc.Alert([
                            html.I(className="fas fa-info-circle me-2"),
                            "Aucun collaborateur disponible. Ajoutez votre premier collaborateur pour commencer."
                        ], color="info", className="text-center")
                    ], width=12)
                ]

            # Create enhanced table
            table_header = [
                html.Thead([
                    html.Tr([
                        html.Th([
                            html.I(className="fas fa-user me-2"),
                            "Collaborateur"
                        ], style={"background-color": "#f8f9fa", "border": "none"}),
                        html.Th([
                            html.I(className="fas fa-envelope me-2"),
                            "Email"
                        ], style={"background-color": "#f8f9fa", "border": "none"}),
                        html.Th([
                            html.I(className="fas fa-user-tag me-2"),
                            "Rôle"
                        ], style={"background-color": "#f8f9fa", "border": "none"}),
                        html.Th([
                            html.I(className="fas fa-project-diagram me-2"),
                            "Projets"
                        ], style={"background-color": "#f8f9fa", "border": "none"}),
                        html.Th("Actions", style={"background-color": "#f8f9fa", "border": "none"})
                    ])
                ])
            ]
            
            table_body = [
                html.Tbody([
                    html.Tr([
                        html.Td([
                            html.Div([
                                html.I(className="fas fa-user-circle me-3", 
                                       style={"font-size": "1.5rem", "color": "#6c757d"}),
                                html.A(
                                    u.name,
                                    href=f"/BIMSYS/bimuser/{u.id}",
                                    style={"color": "#2c3e50", "text-decoration": "none", "font-weight": "500"}
                                )
                            ], className="d-flex align-items-center")
                        ]),
                        html.Td([
                            html.A(
                                u.email,
                                href=f"mailto:{u.email}",
                                style={"color": "#6c757d", "text-decoration": "none"}
                            )
                        ]),
                        html.Td([
                            dbc.Badge(
                                [self.get_role_icon(u.role), " ", u.role],
                                color=self.get_role_color(u.role),
                                className="px-2 py-1"
                            )
                        ]),
                        html.Td([
                            dbc.Badge(
                                f"{len(getattr(u, 'projects', []))} projet{'s' if len(getattr(u, 'projects', [])) != 1 else ''}",
                                color="secondary" if len(getattr(u, 'projects', [])) == 0 else "primary",
                                pill=True
                            )
                        ]),
                        html.Td([
                            dbc.ButtonGroup([
                                dbc.Button([
                                    html.I(className="fas fa-eye")
                                ], color="primary", size="sm", outline=True, 
                                   href=f"/BIMSYS/bimuser/{u.id}",
                                   title="Voir le profil"),
                                dbc.Button([
                                    html.I(className="fas fa-envelope")
                                ], color="info", size="sm", outline=True,
                                   href=f"mailto:{u.email}",
                                   title="Envoyer un email"),
                            ], size="sm")
                        ])
                    ], style={"border-bottom": "1px solid #e9ecef"})
                    for u in users
                ])
            ]

            return [
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader([
                            html.H4([
                                html.I(className="fas fa-users me-2"),
                                "Équipe BIM"
                            ], className="mb-0", style={"color": "#2c3e50"})
                        ], style={"background-color": "#f8f9fa", "border-bottom": "2px solid #e9ecef"}),
                        dbc.CardBody([
                            html.Div([
                                dbc.Table(
                                    table_header + table_body,
                                    responsive=True,
                                    hover=True,
                                    className="mb-0"
                                )
                            ])
                        ])
                    ], className="shadow-sm border-0")
                ], width=12)
            ]

    def get_role_color(self, role):
        """Return appropriate color for role badge"""
        role_colors = {
            "BIM MANAGER": "primary",
            "COORDINATEUR": "success",
            "CHEF DE PROJET": "warning",
            "DESSINATEUR": "info"
        }
        return role_colors.get(role, "secondary")

    def get_role_icon(self, role):
        """Return appropriate icon for role"""
        role_icons = {
            "BIM MANAGER": html.I(className="fas fa-crown"),
            "COORDINATEUR": html.I(className="fas fa-cogs"),
            "CHEF DE PROJET": html.I(className="fas fa-user-tie"),
            "DESSINATEUR": html.I(className="fas fa-drafting-compass")
        }
        return role_icons.get(role, html.I(className="fas fa-user"))

    def register_callbacks(self):
        """Register Callbacks for Modal Control and User Addition"""

        @self.app.callback(
            [Output("add-user-modal", "is_open"),
             Output("user-name", "value"),
             Output("user-email", "value"),
             Output("user-role", "value"),
             Output("user-list", "children"),
             Output("user-projects-lst", "children"),
             Output("user-toast", "is_open"),
             Output("user-toast", "children"),
             Output("user-toast", "icon"),
             Output("btn-user-card-view", "active"),
             Output("btn-user-table-view", "active")],
            [Input("open-add-user", "n_clicks"),
             Input("close-add-user", "n_clicks"),
             Input("submit-add-user", "n_clicks"),
             Input("btn-user-card-view", "n_clicks"),
             Input("btn-user-table-view", "n_clicks")],
            [State("add-user-modal", "is_open"),
             State("user-name", "value"),
             State("user-email", "value"),
             State("user-role", "value")],
            prevent_initial_call=True
        )
        def handle_user_interactions(open_click, close_click, submit_click, 
                                   card_view_click, table_view_click,
                                   is_open, name, email, role):
            
            ctx = callback_context
            if not ctx.triggered:
                return (no_update, no_update, no_update, no_update, no_update, 
                       no_update, no_update, no_update, no_update, no_update, no_update)

            button_id = ctx.triggered[0]["prop_id"].split(".")[0]
            
            # Handle view switching
            if button_id == "btn-user-card-view":
                self.view_type = "Vue Carte"
                users_display = self.get_users_display()
                projects_display = self.projects_by_users()
                return (no_update, no_update, no_update, no_update, users_display, projects_display,
                       no_update, no_update, no_update, True, False)
            
            elif button_id == "btn-user-table-view":
                self.view_type = "Vue Tableau"
                users_display = self.get_users_display()
                projects_display = self.projects_by_users()
                return (no_update, no_update, no_update, no_update, users_display, projects_display,
                       no_update, no_update, no_update, False, True)

            # Handle modal operations
            elif button_id == "open-add-user":
                return (True, no_update, no_update, no_update, no_update, no_update,
                       no_update, no_update, no_update, 
                       self.view_type == "Vue Carte", self.view_type == "Vue Tableau")

            elif button_id == "close-add-user":
                return (False, "", "", None, no_update, no_update,
                       no_update, no_update, no_update,
                       self.view_type == "Vue Carte", self.view_type == "Vue Tableau")

            elif button_id == "submit-add-user":
                # Validate required fields
                if not name or not name.strip():
                    return (is_open, no_update, no_update, no_update, no_update, no_update,
                           True, "Veuillez saisir un nom de collaborateur", "danger",
                           self.view_type == "Vue Carte", self.view_type == "Vue Tableau")
                
                if not email or not email.strip():
                    return (is_open, no_update, no_update, no_update, no_update, no_update,
                           True, "Veuillez saisir une adresse email", "danger",
                           self.view_type == "Vue Carte", self.view_type == "Vue Tableau")
                
                if not role:
                    return (is_open, no_update, no_update, no_update, no_update, no_update,
                           True, "Veuillez sélectionner un rôle", "danger",
                           self.view_type == "Vue Carte", self.view_type == "Vue Tableau")

                # Basic email validation
                if "@" not in email or "." not in email:
                    return (is_open, no_update, no_update, no_update, no_update, no_update,
                           True, "Veuillez saisir une adresse email valide", "danger",
                           self.view_type == "Vue Carte", self.view_type == "Vue Tableau")

                try:
                    with current_app.app_context():
                        # Check if user with same email already exists
                        existing_user = dbBimUsers.query.filter_by(email=email.strip()).first()
                        if existing_user:
                            return (is_open, no_update, no_update, no_update, no_update, no_update,
                                   True, f"Un collaborateur avec l'email {email} existe déjà", "danger",
                                   self.view_type == "Vue Carte", self.view_type == "Vue Tableau")
                        
                        # Create new user
                        new_user = dbBimUsers(
                            name=name.strip(),
                            email=email.strip(),
                            role=role
                        )
                        
                        db.session.add(new_user)
                        db.session.commit()
                        
                        # Send notification email
                        try:
                            self.notify_subscription(name.strip(), email.strip(), new_user.password)
                            toast_message = f"Collaborateur '{name}' créé avec succès! Email d'invitation envoyé."
                        except Exception as e:
                            toast_message = f"Collaborateur '{name}' créé, mais l'email n'a pas pu être envoyé."
                        
                        users_display = self.get_users_display()
                        projects_display = self.projects_by_users()
                        
                        return (False, "", "", None, users_display, projects_display,
                               True, toast_message, "success",
                               self.view_type == "Vue Carte", self.view_type == "Vue Tableau")
                        
                except Exception as e:
                    return (is_open, no_update, no_update, no_update, no_update, no_update,
                           True, f"Erreur lors de la création du collaborateur: {str(e)}", "danger",
                           self.view_type == "Vue Carte", self.view_type == "Vue Tableau")

            return (no_update, no_update, no_update, no_update, no_update, no_update,
                   no_update, no_update, no_update, 
                   self.view_type == "Vue Carte", self.view_type == "Vue Tableau")

    def notify_subscription(self, name, email, password):
        """Enhanced email notification with better formatting"""
        try:
            mailjet = Client(
                auth=("1855d6eacbcc8dc12442521492fb8d76", "7afee7a226886cb7362f7102e7e151f5"),
                version='v3.1'
            )

            data = {
                'Messages': [
                    {
                        "From": {
                            "Email": "mrabetyoussef95@gmail.com",
                            "Name": "BIMSYS - Plateforme BIM"
                        },
                        "To": [
                            {
                                "Email": email,
                                "Name": name
                            }
                        ],
                        "Subject": "🎉 Bienvenue sur BIMSYS - Vos identifiants de connexion",
                        "TextPart": f"""
Bonjour {name},

Félicitations ! Un compte vient d'être créé pour vous sur la plateforme BIMSYS.

=== VOS IDENTIFIANTS ===
📧 Email : {email}
🔑 Mot de passe : {password}

🌐 Connexion : https://ton-domaine/BIMSYS/login

Nous vous recommandons de changer votre mot de passe lors de votre première connexion.

Bienvenue dans l'équipe !

---
L'équipe BIMSYS
                        """,
                        "HTMLPart": f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; color: white; border-radius: 10px 10px 0 0; }}
        .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
        .credentials {{ background: white; padding: 20px; border-radius: 8px; border-left: 4px solid #667eea; margin: 20px 0; }}
        .button {{ display: inline-block; background: #667eea; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
        .footer {{ text-align: center; color: #666; font-size: 14px; margin-top: 30px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎉 Bienvenue sur BIMSYS</h1>
            <p>Votre plateforme BIM professionnelle</p>
        </div>
        <div class="content">
            <h2>Bonjour {name},</h2>
            <p>Félicitations ! Un compte vient d'être créé pour vous sur la plateforme <strong>BIMSYS</strong>.</p>
            
            <div class="credentials">
                <h3>🔐 Vos identifiants de connexion :</h3>
                <p><strong>📧 Email :</strong> {email}</p>
                <p><strong>🔑 Mot de passe :</strong> <code style="background:#f0f0f0; padding:4px 8px; border-radius:4px;">{password}</code></p>
            </div>
            
            <div style="text-align: center;">
                <a href="https://ton-domaine/BIMSYS/login" class="button">🚀 Se connecter maintenant</a>
            </div>
            
            <p><strong>💡 Conseil :</strong> Nous vous recommandons de changer votre mot de passe lors de votre première connexion pour des raisons de sécurité.</p>
            
            <div class="footer">
                <p>Bienvenue dans l'équipe ! 🎊</p>
                <p>---<br>L'équipe BIMSYS</p>
            </div>
        </div>
    </div>
</body>
</html>
                        """
                    }
                ]
            }

            result = mailjet.send.create(data=data)
            print(f"Email sent - Status: {result.status_code}")
            if result.status_code != 200:
                print(f"Email error: {result.json()}")
            
        except Exception as e:
            print(f"Error sending email: {str(e)}")
            raise e