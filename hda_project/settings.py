"""
Django settings for hda_project.
Projet : Plateforme Web H.D.A GLOBAL — Construction TCE & Aménagement
"""

from pathlib import Path
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config("SECRET_KEY", default="dev-key-insecure")
DEBUG = config("DEBUG", default=True, cast=bool)
ALLOWED_HOSTS = [h.strip() for h in config("ALLOWED_HOSTS", default="localhost,127.0.0.1,testserver").split(",") if h.strip()]

# Render (hébergement gratuit depuis GitHub) : le nom d'hôte https est fourni automatiquement
RENDER_HOST = config("RENDER_EXTERNAL_HOSTNAME", default="")
if RENDER_HOST:
    ALLOWED_HOSTS.append(RENDER_HOST)

# ── Production (DEBUG=False) : HTTPS derrière Caddy, cookies sécurisés, clé secrète obligatoire ──
if not DEBUG:
    from django.core.exceptions import ImproperlyConfigured
    if SECRET_KEY.startswith("dev-key") or "CHANGEZ" in SECRET_KEY or len(SECRET_KEY) < 40:
        raise ImproperlyConfigured("SECRET_KEY faible : générez-en une (voir docs/DEPLOIEMENT.md) avant de passer en production.")
    CSRF_TRUSTED_ORIGINS = [o.strip() for o in config(
        "CSRF_TRUSTED_ORIGINS", default=",".join(f"https://{h}" for h in ALLOWED_HOSTS if "." in h and h[0].isalpha())
    ).split(",") if o.strip()]
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")   # Caddy termine le HTTPS
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = config("SECURE_HSTS_SECONDS", default=0, cast=int)  # 31536000 une fois le HTTPS validé
    SECURE_HSTS_INCLUDE_SUBDOMAINS = False
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_REFERRER_POLICY = "same-origin"

# Applications
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
]

THIRD_PARTY_APPS = [
    "widget_tweaks",
    "crispy_forms",
    "crispy_bootstrap5",
]

LOCAL_APPS = [
    "core",
    "services",
    "clients",
    "demandes",
    "devis",
    "interventions",
    "assistant",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.middleware.locale.LocaleMiddleware",
]

ROOT_URLCONF = "hda_project.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "core.context_processors.parametres_entreprise",
            ],
        },
    },
]

WSGI_APPLICATION = "hda_project.wsgi.application"

# Base de données (PostgreSQL par défaut / Docker, SQLite optionnel pour dev local)
USE_SQLITE = config("USE_SQLITE", default=False, cast=bool)

if USE_SQLITE:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": config("POSTGRES_DB", default="hda_db"),
            "USER": config("POSTGRES_USER", default="hda_user"),
            "PASSWORD": config("POSTGRES_PASSWORD", default="hda_secret"),
            "HOST": config("DB_HOST", default="db"),
            "PORT": config("DB_PORT", default="5432"),
        }
    }

# Validation des mots de passe
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Internationalisation — Français par défaut, prêt pour Arabe / Anglais
LANGUAGE_CODE = "fr"
TIME_ZONE = "Africa/Casablanca"
USE_I18N = True
USE_L10N = True
USE_TZ = True
LANGUAGES = [
    ("fr", "Français"),
    ("ar", "العربية"),
    ("en", "English"),
]
LOCALE_PATHS = [BASE_DIR / "locale"]

# Fichiers statiques
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# Fichiers média (uploads : photos de chantier, logo, PDF de devis)
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Email
EMAIL_BACKEND = config(
    "EMAIL_BACKEND",
    default="django.core.mail.backends.console.EmailBackend",
)
EMAIL_HOST = config("EMAIL_HOST", default="smtp.gmail.com")
EMAIL_PORT = config("EMAIL_PORT", default=587, cast=int)
EMAIL_USE_TLS = config("EMAIL_USE_TLS", default=True, cast=bool)
EMAIL_HOST_USER = config("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default="")
DEFAULT_FROM_EMAIL = config("HDA_EMAIL", default="hda.global82@gmail.com")
EMAIL_TIMEOUT = 20  # secondes : ne jamais bloquer l'admin si le SMTP ne répond pas

# Contacts entreprise accessibles dans tout le projet
HDA_EMAIL = config("HDA_EMAIL", default="hda.global82@gmail.com")
HDA_PHONE = config("HDA_PHONE", default="+212661103988")

# Crispy Forms
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# Sécurité uploads : 10 Mo max, types autorisés (images uniquement pour les chantiers)
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10 Mo
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024

# ────────────────────────────────────────────────────────────────────────────
# Automatisation des devis (devis/auto.py + devis/ai.py)
# « l'IA propose, le moteur calcule, l'humain valide »
# ────────────────────────────────────────────────────────────────────────────

# URL publique du site (QR code et liens du portail de suivi dans le PDF)
SITE_URL = config("SITE_URL", default=f"https://{RENDER_HOST}" if RENDER_HOST else "http://localhost:8000")

# Sécurité du portail de suivi client (lien secret) : voir demandes/securite_suivi.py
SUIVI_VALIDITE_JOURS = config("SUIVI_VALIDITE_JOURS", default=90, cast=int)       # 0 = pas d'expiration
SUIVI_LIMITE_PAR_MINUTE = config("SUIVI_LIMITE_PAR_MINUTE", default=60, cast=int)  # requêtes / IP / minute

# Génération automatique d'un devis BROUILLON à la création d'une demande.
# Ne bloque jamais le flux du client (try/except côté demandes/views.py).
DEVIS_AUTO_A_LA_CREATION = config("DEVIS_AUTO_A_LA_CREATION", default=False, cast=bool)

# Génération automatique du devis brouillon dès que l'admin passe une demande
# au statut « Acceptée » (il relit puis clique « Envoyer au client »).
DEVIS_AUTO_A_L_ACCEPTATION = config("DEVIS_AUTO_A_L_ACCEPTATION", default=True, cast=bool)

# Clé API Anthropic — NE JAMAIS committer la clé : la mettre uniquement
# dans le fichier .env (non versionné). Sans clé, tout fonctionne : le devis
# est généré localement (catalogue + regex de surface), l'IA est optionnelle.
# Exemple .env : ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_API_KEY = config("ANTHROPIC_API_KEY", default="")
ANTHROPIC_MODEL = config("ANTHROPIC_MODEL", default="claude-sonnet-4-5-20250929")

# Extension « photos + vision » : au plus N photos de chantier (PieceJointe)
# analysées par le modèle de vision pour enrichir le brouillon. Seulement si
# ANTHROPIC_API_KEY est définie. Échec toléré (jamais bloquant).
DEVIS_VISION_MAX_PHOTOS = config("DEVIS_VISION_MAX_PHOTOS", default=3, cast=int)


# ────────────────────────────────────────────────────────────────────────────
# Assistant IA de l'administration (assistant/) — OpenRouter (modèles gratuits possibles)
# La clé se met UNIQUEMENT dans .env (jamais dans le code ni sur GitHub).
# ────────────────────────────────────────────────────────────────────────────
ASSISTANT_ENABLED = config("ASSISTANT_ENABLED", default=True, cast=bool)
OPENROUTER_API_KEY = config("OPENROUTER_API_KEY", default="")
# Liste de modèles essayés dans l'ordre (le suivant prend le relais en cas de quota / panne).
# « openrouter/free » = routeur OpenRouter qui choisit un modèle gratuit compatible avec les outils.
OPENROUTER_MODELS = config("OPENROUTER_MODELS", default="openrouter/free")
OPENROUTER_TIMEOUT = config("OPENROUTER_TIMEOUT", default=45, cast=int)
