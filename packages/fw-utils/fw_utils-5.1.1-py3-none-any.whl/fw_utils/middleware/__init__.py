"""Reuable starlette middleware classes."""

__all__ = ["CacheControlMiddleware"]


try:
    from .cache_control import CacheControlMiddleware
except ImportError as ie:  # pragma: no cover
    print("Starlette not installed, cannot use middleware classes")
    raise ie
