from flask import Blueprint, jsonify, render_template
from src.web.controllers.auth_controller import login_required
from src.core.services import status_service

status_blueprint = Blueprint("status", __name__, url_prefix="/status")


@status_blueprint.get("/")
@login_required
def index():
    endpoints = status_service.get_endpoints()
    return render_template(
        "system/status.html",
        endpoints=endpoints,
        active_page="estado",
    )


@status_blueprint.get("/api/check-all")
@login_required
def check_all():
    results = status_service.check_all()
    return jsonify([r.to_dict() for r in results])


@status_blueprint.get("/api/check/<endpoint_id>")
@login_required
def check_single(endpoint_id):
    result = status_service.check_endpoint(endpoint_id)
    if result is None:
        return jsonify({"error": "Endpoint no encontrado"}), 404
    return jsonify(result.to_dict())
