"""Fail-closed identity for exact code, interpreter and strategy settings."""
import hashlib
import inspect
import json
import sys
from pathlib import Path


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), allow_nan=False)


def runtime_fingerprint():
    sources = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
               for p in sorted(Path(__file__).parent.glob("*.py"))}
    sources["python"] = sys.version
    return hashlib.sha256(canonical(sources).encode()).hexdigest()


def strategy_fingerprint(strategy):
    from .strategies import PARAMETERS
    identity = {"class": type(strategy).__module__ + "." + type(strategy).__qualname__,
                "source": inspect.getsource(type(strategy)),
                "settings": vars(strategy), "parameters": PARAMETERS.get(strategy.name)}
    return hashlib.sha256(canonical(identity).encode()).hexdigest()
