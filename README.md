# claims-auth

A reusable Django authentication app with JWT, roles, pages, OTP-based forgot password, and email notifications.

---

## Integration Instructions

### 1. Copy Files into Your Project

Copy the entire `authenticate/` folder into your Django project root (same level as `manage.py`).
Also copy `utils.py` from the project root — it handles threaded email sending used by the auth views.

```
your-project/
├── manage.py
├── authenticate/       <- paste here
├── utils.py            <- also copy this file
└── your_project/
```

---

### 2. Install Required Packages

```bash
pip install djangorestframework djangorestframework-simplejwt django-cors-headers python-decouple
```

---

### 3. Add URL Include

In your project's `urls.py`, add:

```python
from django.urls import path, include

urlpatterns = [
    ...
    path('auth/', include('authenticate.urls')),
]
```

---

### 4. Copy Settings

Paste these lines at the **bottom** of your `settings.py`:

```python
from datetime import timedelta

MIDDLEWARE.insert(2, 'corsheaders.middleware.CorsMiddleware')
INSTALLED_APPS.extend(["rest_framework", "corsheaders"])
INSTALLED_APPS.append('authenticate.apps.AuthenticateConfig')

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': False,
}

CORS_ORIGIN_ALLOW_ALL = True

AUTH_USER_MODEL = 'authenticate.PortalUser'

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = config('EMAIL_HOST_USER')
SENDERS_NAME = "Meeting Portal"
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = f"{SENDERS_NAME} <{EMAIL_HOST_USER}>"
```

> `settings.py` must already have `from decouple import config` at the top for `config(...)` to work.

---

### 5. Add Credentials to `.env`

Create a `.env` file next to `manage.py` and add:

```env
SECRET_KEY=your-django-secret-key

DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

DB_ENGINE=django.db.backends.sqlite3
DB_NAME=db.sqlite3

EMAIL_HOST_USER=your-gmail@gmail.com
EMAIL_HOST_PASSWORD=your-gmail-app-password
```

> For `EMAIL_HOST_PASSWORD`, use a **Gmail App Password** (not your regular Gmail password).
> Generate one at: Google Account → Security → 2-Step Verification → App Passwords.

---

### 6. Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

---

### 7. Auto-Assign New Pages to Superadmin

This is handled automatically via a `post_save` signal in `authenticate/signals.py`.
Every time a new `PortalPages` object is created, it is automatically assigned to all roles named `superadmin`.
No extra setup needed — `apps.py` loads the signal on startup via `ready()`.
