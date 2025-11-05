# django-clerk-sdk

Lightweight Django integration for Clerk authentication and user syncing.  
Provides:
- A custom Clerk-backed user model (ClerkUser) and migrations
- A runtime Clerk SDK wrapper with helpers to authenticate requests and create/sync Django users
- DRF authentication classes (cached and non-cached)
- Small utilities for caching, descriptors and config defaults

---

## Quick start

1. Install your project dependencies (Django, drf, httpx, clerk-backend-api, etc).
2. Add the package apps and set AUTH_USER_MODEL.
3. Configure Clerk settings and run migrations.

Example settings.py snippets:

```python
# filepath: c:\Users\Lakan\Dev\Python\django-clerk-sdk\sdk\settings.py
# Use the packaged default or set explicitly.
from django_clerk_sdk import defaults
AUTH_USER_MODEL = defaults.AUTH_USER_MODEL
# Equivalent explicit value (works when 'django_clerk_sdk.users' is in INSTALLED_APPS):
# AUTH_USER_MODEL = "users.ClerkUser"

INSTALLED_APPS = [
    # ... your apps ...
    "django_clerk_sdk",           # core package
    "django_clerk_sdk.users",     # users app (provides ClerkUser + migrations)
    # ... other apps ...
]

# Clerk configuration (required)
CLERK_SECRET_KEY = "sk_live_..."            # your Clerk secret
CLERK_AUTH_PARTIES = ["..."]                # authorized parties per your Clerk setup

# Optional: metrics collector for auth metrics
# CLERK_AUTH_METRICS_COLLECTOR = "path.to.YourCollectorClass"  # must expose .increment(name, amount, tags)
# From repo or project root (Windows)
python [manage.py](http://_vscodecontentref_/0) migrate
# filepath: example_usage.py
from django_clerk_sdk.core.auth.clerk import sdk

# In a Django view or middleware where [request](http://_vscodecontentref_/1) is available
def my_view(request):
    # create or fetch the Django user for the incoming Clerk-authenticated request
    user = sdk.create_or_get_django_user(request)
    # now use [user](http://_vscodecontentref_/2) as usual
    return HttpResponse(f"Hello {user.get_full_name()}")
# filepath: example_usage_class_api.py
from django_clerk_sdk.core.auth.clerk.sdk import ClerkSdk

# classproperty or classmethod access
secret = ClerkSdk.SECRET_KEY          # same as ClerkSdk.get_secret_key()
parties = ClerkSdk.AUTH_PARTIES       # same as ClerkSdk.get_auth_parties()

# get a convenience client (creates a client using SECRET_KEY)
client = ClerkSdk.sdk_client
# Note: prefer instance [sdk.client](http://_vscodecontentref_/3) at runtime to avoid repeated creation
# filepath: example_create_org.py
from django_clerk_sdk.core.auth.clerk import sdk

def create_org_for_partner(request, partner_obj):
    # ensures request is authenticated then creates org in Clerk
    org = sdk.create_organization(request, partner=partner_obj)
    return org
# filepath: c:\Users\Lakan\Dev\Python\django-clerk-sdk\sdk\settings.py
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "django_clerk_sdk.core.auth.clerk.authentication.CachedClerkAuthentication",
        # or "django_clerk_sdk.core.auth.clerk.authentication.SimpleClerkAuthentication"
    ],
}
# filepath: views.py
from rest_framework.views import APIView
from django_clerk_sdk.core.auth.clerk.authentication import CachedClerkAuthentication

class MyApiView(APIView):
    authentication_classes = [CachedClerkAuthentication]
    def get(self, request):
        return Response({"user": request.user.username})

Important configuration keys
AUTH_USER_MODEL — should point to the ClerkUser model. Use the provided default:
from django_clerk_sdk import defaults; AUTH_USER_MODEL = defaults.AUTH_USER_MODEL
or AUTH_USER_MODEL = "users.ClerkUser" (requires 'django_clerk_sdk.users' in INSTALLED_APPS)
CLERK_SECRET_KEY — required; Clerk API secret used to initialize the client
CLERK_AUTH_PARTIES — required; authorized parties for AuthenticateRequestOptions
CLERK_AUTH_METRICS_COLLECTOR — optional; import path or callable that yields an object exposing .increment(...)
Notes & best practices
Prefer the module-level sdk singleton (exported from django_clerk_sdk.core.auth.clerk) for runtime operations in views/middleware. It lazily constructs a client and is thread-safe.
The SDK will try to map users using clerk_user_id if your User model exposes that field; otherwise it falls back to primary email.
The package ships a simple user model (ClerkUser) and migrations. If you use your own custom user model, ensure it exposes fields expected by the SDK (username/email/image/last_active_at) or adapt the SDK mapping.
Use the provided DRF authentication classes to get caching and metrics hooks; configure CLERK_AUTH_METRICS_COLLECTOR to collect counters.
Development
Source is under src/django_clerk_sdk/.
Users app models and migration: src/django_clerk_sdk/users/.
Sample Django project (for local testing) is under sdk/.
To run the sample project:
Create a virtualenv, install dependencies
Configure environment vars (CLERK_SECRET_KEY etc.)
python sdk/manage.py migrate
python sdk/manage.py runserver
Files of interest
src/django_clerk_sdk/defaults.py
src/django_clerk_sdk/core/auth/clerk/sdk.py
src/django_clerk_sdk/core/auth/clerk/authentication.py
src/django_clerk_sdk/users/models.py
src/django_clerk_sdk/users/migrations/0001_initial.py
If you want more examples (middleware, unit tests, or an example project settings file), say which area to expand. ``````