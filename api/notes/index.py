"""
Serverless function for /api/notes (package index)

This file implements list and create for notes and lives inside the
api/notes package alongside [id].py to avoid module name collisions.
"""
import os
import json
from urllib.parse import urlencode

# Safe HTTP helper: prefer requests if installed, otherwise use urllib
try:
    import requests as _requests
    _HAS_REQUESTS = True
except Exception:
    _requests = None
    _HAS_REQUESTS = False

import urllib.request as _urllib_request

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

REST_HEADERS = {
    'apikey': SUPABASE_KEY or '',
    'Authorization': f'Bearer {SUPABASE_KEY}' if SUPABASE_KEY else '',
    'Content-Type': 'application/json'
}


def _http_request(method, url, headers=None, json_body=None, timeout=10):
    headers = headers or {}
    if _HAS_REQUESTS:
        # use requests for convenience
        func = _requests.request
        resp = func(method, url, headers=headers, json=json_body, timeout=timeout)
        return resp.status_code, resp.text

    # fallback to urllib
    data = None
    if json_body is not None:
        data = json.dumps(json_body).encode('utf-8')
    req = _urllib_request.Request(url, data=data, method=method)
    for k, v in headers.items():
        req.add_header(k, v)
    try:
        with _urllib_request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode('utf-8')
            return resp.getcode(), body
    except _urllib_request.HTTPError as e:
        try:
            body = e.read().decode('utf-8')
        except Exception:
            body = str(e)
        return e.code if hasattr(e, 'code') else 500, body
    except Exception as e:
        return 500, str(e)


def list_notes(req):
    # Validate configuration early to return a clear error
    if not SUPABASE_URL:
        return 500, {'error': 'SUPABASE_URL not configured'}
    if not SUPABASE_KEY:
        return 500, {'error': 'SUPABASE_SERVICE_ROLE_KEY not configured'}

    qs = {'select': '*', 'order': 'updated_at.desc'}
    url = f"{SUPABASE_URL}/rest/v1/notes?{urlencode(qs)}"
    status, text = _http_request('GET', url, headers=REST_HEADERS, timeout=10)
    if status != 200:
        return 500, {'error': text}
    try:
        return 200, json.loads(text)
    except Exception:
        return 500, {'error': 'invalid json from supabase', 'raw': text}


def create_note(req):
    # Validate configuration early
    if not SUPABASE_URL:
        return 500, {'error': 'SUPABASE_URL not configured'}
    if not SUPABASE_KEY:
        return 500, {'error': 'SUPABASE_SERVICE_ROLE_KEY not configured'}

    try:
        payload = req.get_json() if hasattr(req, 'get_json') else json.loads(req.body or '{}')
    except Exception:
        payload = {}

    note = {
        'title': payload.get('title') or 'Untitled',
        'content': payload.get('content') or '',
        'language': payload.get('language'),
        'tags': payload.get('tags'),
        'scheduled_at': payload.get('scheduled_at')
    }

    headers = REST_HEADERS.copy()
    headers['Prefer'] = 'return=representation'
    url = f"{SUPABASE_URL}/rest/v1/notes"
    status, text = _http_request('POST', url, headers=headers, json_body=note, timeout=10)
    if status not in (201, 200):
        return 500, {'error': text}
    try:
        data = json.loads(text)
    except Exception:
        return 500, {'error': 'invalid json from supabase', 'raw': text}
    return 201, data[0] if isinstance(data, list) and data else data


def handler(req, res):
    method = req.method.upper()
    if method == 'GET':
        status, body = list_notes(req)
        res.status_code = status
        res.headers['Content-Type'] = 'application/json'
        res.send(json.dumps(body))
        return

    if method == 'POST':
        status, body = create_note(req)
        res.status_code = status
        res.headers['Content-Type'] = 'application/json'
        res.send(json.dumps(body))
        return

    res.status_code = 405
    res.send(json.dumps({'error': 'Method not allowed'}))
