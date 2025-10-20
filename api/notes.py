"""Stub shim for /api/notes present only to avoid import/package name conflicts.

The real implementation lives in the package at api/notes/index.py. This file is
kept as a safe, tiny stub so that if it exists on disk it won't export any
non-class/module names that confuse the Vercel runtime (which previously raised
TypeError: issubclass() arg 1 must be a class when a package/file name collided).

Behavior: always returns 501 with a small JSON error directing traffic to the
package implementation.
"""
import json


def handler(req, res):
    res.status_code = 501
    res.headers['Content-Type'] = 'application/json'
    res.send(json.dumps({'error': 'Deprecated endpoint. Use /api/notes (package)'}))
