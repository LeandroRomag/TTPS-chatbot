from flask import Blueprint, render_template
authentication_blueprint = Blueprint("authentication", __name__, url_prefix="/auth")

@authentication_blueprint.get("/login")
def login():
    return render_template("login.html")

@authentication_blueprint.post("/login")
def login_post():
    # login logic
    print("mostrar mensaje de login correcto y redireccionar a la pantalla de dashboard indicando credenciales correctas")
    return "login post"  # Placeholder - implement actual logic


@authentication_blueprint.get("/logout")
def logout():
    # logout logic
    print("mostrar mensaje de logout correcto y redireccionar a la pantalla de login") # return redirect(url_for("authentication.login"))

# controller para que un administrador cree otros usuarios
@authentication_blueprint.get("/create-admin")
def create_admin():
    return render_template("create_admin.html")


