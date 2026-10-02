from functools import wraps
import io
import os

from flask import Flask, flash, redirect, render_template, request, send_file, session, url_for

from database import create_user, get_user_by_id, init_db, verify_user
from generator import build_landing_html, slugify

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-key-change-me-in-production")

# Initialize SQLite database schema
init_db()

# Flask/Werkzeug will reject uploads larger than this. 40MB is generous for ~15 photos.
app.config["MAX_CONTENT_LENGTH"] = 40 * 1024 * 1024


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Por favor inicia sesión para acceder.", "error")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function


@app.route("/", methods=["GET"])
@login_required
def dashboard():
    """The internal form used to fill in a property's data and photos."""
    user = get_user_by_id(session["user_id"])
    return render_template("dashboard.html", user=user)


@app.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not username or not password:
            flash("Por favor completa todos los campos requeridos.", "error")
            return render_template("register.html", username=username)

        if password != confirm_password:
            flash("Las contraseñas no coinciden.", "error")
            return render_template("register.html", username=username)

        if len(password) < 6:
            flash("La contraseña debe tener al menos 6 caracteres.", "error")
            return render_template("register.html", username=username)

        try:
            user_id = create_user(username, password)
            session["user_id"] = user_id
            flash("¡Registro exitoso! Bienvenido.", "success")
            return redirect(url_for("dashboard"))
        except ValueError as exc:
            flash(str(exc), "error")
            return render_template("register.html", username=username)

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = verify_user(username, password)
        if user:
            session["user_id"] = user["id"]
            flash("¡Bienvenido de nuevo!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Usuario o contraseña incorrectos.", "error")
            return render_template("login.html", username=username)

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Has cerrado sesión correctamente.", "success")
    return redirect(url_for("login"))


@app.route("/generate", methods=["POST"])
@login_required
def generate():
    """Builds the self-contained landing page and returns it as a download."""
    try:
        html = build_landing_html(request.form, request.files)
    except ValueError as exc:
        flash(str(exc), "error")
        return redirect(url_for("dashboard"))

    filename = slugify(request.form.get("address_title", "propiedad")) + ".html"
    buf = io.BytesIO(html.encode("utf-8"))
    buf.seek(0)
    return send_file(
        buf,
        mimetype="text/html",
        as_attachment=True,
        download_name=filename,
    )


@app.errorhandler(413)
def too_large(_e):
    flash("Las fotos que subiste pesan demasiado en total (límite 40MB). Reduce la cantidad o el tamaño de las imágenes.", "error")
    return redirect(url_for("dashboard"))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
