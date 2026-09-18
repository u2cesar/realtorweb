"""
Builds a self-contained real-estate landing page (single .html file, images
embedded as base64) from form data + uploaded photos.

Kept independent from Flask's own Jinja environment so it can be unit-tested
or reused from a CLI/script without spinning up the web app.
"""
import base64
import io
import os
import re
import unicodedata
from urllib.parse import quote

import jinja2
from PIL import Image, ImageOps

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")
_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(TEMPLATES_DIR),
    autoescape=True,
    trim_blocks=True,
    lstrip_blocks=True,
)

# ---------------------------------------------------------------- helpers --

def slugify(text: str) -> str:
    text = text or "propiedad"
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^\w\s-]", "", text).strip().lower()
    text = re.sub(r"[-\s]+", "-", text)
    return text or "propiedad"


def lines_to_list(raw: str) -> list[str]:
    if not raw:
        return []
    return [line.strip() for line in raw.splitlines() if line.strip()]


def digits_only(raw: str) -> str:
    return re.sub(r"[^\d]", "", raw or "")


def parse_int(raw: str):
    d = digits_only(raw)
    return int(d) if d else None


def format_thousands(n: int) -> str:
    return f"{n:,}"


def image_to_data_uri(file_storage, max_dim: int = 1700, quality: int = 78):
    """Reads an uploaded file, downsizes/compresses it, and returns a
    data: URI ready to embed directly in HTML. Returns None if no file
    was actually provided."""
    if file_storage is None or not getattr(file_storage, "filename", ""):
        return None

    img = Image.open(file_storage.stream)
    img = ImageOps.exif_transpose(img)  # respect phone camera orientation
    img = img.convert("RGB")

    w, h = img.size
    if max(w, h) > max_dim:
        ratio = max_dim / max(w, h)
        img = img.resize((max(1, int(w * ratio)), max(1, int(h * ratio))), Image.LANCZOS)

    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=quality, optimize=True)
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/jpeg;base64,{b64}"


def build_wa_link(number: str, message: str) -> str:
    number = digits_only(number)
    if not number:
        return "#"
    if message:
        return f"https://wa.me/{number}?text={quote(message)}"
    return f"https://wa.me/{number}"


# --------------------------------------------------------------- builder --

