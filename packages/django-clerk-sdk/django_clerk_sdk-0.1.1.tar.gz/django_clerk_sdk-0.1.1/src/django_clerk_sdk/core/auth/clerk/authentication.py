"""
Clerk-backed DRF authentication with request-scoped logging and metrics hooks.

Features:
- CachedClerkAuthentication: caches Django user PK keyed by the Bearer token.
- SimpleClerkAuthentication: bypasses cache and always revalidates with Clerk.
- Request-scoped logging: request id is picked up from headers or generated, and included
  in log records emitted during auth processing.
- Metrics hooks: emits counters for cache hits/misses/stale/store and auth success/failure.
  Configure your own collector by setting `CLERK_AUTH_METRICS_COLLECTOR` in Django settings.
"""

from __future__ import annotations

import logging
import uuid
from typing import Optional, Tuple, Any, Dict

from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.module_loading import import_string
from rest_framework import exceptions
from rest_framework.authentication import BaseAuthentication, get_authorization_header

from django_clerk_sdk.core.auth import clerk  # expects clerk.sdk to be available
from django_clerk_sdk.core.utils import cache as cache_utils

logger = logging.getLogger(__name__)
User = get_user_model()


# -------------------------
# Metrics collector support
# -------------------------
class MetricsCollectorProtocol:
    """Protocol-like duck type for metrics collectors."""

    def increment(self, name: str, amount: int = 1, tags: dict | None = None) -> None:
        raise NotImplementedError


class _NoopCollector(MetricsCollectorProtocol):
    def increment(self, name: str, amount: int = 1, tags: dict | None = None) -> None:
        # no-op
        return None


class _InMemoryCollector(MetricsCollectorProtocol):
    """Simple in-memory counter useful for local development or tests."""
    def __init__(self) -> None:
        self._counters: Dict[str, int] = {}

    def increment(self, name: str, amount: int = 1, tags: dict | None = None) -> None:
        self._counters[name] = self._counters.get(name, 0) + int(amount)

    def snapshot(self) -> Dict[str, int]:
        return dict(self._counters)


def _load_metrics_collector() -> MetricsCollectorProtocol:
    """
    Load a metrics collector specified in settings.CLERK_AUTH_METRICS_COLLECTOR.

    The setting may be:
      - an import path string to a class/instance that exposes .increment(name, amount, tags)
      - a callable that returns an object with .increment(...)
      - missing (in which case the in-memory collector is returned)
    """
    configured = getattr(settings, "CLERK_AUTH_METRICS_COLLECTOR", None)
    if not configured:
        # use a simple in-memory collector by default (safe)
        return _InMemoryCollector()

    # If it's a string import path, import it
    if isinstance(configured, str):
        try:
            thing = import_string(configured)
            # If the import produced a class, instantiate it
            if callable(thing):
                try:
                    inst = thing()
                except Exception:
                    # it's probably an instance already or factory failing — use as-is
                    inst = thing
            else:
                inst = thing
        except Exception:
            logger.exception("Failed to import CLERK_AUTH_METRICS_COLLECTOR '%s'; falling back to noop.", configured)
            return _NoopCollector()
    else:
        inst = configured

    # If inst itself is callable (factory), try to call it to obtain the collector
    try:
        if callable(inst) and not hasattr(inst, "increment"):
            inst = inst()
    except Exception:
        logger.exception("Failed to instantiate metrics collector; falling back to noop.")
        return _NoopCollector()

    # Validate presence of increment method
    if not hasattr(inst, "increment"):
        logger.error("Configured CLERK_AUTH_METRICS_COLLECTOR does not expose 'increment'; falling back to noop.")
        return _NoopCollector()

    return inst  # type: ignore[return-value]


_metrics = _load_metrics_collector()


def _metric(name: str, amount: int = 1, tags: dict | None = None) -> None:
    try:
        _metrics.increment(name=name, amount=amount, tags=tags)
    except Exception:
        # Metrics must not interfere with authentication; log and continue.
        logger.debug("Metrics increment failed for %s", name, exc_info=True)


