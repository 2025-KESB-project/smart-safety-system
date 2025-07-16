from .core import core_routes
from .events import event_routes

def register_routes(app):
    app.register_blueprint(core_routes)
    app.register_blueprint(event_routes)