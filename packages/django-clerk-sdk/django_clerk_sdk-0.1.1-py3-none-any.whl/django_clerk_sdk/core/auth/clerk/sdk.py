"""Clerk SDK helper for Django applications.

This module provides:
- a thread-safe singleton `ClerkSdk` instance for runtime operations (preferred),
- both classmethod and classproperty accessors for configuration (implements option 1 and 3),
- helpers to authenticate requests, fetch Clerk users, and create/sync Django users.

Usage examples:
    # classmethod style (option 1)
    ClerkSdk.get_secret_key()
    ClerkSdk.get_auth_parties()

    # classproperty style (option 3)
    ClerkSdk.SECRET_KEY
    ClerkSdk.AUTH_PARTIES

    # runtime usage via the singleton instance
    sdk = ClerkSdk()
    django_user = sdk.create_or_get_django_user(request)
"""
from __future__ import annotations

import logging
import threading
import warnings
from typing import Any, Optional

import httpx
from clerk_backend_api import (
    AuthenticateRequestOptions,
    Clerk,
    CreateOrganizationRequestBody,
    EmailAddress,
)
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.exceptions import AuthenticationFailed

from django_clerk_sdk.core.utils.descriptors import classproperty

# Suppress noisy warnings from third-party libs
warnings.filterwarnings("ignore", module="clerk_backend_api")
warnings.filterwarnings("ignore", module="pydantic")

logger = logging.getLogger(__name__)

User = get_user_model()


# ----------------------------
# Exceptions
# ----------------------------
class ClerkSdkError(Exception):
    """Base error for SDK operations."""


class ConfigurationError(ClerkSdkError, ValueError):
    """Raised when required configuration is missing."""


