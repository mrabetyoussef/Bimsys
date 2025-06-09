import dash_bootstrap_components as dbc  
from dash import dcc, html, Input, Output , callback_context
from app.pages.home import HomePage
from app.pages.projects import ProjectsPage
from app.pages.project import ProjectPage
from app.pages.bimuser import BimUser
from app.pages.task import TaskPage
from app.pages.phase import Phase
from app.pages.login import LoginPage
import feffery_antd_components as fac
from app.pages.user import UserPage

import dash
from flask_login import current_user
from app.pages import BimUsers
from database.model import BimUsers as dbBimUser

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
        self.user = UserPage(self.dash_app)

        
        self.dash_app.layout = dbc.Container([
            dcc.Location(id="url", refresh=False),

            
            dbc.Row(
                dbc.Col(
                    html.Div(id="page-content", style={
                        "padding": "30px",
                        "background": "",
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
            Input("url", "pathname") ,
            # Input("logout-button", "n_clicks"),

        )
        def display_page(pathname ):

            if not current_user.is_authenticated and pathname != "/BIMSYS/login" :                
                return self.login_layout
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

            if current_user:
                email =  current_user.email
                user_avatar =self.email_to_initials(email)
            else :
                user_avatar = ""

            return self.build_layout(user_avatar,content)

    def email_to_initials(self,email: str) -> str:
        """
        Convert an email address to initials.
        Example: john.doe@example.com → JD
                sarah@example.com → S
        """
        if not email or "@" not in email:
            return ""

        username = email.split("@")[0]
        parts = [p for p in username.replace(".", " ").replace("_", " ").split() if p]
        initials = "".join(p[0].upper() for p in parts[:2])
        return initials


    def build_layout(self, user_avatar, content):
        HEADER_HEIGHT = "64px"

        return fac.AntdLayout([

        # ===== HEADER =====
        fac.AntdHeader(
            style={
                "position": "fixed",
                "top": "0",
                "left": "0",
                "margin": "0",
                "zIndex": 10,
                "width": "100%",
                "background": "#fff",
                "boxShadow": "0 2px 4px rgba(0,0,0,0.1)",
                "height": HEADER_HEIGHT,
                "display": "flex",
                "alignItems": "center",
                "padding": "0 16px",
            },
            children=dbc.Container(
                dbc.Row(
                    [
                        dbc.Col(html.H2("BIM SYSTEM", className="mb-0"), width="auto"),
                        dbc.Col(html.Div(), width=True),  # spacer
                        dbc.Col(
                            fac.AntdDropdown(
                                fac.AntdAvatar(
                                    mode="text",
                                    text=user_avatar,
                                    size="large",
                                    style={"background": "#grey", "cursor": "pointer"}
                                ),
                                menuItems=[{
                                    "title": dbc.Button(
                                        [fac.AntdIcon(icon="logout"), " Se déconnecter"],
                                        id="logout-button",
                                        color="link",
                                        n_clicks=0,
                                        style={"padding": 0, "textDecoration": "none"}
                                    )
                                }],
                                trigger="hover",
                                placement="bottomRight",
                            ),
                            width="auto",
                        ),
                    ],
                    align="center",
                    className="h-100",
                ),
                fluid=True,
                className="px-0"  # ← remove default horizontal padding
            )
        ),

        # ===== MAIN LAYOUT =====
        fac.AntdLayout([

            # Sidebar (Sider)
          fac.AntdSider(
    # wrap the Menu in a list, as per the docs
    [
        fac.AntdMenu(
            menuItems=[
                {
                    'component': 'Item',
                    'props': {
                        'key': 'home',
                        'title': 'Accueil',
                        'icon': 'antd-home',
                        'href': '/BIMSYS/'
                    }
                },
                {
                    'component': 'Item',
                    'props': {
                        'key': 'projects',
                        'title': 'Projets',
                        'icon': 'antd-folder-open',
                        'href': '/BIMSYS/projects'
                    }
                },
                {
                    'component': 'Item',
                    'props': {
                        'key': 'collaborateurs',
                        'title': 'Collaborateurs',
                        'icon': 'antd-team',
                        'href': '/BIMSYS/collaborateurs'
                    }
                },
            ],
            mode='inline',                     # vertical menu
            defaultSelectedKey='home',      # which one is active
            style={
                'height': '100%',
                'overflow': 'hidden auto',
                'boxShadow': '0 2px 6px rgba(0,0,0,0.1)',
                'borderRadius': '8px',
                'backgroundColor': 'white'
            },
        )
    ],
    collapsible=True,
    collapsedWidth=60,
    
    breakpoint='lg',
    style={
        'backgroundColor': 'white',
        'padding': '60px 0px',
    },
),


            # Content Area
            fac.AntdContent(
                style={
                    "margin": "20px",
                    "padding": "30px",
                    "background": "white",
                    "borderRadius": "10px",
                    "boxShadow": "0 2px 6px rgba(0,0,0,0.05)",
                    "minHeight": f"calc(100vh - {HEADER_HEIGHT})",
                    "marginTop": HEADER_HEIGHT  
                },
                children=content
            ),

        ], style={"display": "flex"})

    ])