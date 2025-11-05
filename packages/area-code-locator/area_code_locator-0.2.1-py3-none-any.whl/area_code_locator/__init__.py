from threading import Lock
# CHANGE THIS to your actual module name:
from .area_code_locator import AreaCodeLocator   # e.g. .locator or .area_code_locator

__all__ = ["lookup", "batch_lookup", "AreaCodeLocator"]

_loc = None
_lock = Lock()

def _get():
    global _loc
    if _loc is None:
        with _lock:
            if _loc is None:
                _loc = AreaCodeLocator()
    return _loc

def lookup(lat: float, lon: float, return_all: bool = True):
    return _get().lookup(lat=lat, lon=lon, return_all=return_all)

def batch_lookup(points, return_all: bool = True):
    L = _get()
    return [L.lookup(lat, lon, return_all=return_all) for lat, lon in points]
