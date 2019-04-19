import os
import datetime
import platform

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '$h_(7hidj&1#6h)j(h2jw1!h!+tuo5*#5ysu-2&l^!0(^%hv&_'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = [
    'indy_community.apps.IndyCoreConfig',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'background_task',
    'rest_framework',
    'indy_api',
    'indy_community_demo',
]

def file_ext():
    if platform.system() == 'Linux':
        return '.so'
    elif platform.system() == 'Darwin':
        return '.dylib'
    elif platform.system() == 'Windows':
        return '.dll'
    else:
        return '.so'

INDY_CONFIG = {
    'storage_dll': 'libindystrgpostgres' + file_ext(),
    'storage_entrypoint': 'postgresstorage_init',
    'payment_dll': 'libnullpay' + file_ext(),
    'payment_entrypoint': 'nullpay_init',
    'wallet_config': {'id': '', 'storage_type': 'postgres_storage'},
    'wallet_credentials': {'key': ''},
    'storage_config': {'url': 'localhost:5432'},
    'storage_credentials': {'account': 'postgres', 'password': 'mysecretpassword', 'admin_account': 'postgres', 'admin_password': 'mysecretpassword'},
    'vcx_agency_url': 'http://localhost:8080',
    'vcx_agency_did': 'VsKV7grR1BUE29mG2Fm2kX',
    'vcx_agency_verkey': 'Hezce2UWMZ3wUhVkh2LfKSs8nDzWwzs2Win7EzNN3YaR',
    'vcx_payment_method': 'null',
    'vcx_enterprise_seed': '000000000000000000000000Trustee1',
    'vcx_institution_seed': '00000000000000000000000000000000',
    'vcx_genesis_path': '/tmp/atria-genesis.txt',
    'register_dids': True,
    'ledger_url': 'http://localhost:9000',
}

INDY_PROFILE_VIEW = 'indy_community.views.profile_view'
INDY_DATA_VIEW = 'indy_community.views.data_view'
INDY_WALLET_VIEW = 'indy_community.views.wallet_view'

INDY_CONVERSATION_CALLBACK = 'indy_community.agent_utils.conversation_callback'
INDY_CONNECTION_CALLBACK = 'indy_community.agent_utils.connection_callback'

REST_FRAMEWORK = {
    # Use Django's standard `django.contrib.auth` permissions,
    # or allow read-only access for unauthenticated users.
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
}

BACKGROUND_TASK_RUN_ASYNC = False
BACKGROUND_TASK_ASYNC_THREADS = 1
MAX_ATTEMPTS = 1
#MAX_RUN_TIME = 120

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

#AUTHENTICATION_BACKENDS = ['indy_community.indyauth.IndyBackend']

ROOT_URLCONF = 'indy_community_demo.urls'

#SESSION_COOKIE_AGE = 1800

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'indy_community_demo.wsgi.application'

DEFAULT_USER_ROLE = 'User'
DEFAULT_ORG_ROLE = 'Admin'

LOGOUT_REDIRECT_URL = '/'

# Database
# https://docs.djangoproject.com/en/2.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

AUTH_USER_MODEL = 'indy_community.IndyUser'

# override to create app-specific models during data loading
INDY_ORGANIZATION_MODEL = 'indy_community.IndyOrganization'
INDY_ORG_RELATION_MODEL = 'indy_community.IndyOrgRelationship'

# Password validation
# https://docs.djangoproject.com/en/2.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/2.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

gettext = lambda s: s
LANGUAGES = (
    ('en', gettext('English')),
    ('es', gettext('Spanish')),
    ('zh-hans', gettext('Chinese')),
    ('fr', gettext('French')),
)
MODELTRANSLATION_DEFAULT_LANGUAGE = 'en'
MODELTRANSLATION_TRANSLATION_REGISTRY = "atriacalendar.translation"

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.1/howto/static-files/

STATIC_URL = '/static/'
