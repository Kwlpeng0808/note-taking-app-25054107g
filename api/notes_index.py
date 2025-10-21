"""Deprecated shim for /api/notes (index).

Minimal safe file to avoid potential import-time conflicts. Real code is
in api/notes/index.py.
"""

def handler(req, res):
    res.status_code = 501
    res.headers['Content-Type'] = 'application/json'
    res.send('{"error":"deprecated endpoint: use /api/notes"}')