# -------------------------
# Request-scoped logging
# -------------------------
def _get_request_id_from_request(req) -> str:
    """Extract a request id from common headers, else generate one."""
    # Support: X-Request-ID, X-RequestID, X-Correlation-ID (case-insensitive)
    header_candidates = ("HTTP_X_REQUEST_ID", "HTTP_X_REQUESTID", "HTTP_X_CORRELATION_ID")
    for hdr in header_candidates:
        val = req.META.get(hdr)
        if val:
            return str(val)
    # Also try the Authorization header if some callers place id there (unlikely)
    header = req.META.get("HTTP_X_REQUEST_ID") or req.META.get("X-Request-ID")
    if header:
        return str(header)
    # fallback to generating a UUID4 hex
    return uuid.uuid4().hex


class _RequestLoggerAdapter(logging.LoggerAdapter):
    """Attach request_id to all logging calls made through this adapter."""

    def process(self, msg, kwargs):
        extra = kwargs.setdefault("extra", {})
        extra.setdefault("request_id", self.extra.get("request_id"))
        return msg, kwargs


def _logger_for_request(req) -> logging.LoggerAdapter:
    """Return a LoggerAdapter which includes request_id in logs."""
    request_id = _get_request_id_from_request(req)
    return _RequestLoggerAdapter(logger, {"request_id": request_id})


# -------------------------
# Helper: canonical cache key
# -------------------------
def _cache_key_for_token(token: str) -> str:
    return f"clerk:token:{token}"


