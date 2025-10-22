"""Lightweight health/sanity endpoint to verify Vercel Python runtime.

This endpoint intentionally avoids heavy imports and top-level side-effects.
Deploying it helps determine whether Vercel's function runtime can load a
minimal handler successfully.
"""
import json


def handler(req, res):
    res.status_code = 200
    res.headers['Content-Type'] = 'application/json'
    res.send(json.dumps({'status': 'ok', 'service': 'ping'}))
