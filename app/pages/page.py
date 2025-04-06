import dash_bootstrap_components as dbc
from dash import html, dcc, Input, Output, State, callback_context, no_update
from flask import current_app
from database.db import db
from database.model import BimUsers as dbBimUsers
from datetime import datetime
import pandas as pd
from dash import dcc
from dash import callback, Output, Input, ctx, dcc, MATCH , ALL
import pdb

class page:

    def __init__(self, app):
        """Initialize Users Page and Register Callbacks"""
        self.app = app
        self.register_callbacks()
        self.view_type = "Vue Carte"


    

    def layout(self):
        """Return User List with Add User Modal"""
        return dbc.Card("this is an empty page")



    
    def register_callbacks(self):
      pass