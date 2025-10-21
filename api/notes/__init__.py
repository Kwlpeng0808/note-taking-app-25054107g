"""api.notes package init.

Re-export the handler from index.py so that importing api.notes (module)
returns a package that has a `handler` attribute expected by Vercel.
"""
from .index import handler  # re-export

__all__ = ['handler']
