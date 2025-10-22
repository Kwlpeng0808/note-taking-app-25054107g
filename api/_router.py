"""Central request router for /api/* endpoints.

This file is intentionally minimal at import time (no heavy imports).
It dynamically imports the target API module at request time and forwards
the request to its `handler(req, res)`. Any import-time or runtime
exceptions are caught and returned as JSON so Vercel's wrapper doesn't
see a broken module and produce the `issubclass()` TypeError.
"""
import importlib
import importlib.util
import json
import os
import traceback


def _call_module_handler(module, req, res):
    # call the module's handler if present
    handler = getattr(module, 'handler', None)
    if not callable(handler):
        res.status_code = 500
        res.headers['Content-Type'] = 'application/json'
        res.send(json.dumps({'error': 'module has no callable handler'}))
        return
    try:
        return handler(req, res)
    except Exception:
        tb = traceback.format_exc()
        res.status_code = 500
        res.headers['Content-Type'] = 'application/json'
        # return a short traceback to avoid huge responses
        res.send(json.dumps({'error': 'handler exception', 'trace': tb.splitlines()[-20:]}, ensure_ascii=False))


def _import_notes_id_module():
    # load api/notes/[id].py by filepath
    base = os.path.dirname(__file__)
    path = os.path.join(base, 'notes', '[id].py')
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    spec = importlib.util.spec_from_file_location('api.notes._id', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _import_module_for_path(path):
    # path is e.g. '/api/generate' or '/api/notes/123'
    parts = [p for p in path.split('/') if p]
    if not parts:
        raise ImportError('empty path')
    # parts[0] == 'api'
    if len(parts) == 1:
        raise ImportError('no endpoint specified')
    endpoint = parts[1]
    # special-case notes/<id>
    if endpoint == 'notes' and len(parts) >= 3:
        return _import_notes_id_module()
    # otherwise import api.<endpoint>
    module_name = f'api.{endpoint}'
    return importlib.import_module(module_name)


def handler(req, res):
    # Determine request path; fall back to req.path or req.url
    path = getattr(req, 'path', None) or getattr(req, 'url', None) or ''
    try:
        module = _import_module_for_path(path)
    except Exception:
        tb = traceback.format_exc()
        res.status_code = 500
        res.headers['Content-Type'] = 'application/json'
        res.send(json.dumps({'error': 'import error', 'trace': tb.splitlines()[-20:]}, ensure_ascii=False))
        return

    return _call_module_handler(module, req, res)
