from flask import Blueprint, request

event_routes = Blueprint("events", __name__)

@event_routes.route("/event/log", methods=["POST"])
def log_event():
    data = request.get_json()

    return {"message" : "Logged"}, 201