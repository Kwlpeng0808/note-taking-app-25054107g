"""api.notes package init.

Expose a handler while deferring importing of the heavy implementation
until the handler is actually invoked. This avoids import-time failures
when optional dependencies (like `requests`) are missing during a
deploy/build step.
"""

def handler(req, res):
	# Import the real handler on-demand to avoid import-time side effects.
	from . import index as _index
	return _index.handler(req, res)


__all__ = ['handler']
