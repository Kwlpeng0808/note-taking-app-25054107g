"""Small shim to avoid module/package import collisions on Vercel.

The canonical implementation for the notes collection lives under api/notes/
package (index.py). This file exists only as a safe stub so that if Vercel
encounters this top-level module it won't export unexpected objects that could
cause isinstance/issubclass checks to fail at runtime.
"""
import json


def handler(req, res):
    res.status_code = 501
    res.headers['Content-Type'] = 'application/json'
    res.send(json.dumps({'error': 'Deprecated endpoint. Use /api/notes (package)'}))
