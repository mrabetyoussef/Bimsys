from functools import wraps
from flask_login import current_user
from dash import callback_context

class Forbidden(Exception):
    pass

def roles_required_for_actions(allowed_roles, restricted_actions):
   
    def deco(fn):
        @wraps(fn)
        def wrapped(*args, **kwargs):
            btn = None
            if callback_context.triggered:
                btn = callback_context.triggered[0]["prop_id"].split(".")[0]

            if btn in restricted_actions:
                if not current_user.is_authenticated or current_user.role not in allowed_roles:
                    raise Forbidden("Accès restreint à cette action")
            return fn(*args, **kwargs)
        return wrapped
    return deco
