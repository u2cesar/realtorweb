import io
import os

from flask import Flask, flash, redirect, render_template, request, send_file, url_for

from generator import build_landing_html, slugify

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-key-change-me-in-production")

# Flask/Werkzeug will reject uploads larger than this. 40MB is generous for ~15 photos.
app.config["MAX_CONTENT_LENGTH"] = 40 * 1024 * 1024


@app.route("/", methods=["GET"])
def dashboard():
    """The internal form used to fill in a property's data and photos."""
    return render_template("dashboard.html")


@app.route("/generate", methods=["POST"])
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
