from flask import Blueprint, jsonify

core_routes = Blueprint('core', __name__)

@core_routes.route("/status")
def status():
    return jsonify({"status" : "ok"})