# -------------------------
# Authentication classes
# -------------------------
class CachedClerkAuthentication(BaseAuthentication):
    """
    Authenticates using Clerk and caches the Django user's PK by token.

    Metrics emitted:
      - clerk_auth_cache_hit
      - clerk_auth_cache_miss
      - clerk_auth_cache_stale
      - clerk_auth_cache_store_success
      - clerk_auth_cache_store_failure
      - clerk_auth_success
      - clerk_auth_failure
    """
    keyword = "Bearer"

    def authenticate(self, request):
        log = _logger_for_request(request)
        auth = get_authorization_header(request).split()

        if not auth:
            log.debug("No Authorization header present; skipping authentication.")
            return None

        if auth[0].lower() != self.keyword.lower().encode():
            log.debug("Authorization scheme is not Bearer; skipping.")
            return None

        if len(auth) == 1:
            log.warning("Invalid token header: no credentials provided.")
            raise exceptions.AuthenticationFailed("Invalid token header. No credentials provided.")
        if len(auth) > 2:
            log.warning("Invalid token header: token contains spaces.")
            raise exceptions.AuthenticationFailed("Invalid token header. Token string should not contain spaces.")

        try:
            token = auth[1].decode()
        except UnicodeError:
            log.warning("Invalid token header: invalid characters in token.")
            raise exceptions.AuthenticationFailed("Invalid token header. Token contains invalid characters.")

        log.debug("Attempting to authenticate token (redacted).")
        return self.authenticate_credentials(token, request)

    def authenticate_header(self, request) -> str:
        return self.keyword

    def authenticate_credentials(self, token: str, request) -> Optional[Tuple[Any, None]]:
        log = _logger_for_request(request)
        cache_key = _cache_key_for_token(token)

        # Try cache first — store only user.pk for portability
        cached_pk = cache_utils.retrieve(cache_key)
        if cached_pk is not None:
            try:
                user = User.objects.get(pk=cached_pk)
                log.info("Authenticated user from cache (pk=%s).", cached_pk)
                _metric("clerk_auth_cache_hit", tags={"source": "cache"})
                _metric("clerk_auth_success", tags={"source": "cache"})
                return user, None
            except User.DoesNotExist:
                # Stale cache; clear and continue
                log.info("Stale cache entry for key=%s; clearing and revalidating with Clerk.", cache_key)
                cache_utils.clear(cache_key)
                _metric("clerk_auth_cache_stale", tags={"cache_key": cache_key})
        else:
            _metric("clerk_auth_cache_miss", tags={"cache_key": cache_key})

        # Validate with Clerk (this may raise AuthenticationFailed)
        try:
            # Prefer to pass the DRF request object; if the ClerkSdk expects a httpx.Request
            # it should handle it. If it errors, attempt to re-run with a minimal httpx.Request.
            clerk.sdk.authenticate_request(request)
        except exceptions.AuthenticationFailed:
            log.warning("Clerk authentication failed for token (redacted).")
            _metric("clerk_auth_failure", tags={"reason": "clerk_failed"})
            raise
        except TypeError:
            # Clerk SDK may expect httpx.Request — try to construct a minimal one and retry.
            try:
                import httpx
                # Build a minimal httpx.Request with method and headers derived from Django request
                method = getattr(request, "method", "GET")
                url = getattr(request, "build_absolute_uri", lambda: "")()
                headers = {}
                # copy HTTP_ headers to normal header names
                for k, v in request.META.items():
                    if k.startswith("HTTP_"):
                        headers[k[5:].replace("_", "-")] = v
                # include Authorization explicitly
                auth_header = get_authorization_header(request)
                if auth_header:
                    try:
                        headers["Authorization"] = auth_header.decode()
                    except Exception:
                        headers["Authorization"] = auth_header
                httpx_req = httpx.Request(method=method, url=url, headers=headers)
                clerk.sdk.authenticate_request(httpx_req)
            except Exception as exc:
                log.exception("Clerk authentication failed (fallback path).")
                _metric("clerk_auth_failure", tags={"reason": "fallback_failed"})
                raise exceptions.AuthenticationFailed("Failed to authenticate request.") from exc
        except Exception as exc:
            log.exception("Unexpected error while calling Clerk authentication.")
            _metric("clerk_auth_failure", tags={"reason": "unexpected_error"})
            raise exceptions.AuthenticationFailed("Failed to authenticate request.") from exc

        # Clerk says the request is authenticated; now map/create Django user
        try:
            user = clerk.sdk.create_or_get_django_user(request)
        except Exception as exc:
            log.exception("Failed to map or create Django user for authenticated Clerk user.")
            _metric("clerk_auth_failure", tags={"reason": "user_mapping_failed"})
            raise exceptions.AuthenticationFailed("Failed to resolve user.") from exc

        # Cache the user's pk for subsequent requests; non-fatal if caching fails
        try:
            cache_utils.store(cache_key, user.pk)
            _metric("clerk_auth_cache_store_success", tags={"cache_key": cache_key})
            log.debug("Cached token -> user.pk mapping (pk=%s).", user.pk)
        except Exception:
            _metric("clerk_auth_cache_store_failure", tags={"cache_key": cache_key})
            log.exception("Failed to store token -> user.pk in cache; continuing without cache.")

        _metric("clerk_auth_success", tags={"source": "clerk"})
        log.info("Authenticated and resolved Django user (pk=%s).", getattr(user, "pk", None))
        return user, None


class SimpleClerkAuthentication(CachedClerkAuthentication):
    """Like CachedClerkAuthentication but bypasses the cache entirely (always revalidates)."""

    def authenticate_credentials(self, token: str, request) -> Optional[Tuple[Any, None]]:
        log = _logger_for_request(request)
        log.debug("Simple auth: bypassing cache and revalidating token.")

        try:
            clerk.sdk.authenticate_request(request)
        except exceptions.AuthenticationFailed:
            _metric("clerk_auth_failure", tags={"mode": "simple"})
            log.warning("Clerk authentication failed (simple).")
            raise
        except Exception:
            _metric("clerk_auth_failure", tags={"mode": "simple", "reason": "unexpected"})
            log.exception("Unexpected error during Clerk authentication (simple).")
            raise exceptions.AuthenticationFailed("Failed to authenticate request (simple).")

        try:
            user = clerk.sdk.create_or_get_django_user(request)
        except Exception:
            log.exception("Failed to create or resolve Django user (simple).")
            _metric("clerk_auth_failure", tags={"mode": "simple", "reason": "user_mapping_failed"})
            raise exceptions.AuthenticationFailed("Failed to resolve user (simple).")

        _metric("clerk_auth_success", tags={"mode": "simple"})
        log.info("Authenticated user (simple) pk=%s", getattr(user, "pk", None))
        return user, None
