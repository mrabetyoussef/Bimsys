import dash
import dash_bootstrap_components as dbc  
from dash import dcc, html, Input, Output
from app.pages.home import HomePage
from app.pages.projects import ProjectsPage
from app.pages.project import ProjectPage
from app.pages.bimuser import BimUser
from app.pages.task import TaskPage
from app.pages.phase import Phase
from app.pages.login import LoginPage
import feffery_antd_components as fac

from app.pages import BimUsers

class DashApp:

    def __init__(self, flask_app):
        """Initialize Dash inside Flask with Bootstrap & Font Awesome"""
        self.dash_app = dash.Dash(title="BIMSYS",
            name="BIMSYS"
            ,
            server=flask_app,
            routes_pathname_prefix="/BIMSYS/",
            external_stylesheets=[dbc.themes.BOOTSTRAP, 
            "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css"],     suppress_callback_exceptions=True
        )
        self.dash_app.enable_dev_tools(debug=True, dev_tools_ui=True, dev_tools_props_check=True)
        self.log_try = 0
        self.login_page = LoginPage(self.dash_app)
        self.login_layout = html.Div(self.login_page.layout())
        self.projects_page = ProjectsPage(self.dash_app)  
        self.bimUsers = BimUsers(self.dash_app)
        self.project = ProjectPage(self.dash_app)
        self.taskpage = TaskPage(self.dash_app)
        self.phase = Phase(self.dash_app)

    

        self.dash_app.layout = dbc.Container([
            dcc.Location(id="url", refresh=False),

            dbc.Row(
                [
                    dbc.Col(
                        html.H2("BIM SYSTEM", className="mb-0"),
                        width=True,
                    ),

                    dbc.Col(
                        fac.AntdDropdown(
                            fac.AntdAvatar(
                                mode = "text", text = "TF",
                                size='large',
                                style={'background': '#1890ff', 'cursor': 'pointer'},
                            ),
                            menuItems=[
                               {
                                'title': html.A(
                                    [html.A(dbc.Button("se déconnecter"), href = "/BIMSYS/phase")],
                                    href="/logout",
                                    style={'textDecoration': 'none', 'color': 'inherit'}
                                )
                            }
                            ],
                            trigger='hover',
                            placement='bottomRight',
                        ),
                        width="auto",
                    ),
                ],
                align="center",
                justify="between",
                className="py-3 border-bottom"
            ),

            # --- ZONE DE CONTENU ---
            dbc.Row(
                dbc.Col(
                    html.Div(id="page-content", style={
                        "padding": "30px",
                        "background": "#ffffff",
                        "border-radius": "10px",
                        "min-height": "80vh"
                    }),
                    width=12
                ),
                className="g-0 mt-4"
            )

        ], fluid=True)


        self.register_callbacks()



    def register_callbacks(self):
        """Handle page navigation inside Dash"""
        @self.dash_app.callback(
            Output("page-content", "children"),
            Input("url", "pathname") 
        )
        def display_page(pathname):
            from flask_login import current_user
            print(current_user)
            if not current_user.is_authenticated and pathname != "/BIMSYS/login" :                
                content =  self.login_layout
            if pathname == "/BIMSYS/login":
                return self.login_layout
            if pathname == "/BIMSYS/projects":
                content =  self.projects_page.layout()  # Use the pre-initialized instance
            elif pathname.startswith("/BIMSYS/project/"):
                project_id = pathname.split("/")[-1]
                content =  self.project.layout(project_id)
            elif pathname.startswith("/BIMSYS/collaborateurs"):
                content =  self.bimUsers.layout()
            elif  pathname.startswith("/BIMSYS/bimuser"):
                bimuser_id = pathname.split("/")[-1]
                content =  BimUser(bimuser_id).layout()
            elif  pathname.startswith("/BIMSYS/task"):
                task_id = pathname.split("/")[-1]
                content =  self.taskpage.layout(task_id)
            elif  pathname.startswith("/BIMSYS/phase"):
                phase_id = pathname.split("/")[-1]
                content =  self.phase.layout(phase_id)
            else : 
                content = HomePage().layout()
            return dbc.Row([

                dbc.Col(
                    dbc.Card([
                        dbc.Nav([
                            dbc.NavLink([
                                        html.I(className="fa fa-home me-2"),  
                                         "Accueil" ], 
                                        href="/BIMSYS/", active="exact", className="mb-2"),

                            dbc.NavLink([
                                html.I(className="fa fa-folder-open me-2"),  
                                "Projets"
                            ], href="/BIMSYS/projects", active="exact", className="mb-2"),

                            dbc.NavLink([
                                html.I(className="fa fa-folder-open me-2"),  
                                "Collaborateurs"
                            ], href="/BIMSYS/collaborateurs", active="exact", className="mb-2"),
                        ], vertical=True, pills=True),
                    ], body=True, style={
                        "height": "100vh",
                        "background": "#f8f9fa", "padding": "20px"
                    }),
                    width=3,
                ),
                dbc.Col(children =  content , style={"padding": "30px", "background": "#ffffff", "border-radius": "10px"})





            ])