# ----------------------------
# Clerk SDK implementation
# ----------------------------
class ClerkSdk:
    """Singleton wrapper around the Clerk Python client with Django helpers.

    Implements:
      - classmethod accessors (option 1): get_secret_key(), get_auth_parties()
      - classproperty accessors (option 3): SECRET_KEY, AUTH_PARTIES
      - instance-level lazy, thread-safe client and user helpers (preferred for runtime)
    """

    # Singleton bookkeeping
    _instance: Optional["ClerkSdk"] = None
    _instance_lock = threading.Lock()

    # ----- classmethod (option 1) accessors ---------------------------------
    @classmethod
    def get_secret_key(cls) -> str:
        """Return Clerk secret key from Django settings or raise ConfigurationError."""
        key = getattr(settings, "CLERK_SECRET_KEY", None)
        if not key:
            logger.error("CLERK_SECRET_KEY is not configured.")
            raise ConfigurationError(
                "ClerkSdk requires 'CLERK_SECRET_KEY' to be set in Django settings (CLERK_SECRET_KEY)."
            )
        return key

    @classmethod
    def get_auth_parties(cls) -> Any:
        """Return authorized parties configuration or raise ConfigurationError."""
        parties = getattr(settings, "CLERK_AUTH_PARTIES", None)
        if not parties:
            logger.error("CLERK_AUTH_PARTIES is not configured.")
            raise ConfigurationError(
                "ClerkSdk requires 'CLERK_AUTH_PARTIES' to be set in Django settings (CLERK_AUTH_PARTIES)."
            )
        return parties

    # ----- classproperty (option 3) accessors --------------------------------
    @classproperty
    def SECRET_KEY(cls) -> str:
        """Class-level property to access the secret key (classproperty)."""
        return cls.get_secret_key()

    @classproperty
    def AUTH_PARTIES(cls) -> Any:
        """Class-level property to access authorized parties (classproperty)."""
        return cls.get_auth_parties()

    # ----- optional class-level convenience client (creates a fresh client) ---
    @classproperty
    def sdk_client(cls) -> Clerk:
        """Convenience class-level client (creates a new Clerk client using SECRET_KEY).
        Prefer the instance-level `client` for runtime operations that benefit from re-use.
        """
        return Clerk(bearer_auth=cls.SECRET_KEY)  # type: ignore[arg-type]

    # ---------------------------
    # Singleton instance lifecycle
    # ---------------------------
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        # init only once
        if getattr(self, "_initialized", False):
            return
        self._initialized = True

        self._user_id: Optional[str] = None
        self._user: Optional[Any] = None
        self._client: Optional[Clerk] = None
        self._client_lock = threading.Lock()

    # ----- instance-level lazy client (preferred) ----------------------------
    @property
    def client(self) -> Clerk:
        """Lazily construct and return a Clerk client authenticated with the secret key.

        This is thread-safe and avoids creating the client at import-time.
        """
        if self._client is None:
            with self._client_lock:
                if self._client is None:
                    logger.debug("Initializing instance Clerk client.")
                    self._client = Clerk(bearer_auth=self.get_secret_key())  # type: ignore[arg-type]
        return self._client # type: ignore[return-type]

    @property
    def users(self):
        """Convenience accessor to the users endpoint on the client."""
        return self.client.users

    # ----- simple properties -------------------------------------------------
    @property
    def user_id(self) -> Optional[str]:
        return self._user_id

    @property
    def user(self) -> Optional[Any]:
        return self._user

    # ----- authentication helpers -------------------------------------------
    def authenticate_request(self, request: httpx.Request) -> str:
        """Authenticate incoming request with Clerk and set self._user_id on success.

        Raises AuthenticationFailed or ConfigurationError appropriately.
        """
        try:
            options = AuthenticateRequestOptions(authorized_parties=self.get_auth_parties())
            state = self.client.authenticate_request(request, options)
        except ConfigurationError:
            # bubble config errors
            raise
        except Exception as exc:
            logger.exception("Error authenticating request with Clerk.")
            raise AuthenticationFailed("Failed to authenticate request.") from exc

        if not getattr(state, "is_signed_in", False):
            logger.warning("Clerk authentication returned not signed-in state.")
            raise AuthenticationFailed("Authentication failed: user not signed in.")

        payload = getattr(state, "payload", {}) or {}
        sub = payload.get("sub")
        if not sub:
            logger.error("Clerk authentication succeeded but no 'sub' found in token payload.")
            raise AuthenticationFailed("Authentication failed: subject id missing in payload.")

        self._user_id = sub
        logger.debug("Authenticated Clerk subject id: %s", sub)
        return sub # type: ignore

    def get_user(self, request: httpx.Request):
        """Return Clerk user object for the authenticated request. Authenticates when necessary."""
        if not self.user_id:
            self.authenticate_request(request)

        try:
            user = self.users.get(user_id=self.user_id) # type: ignore[arg-type]
        except Exception as exc:
            logger.exception("Failed to fetch user from Clerk.")
            raise AuthenticationFailed("Failed to fetch user from Clerk.") from exc

        if not user:
            logger.error("Clerk returned no user for id %s", self.user_id)
            raise AuthenticationFailed("User does not exist in Clerk.")

        self._user = user
        return user

    def get_primary_email(self) -> EmailAddress:
        """Return primary EmailAddress object for the loaded Clerk user.

        Raises ValueError if user not loaded or no primary email found.
        """
        if self.user is None:
            raise ValueError("User must be loaded before calling get_primary_email().")

        primary_email_id = getattr(self.user, "primary_email_address_id", None)
        if not primary_email_id:
            raise ValueError("Authenticated Clerk user has no primary_email_address_id set.")

        email_addresses = getattr(self.user, "email_addresses", []) or []
        for email in email_addresses:
            if getattr(email, "id", None) == primary_email_id:
                return email

        raise ValueError("Primary email address not found among user's email_addresses.")

    # ----- Django user mapping and creation ---------------------------------
    @staticmethod
    def _model_has_field(model_cls: type, field_name: str) -> bool:
        """Return True if the Django model has a DB field with the given name."""
        try:
            return field_name in {f.name for f in model_cls._meta.get_fields()}
        except Exception:
            # If introspection fails, be conservative.
            return False

    def create_or_get_django_user(self, request: httpx.Request):
        """Create or fetch a Django user corresponding to the authenticated Clerk user.

        The function:
        - authenticates the request,
        - fetches the Clerk user,
        - chooses a lookup (clerk_user_id if present on your model, otherwise email),
        - creates the Django user with safe defaults (unusable password),
        - updates any commonly available fields.
        """
        clerk_user = self.get_user(request)

        clerk_id_field = "clerk_user_id"
        if self._model_has_field(User, clerk_id_field):
            lookup = {clerk_id_field: getattr(clerk_user, "id")}
        else:
            # fallback to primary email string if clerk_user_id not available
            try:
                primary_email_obj = self.get_primary_email()
                email_value = getattr(primary_email_obj, "email_address", None)
            except ValueError:
                email_value = getattr(clerk_user, "email", None) or None

            if not email_value:
                raise ClerkSdkError("Cannot determine lookup key for Django user (no clerk_user_id and no email).")
            lookup = {"email": email_value}

        # Build defaults by inspecting the user model
        defaults = {}
        if self._model_has_field(User, "username"):
            defaults["username"] = getattr(clerk_user, "username", None) or str(getattr(clerk_user, "id"))
        if self._model_has_field(User, "first_name"):
            defaults["first_name"] = getattr(clerk_user, "first_name", "") or ""
        if self._model_has_field(User, "last_name"):
            defaults["last_name"] = getattr(clerk_user, "last_name", "") or ""
        if self._model_has_field(User, "email") and "email" not in lookup:
            defaults["email"] = getattr(clerk_user, "email", None)
        if self._model_has_field(User, "image"):
            defaults["image"] = getattr(clerk_user, "profile_image_url", None)
        if self._model_has_field(User, "last_login"):
            defaults["last_login"] = getattr(clerk_user, "last_sign_in_at", None)
        if self._model_has_field(User, "last_active_at"):
            defaults["last_active_at"] = getattr(clerk_user, "last_active_at", None)

        user, created = User.objects.get_or_create(defaults=defaults, **lookup)

        if created:
            # Ensure no insecure default password is set
            try:
                user.set_unusable_password()
            except Exception:
                logger.debug("set_unusable_password not available on User model instance.")
            try:
                user.save()
            except Exception:
                logger.exception("Failed to save newly created Django user.")

        # Optional: sync fields if they differ
        updated = False
        mapping = {
            "username": getattr(clerk_user, "username", None),
            "first_name": getattr(clerk_user, "first_name", None),
            "last_name": getattr(clerk_user, "last_name", None),
            "image": getattr(clerk_user, "profile_image_url", None),
            "last_login": getattr(clerk_user, "last_sign_in_at", None),
            "last_active_at": getattr(clerk_user, "last_active_at", None),
        }
        for field_name, value in mapping.items():
            if value is None:
                continue
            if self._model_has_field(User, field_name) and getattr(user, field_name, None) != value:
                setattr(user, field_name, value)
                updated = True

        if updated:
            try:
                user.save()
            except Exception:
                logger.exception("Failed to save updated Django user fields after syncing with Clerk.")

        return user

    # ----- organizations ----------------------------------------------------
    def create_organization(self, request: httpx.Request, partner: Any) -> Any:
        """Create an organization in Clerk for the authenticated user."""
        if not self.user_id:
            self.authenticate_request(request)

        payload = CreateOrganizationRequestBody(
            name=getattr(partner, "display_name", "Organization"),
            created_by=self.user_id,
            created_at=timezone.now(),
            max_allowed_memberships=getattr(partner, "max_allowed_users", None),
        )

        try:
            org = self.client.organizations.create(request=payload)
        except Exception:
            logger.exception("Failed to create organization via Clerk.")
            raise ClerkSdkError("Failed to create organization via Clerk.")
        return org

    # ----- convenience ------------------------------------------------------
    def users(self) -> Any:
        """Return the underlying users client (convenience)."""
        return self.users_client


# Shared module-level singleton instance
sdk = ClerkSdk()

__all__ = ["sdk", "ClerkSdkError", "ConfigurationError"]
