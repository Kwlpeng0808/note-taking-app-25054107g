"""Deprecated top-level shim for /api/notes.

This file intentionally minimal. The canonical implementation lives in
`api/notes/index.py`. Keeping a small stub here reduces the risk of import-time
side-effects or conflicting exports.
"""

def handler(req, res):
    # return a simple JSON message; Vercel routing should prefer the package
    res.status_code = 501
    res.headers['Content-Type'] = 'application/json'
    res.send('{"error":"deprecated endpoint: use /api/notes"}')