def build_landing_html(form, files) -> str:
    """`form` behaves like a Flask/Werkzeug MultiDict (request.form),
    `files` like request.files. Returns the finished HTML as a string."""

    def f(name, default=""):
        return (form.get(name) or default).strip()

    # ---- required fields -------------------------------------------------
    address_title = f("address_title")
    city_state = f("city_state")
    whatsapp_number = f("whatsapp_number")

    if not address_title:
        raise ValueError("Falta la dirección de la propiedad.")
    if not city_state:
        raise ValueError("Falta la ciudad / estado.")
    if not whatsapp_number:
        raise ValueError("Falta el número de WhatsApp del asesor.")

    hero_file = files.get("hero_photo")
    hero_image = image_to_data_uri(hero_file)
    if not hero_image:
        raise ValueError("Falta la foto principal (hero).")

    # ---- brand / meta ------------------------------------------------------
    brand_main = f("brand_main", "PM Real")
    brand_accent = f("brand_accent", "Home")
    brand_tagline = f("brand_tagline", "Propiedades seleccionadas.")
    brand_url = f("brand_url")
    favicon_emoji = f("favicon_emoji", "🏠")
    page_title = f("page_title") or f"{address_title} — {city_state} | {brand_main}{brand_accent}"
    meta_description = f("meta_description") or f"{address_title}, {city_state}. Ficha completa de la propiedad."

    # ---- hero ---------------------------------------------------------------
    hero_eyebrow = f("hero_eyebrow", f"{city_state}")
    hero_subtitle = f("hero_subtitle")

    beds = f("beds")
    baths = f("baths")
    lot_sqft_raw = f("lot_sqft")
    construction_sqft_raw = f("construction_sqft")
    price_pill = f("price_pill")
    extra_pill = f("extra_pill")

    hero_pills = []
    if beds:
        hero_pills.append(f"{beds} habitaciones")
    if baths:
        hero_pills.append(f"{baths} baños")
    lot_num = parse_int(lot_sqft_raw)
    if lot_num:
        hero_pills.append(f"Lote de {format_thousands(lot_num)} pies²")
    if construction_sqft_raw:
        cons_num = parse_int(construction_sqft_raw)
        if cons_num:
            hero_pills.append(f"{format_thousands(cons_num)} pies² de construcción")
    if price_pill:
        hero_pills.append(price_pill)
    if extra_pill:
        hero_pills.append(extra_pill)

    # ---- intro / opportunity block -----------------------------------------
    intro_kicker = f("intro_kicker", "La propiedad")
    intro_heading = f("intro_heading")
    intro_paragraphs = [p for p in [f("intro_paragraph_1"), f("intro_paragraph_2")] if p]

    figure_number = lot_num
    figure_label = f("figure_label", "pies² de lote")
    figure_rows = []
    if beds:
        figure_rows.append({"n": beds, "l": "Habitaciones"})
    if baths:
        figure_rows.append({"n": baths, "l": "Baños completos"})

    # ---- gallery / cube -----------------------------------------------------
    gallery_intro_text = f("gallery_intro_text", "Recorre cada espacio de la propiedad.")
    gallery_files = files.getlist("gallery_photos")
    gallery_captions = lines_to_list(f("gallery_captions"))

    photos = []
    for i, gf in enumerate(gallery_files):
        uri = image_to_data_uri(gf)
        if not uri:
            continue
        cap = gallery_captions[i] if i < len(gallery_captions) else f"Foto {i + 1}"
        photos.append({"src": uri, "cap": cap})

    if len(photos) < 2:
        raise ValueError("Sube al menos 2 fotos para la galería (además de la foto principal).")

    # ---- features -----------------------------------------------------------
    features_interior = lines_to_list(f("features_interior"))
    features_exterior = lines_to_list(f("features_exterior"))

    # ---- lifestyle band (optional) -------------------------------------------
    lifestyle_image = image_to_data_uri(files.get("lifestyle_photo"))
    lifestyle_heading = f("lifestyle_heading")
    lifestyle_text = f("lifestyle_text")
    lifestyle = None
    if lifestyle_image:
        lifestyle = {
            "image": lifestyle_image,
            "heading": lifestyle_heading or "Un espacio con potencial.",
            "text": lifestyle_text,
        }

    # ---- agent (optional) -----------------------------------------------------
    agent_photo = image_to_data_uri(files.get("agent_photo"))
    agent_name = f("agent_name")
    agent = None
    if agent_photo or agent_name:
        agent = {
            "photo": agent_photo,
            "name": agent_name or "Tu asesor(a)",
            "role_line": f("agent_role_line"),
            "bio": f("agent_bio"),
            "badge_text": f("agent_badge_text", "Su mejor inversión"),
        }

    # ---- contact / cta ----------------------------------------------------------
    whatsapp_message = f("whatsapp_message", f"Hola, vi la propiedad en {address_title} y me gustaría más información.")
    wa_link = build_wa_link(whatsapp_number, whatsapp_message)

    cta_heading = f("cta_heading", f"Agenda tu visita a {address_title}")
    cta_text = f("cta_text", "Escríbenos directo por WhatsApp y coordinamos un recorrido por la propiedad.")
    contact_name_line = agent["name"] if agent else f"{brand_main}{brand_accent}"

    share_title = f"{address_title} — {city_state}"
    share_text = hero_subtitle or f"{address_title}, {city_state}."

    context = {
        "page_title": page_title,
        "meta_description": meta_description,
        "favicon_emoji": favicon_emoji,
        "brand_main": brand_main,
        "brand_accent": brand_accent,
        "brand_tagline": brand_tagline,
        "brand_url": brand_url,
        "hero_image": hero_image,
        "hero_eyebrow": hero_eyebrow,
        "address_title": address_title,
        "city_state": city_state,
        "hero_subtitle": hero_subtitle,
        "hero_pills": hero_pills,
        "wa_link": wa_link,
        "intro_kicker": intro_kicker,
        "intro_heading": intro_heading,
        "intro_paragraphs": intro_paragraphs,
        "figure_number": figure_number,
        "figure_label": figure_label,
        "figure_rows": figure_rows,
        "gallery_intro_text": gallery_intro_text,
        "photos": photos,
        "features_interior": features_interior,
        "features_exterior": features_exterior,
        "lifestyle": lifestyle,
        "agent": agent,
        "cta_heading": cta_heading,
        "cta_text": cta_text,
        "contact_name_line": contact_name_line,
        "whatsapp_number_display": whatsapp_number,
        "share_title": share_title,
        "share_text": share_text,
    }

    template = _env.get_template("landing_template.html")
    return template.render(**context)
