# Generador de landing pages — PM Real Home

Dashboard web en Flask para armar la landing page de una propiedad (dirección,
fotos, características, datos del asesor) y descargar un único archivo
`.html` **autocontenido** — todas las fotos quedan incrustadas como base64
dentro del mismo archivo, así que puedes subirlo tal cual a cualquier hosting
comercial sin subir carpetas de imágenes por separado.

La página generada incluye lo mismo que la landing hecha a mano:
- Hero a pantalla completa con animación de entrada
- Galería en cubo 3D (gira con flechas, teclado, swipe o solo)
- Contador animado del tamaño del lote
- Sección opcional del asesor con foto y "cartel" animado
- Botón flotante de WhatsApp + botón de compartir (Web Share API)
- Animaciones con GSAP + ScrollTrigger, con fallback si no cargan

## Requisitos

- Python 3.10 o más nuevo

## Correrlo en local

```bash
python -m venv .venv
source .venv/bin/activate        # En Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Abre `http://localhost:5000` en el navegador. La aplicación te pedirá iniciar
sesión o registrarte (`/register`). Una vez registrado e iniciada la sesión,
podrás acceder al formulario para generar las landing pages.

## Desplegar en Railway

1. Sube esta carpeta a un repositorio de GitHub (o usa `railway up` desde la
   CLI de Railway directamente sobre esta carpeta, sin necesidad de Git).
2. En [railway.app](https://railway.app), crea un nuevo proyecto → **Deploy
   from GitHub repo** (o el resultado de `railway up`).
3. Railway detecta automáticamente que es una app Python (por
   `requirements.txt`) y usa el `Procfile` para arrancarla con `gunicorn`.
   No necesitas configurar nada más — Railway define la variable `PORT`
   automáticamente y el `Procfile` ya la usa.
4. Cuando termine el deploy, Railway te da una URL pública
   (`algo.up.railway.app`) — ábrela y ahí está el dashboard.

### Variables de entorno (opcional)

| Variable     | Para qué sirve                                              | Obligatoria |
|--------------|---------------------------------------------------------------|-------------|
| `SECRET_KEY` | Firma las cookies de sesión (usadas para autenticación y mensajes)| No — pero se recomienda poner una en producción |
| `DATABASE_PATH` | Ruta del archivo SQLite para los usuarios | No — por defecto es `app.db` |

En Railway: **Settings → Variables → New Variable** para agregar `SECRET_KEY`
con cualquier texto largo y aleatorio.

## Límites y notas

- El límite de subida está puesto en 40MB en total (`app.py`,
  `MAX_CONTENT_LENGTH`) — de sobra para ~15 fotos ya comprimidas por la app.
  Puedes subirlo si lo necesitas.
- Cada foto se redimensiona automáticamente (máximo 1700px de lado largo) y
  se comprime a JPEG calidad 78 antes de incrustarla, para que el `.html`
  final no pese demasiado.
- El dashboard no guarda nada en una base de datos: cada envío genera el
  archivo al vuelo y lo entrega como descarga. Si quieres guardar un
  historial de propiedades generadas, sería el siguiente paso natural
  (agregar una base de datos o un bucket de almacenamiento).
- La página generada carga las fuentes (Google Fonts) y GSAP desde CDN
  públicos — necesita internet para verse con esas fuentes/animaciones
  exactas, pero si no hay internet cae de vuelta a una fuente y sin
  animaciones, sin romperse.
- El botón "Compartir" (Web Share API) solo funciona una vez la página esté
  servida por `https://` (no al abrir el archivo con doble clic).

## Estructura del proyecto

```
pm-landing-generator/
├── app.py                       # Rutas Flask (dashboard, registro, login, logout, generar)
├── database.py                  # Lógica de base de datos SQLite y gestión de usuarios
├── generator.py                 # Lógica: procesa el formulario y las fotos, renderiza la plantilla
├── requirements.txt
├── Procfile                     # Comando de arranque para Railway
├── templates/
│   ├── dashboard.html           # Formulario del dashboard
│   ├── login.html               # Formulario de inicio de sesión
│   ├── register.html            # Formulario de registro de usuario
│   └── landing_template.html    # Plantilla Jinja2 de la página final
└── static/
    └── dashboard.css            # Estilos SOLO del dashboard (la página generada no depende de esto)
```
