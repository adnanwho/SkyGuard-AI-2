"""SkyGuard AI application package.

Keep package import lightweight so QC, schema, and evaluation utilities remain
usable when optional ML detector dependencies are not installed. The engine is
loaded lazily only when explicitly requested.
"""

__all__ = ["SkyGuardEngine", "SkyGuardResult"]


def __getattr__(name: str):
    if name in __all__:
        from .engine import SkyGuardEngine, SkyGuardResult
        return {"SkyGuardEngine": SkyGuardEngine, "SkyGuardResult": SkyGuardResult}[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
