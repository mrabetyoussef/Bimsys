import dash
import dash_bootstrap_components as dbc  
from dash import dcc, html, Input, Output
from app.pages.home import HomePage
from app.pages.projects import ProjectsPage
from app.pages.project import ProjectPage
from app.pages import BimUsers

class DashApp:
    def __init__(self, flask_app):
        """Initialize Dash inside Flask with Bootstrap & Font Awesome"""
        self.dash_app = dash.Dash(
            __name__,
            server=flask_app,
            routes_pathname_prefix="/BIMSYS/",
            external_stylesheets=[dbc.themes.BOOTSTRAP, 
            "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css"],     suppress_callback_exceptions=True
        )
        self.dash_app.enable_dev_tools(debug=True, dev_tools_ui=True, dev_tools_props_check=True)


        self.projects_page = ProjectsPage(self.dash_app)  
        self.bimUsers = BimUsers(self.dash_app)


        self.dash_app.layout = dbc.Container([
            dcc.Location(id="url", refresh=False),

            dbc.Row([
                dbc.Col(html.Div([
                    html.H2("BIM SYSTEM", className="text-center", style={"display": "inline-block", "vertical-align": "middle"}),
                ], style={"display": "flex", "align-items": "center", "padding": "15px", "border-bottom": "2px solid #ddd"}), width=12)
            ], className="align-items-center"),

            dbc.Row([
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
                    width=3
                ),

                dbc.Col(html.Div(id="page-content", style={"padding": "30px", "background": "#ffffff", "border-radius": "10px"}), 
                        width=9, className="p-4"),
            ], className="g-0"),  
        ], fluid=True)

        self.register_callbacks()

    def register_callbacks(self):
        """Handle page navigation inside Dash"""
        @self.dash_app.callback(
            Output("page-content", "children"),
            Input("url", "pathname")  
        )
        def display_page(pathname):
            print(pathname)
            if pathname == "/BIMSYS/projects":
                return self.projects_page.layout()  # Use the pre-initialized instance
            elif pathname.startswith("/BIMSYS/project/"):
                project_id = pathname.split("/")[-1]
                return ProjectPage(project_id).layout()
            elif pathname.startswith("/BIMSYS/collaborateurs"):
                return self.bimUsers.layout()
            return HomePage().layout()
