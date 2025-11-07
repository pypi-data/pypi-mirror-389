"""Cache Control Middleware."""

import re
import typing as t

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

RequestResponseEndpoint = t.Callable[[Request], t.Awaitable[Response]]
PathList = t.List[t.Union[str, re.Pattern]]


class CacheControlMiddleware(BaseHTTPMiddleware):
    """CacheControlMiddleware.

    Starlette middleware class that adds cache control headers
    to responses
    """

    def __init__(
        self,
        app: ASGIApp,
        cachable_paths: t.Optional[PathList] = None,
        no_cache_paths: t.Optional[PathList] = None,
    ):
        """Contructor.

        Keyword Arguments:
        app: ASGIApp
        cachable_paths: List of string prefixes or regex patterns of paths that
            should not have cache control headers applied
        no_cache_paths: If specified, an _exclusive_ list of string prefixes or
            regex patterns of paths to apply cache control headers to. If a
            path does not match a list item, cache control headers *will not*
            be applied. This takes precedense over `cachable_paths`; i.e. using
            this setting will override any behavior specified by `cachable_paths`
        """
        super().__init__(app)
        self.cachable_paths = cachable_paths
        self.no_cache_paths = no_cache_paths

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """Main method."""
        response = await call_next(request)

        path = request.url.path
        add_headers = False
        if self.no_cache_paths:
            add_headers = self._any_path_match(path, self.no_cache_paths)
        else:
            add_headers = not (
                self.cachable_paths and self._any_path_match(path, self.cachable_paths)
            )

        if add_headers:
            response.headers["Cache-Control"] = "no-store; no-cache; must-revalidate;"
            response.headers["Pragma"] = "no-cache"
        return response

    def _any_path_match(self, path: str, match_list: PathList) -> bool:
        return any(self._path_match(path, match) for match in match_list)

    def _path_match(self, path: str, match: t.Union[str, re.Pattern]) -> bool:
        if isinstance(match, str):
            return path.startswith(match)
        else:
            return match.match(path) is not None
