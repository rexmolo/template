from urllib.parse import urlparse

from starlette.datastructures import Headers, MutableHeaders
from starlette.responses import Response
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.config import Settings

PUBLIC_API_PREFIX = "/api/v1/public"
PUBLIC_CORS_METHODS = ("GET", "POST", "OPTIONS")
PUBLIC_CORS_HEADERS = ("Content-Type", "X-Captcha-Token", "Idempotency-Key")
SAFE_METHODS = {"GET", "HEAD", "OPTIONS", "TRACE"}

SECURITY_HEADERS = {
    "Content-Security-Policy": "default-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
    "Referrer-Policy": "no-referrer",
    "Strict-Transport-Security": "max-age=63072000; includeSubDomains; preload",
    "X-Frame-Options": "DENY",
}


class SecurityHeadersMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_with_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                for name, value in SECURITY_HEADERS.items():
                    if name not in headers:
                        headers[name] = value
            await send(message)

        await self.app(scope, receive, send_with_headers)


class PublicCORSMiddleware:
    def __init__(self, app: ASGIApp, settings: Settings) -> None:
        self.app = app
        self.public_site_origin = settings.public_site_origin

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or not scope["path"].startswith(PUBLIC_API_PREFIX):
            await self.app(scope, receive, send)
            return

        headers = Headers(scope=scope)
        origin = headers.get("origin")
        if not origin:
            await self.app(scope, receive, send)
            return

        if origin != self.public_site_origin:
            await Response(status_code=400)(scope, receive, send)
            return

        if scope["method"] == "OPTIONS":
            requested_method = headers.get("access-control-request-method")
            requested_headers = _split_header_values(headers.get("access-control-request-headers"))
            if requested_method not in PUBLIC_CORS_METHODS or not _headers_allowed(requested_headers):
                await Response(status_code=400)(scope, receive, send)
                return

            await Response(status_code=200, headers=self._cors_headers(origin))(scope, receive, send)
            return

        async def send_with_cors(message: Message) -> None:
            if message["type"] == "http.response.start":
                response_headers = MutableHeaders(scope=message)
                for name, value in self._cors_headers(origin).items():
                    response_headers[name] = value
            await send(message)

        await self.app(scope, receive, send_with_cors)

    def _cors_headers(self, origin: str) -> dict[str, str]:
        return {
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Methods": ", ".join(PUBLIC_CORS_METHODS),
            "Access-Control-Allow-Headers": ", ".join(PUBLIC_CORS_HEADERS),
            "Vary": "Origin",
        }


class CookieOriginGuardMiddleware:
    def __init__(self, app: ASGIApp, settings: Settings) -> None:
        self.app = app
        self.app_origin = settings.app_origin

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = Headers(scope=scope)
        if not self._requires_origin_check(scope, headers):
            await self.app(scope, receive, send)
            return

        if not self._allowed_origin(headers):
            await Response("Forbidden", status_code=403)(scope, receive, send)
            return

        await self.app(scope, receive, send)

    def _requires_origin_check(self, scope: Scope, headers: Headers) -> bool:
        return (
            scope["method"] not in SAFE_METHODS
            and not scope["path"].startswith(PUBLIC_API_PREFIX)
            and headers.get("cookie") is not None
        )

    def _allowed_origin(self, headers: Headers) -> bool:
        origin = headers.get("origin")
        if origin:
            return origin == self.app_origin

        referer = headers.get("referer")
        if not referer:
            return False

        parsed = urlparse(referer)
        referer_origin = f"{parsed.scheme}://{parsed.netloc}"
        return referer_origin == self.app_origin


def _split_header_values(value: str | None) -> set[str]:
    if not value:
        return set()
    return {item.strip().lower() for item in value.split(",") if item.strip()}


def _headers_allowed(headers: set[str]) -> bool:
    allowed = {header.lower() for header in PUBLIC_CORS_HEADERS}
    return headers.issubset(allowed)
