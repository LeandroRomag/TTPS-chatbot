from flask import Blueprint, render_template, redirect, url_for, request, flash

user_blueprint = Blueprint("user", __name__, url_prefix="/user")

@user_blueprint.get("/")
def index():
    return render_template("user/index.html", active_page='usuarios')

@user_blueprint.get("/create")
def create():
    return render_template("user/create.html", active_page='usuarios')

@user_blueprint.post("/create")
def create_post():
    return render_template("user/create.html", active_page='usuarios')
