from flask import Blueprint, render_template, redirect, url_for, request, flash

document_blueprint = Blueprint("document", __name__, url_prefix="/document")

@document_blueprint.get("/")
def index():
    return render_template("document/index.html", active_page='documentos')

@document_blueprint.get("/create")
def create():
    return render_template("document/create.html", active_page='documentos')

@document_blueprint.post("/create")
def create_post():
    return render_template("document/create.html", active_page='documentos')
