"""
Vercel Serverless function for /api/notes/:id

Supports GET, PUT, DELETE using Supabase REST via HTTP requests.
"""
import os
import json
import urllib.request as _urllib_request
try:
    import requests as _requests
    _HAS_REQUESTS = True
except Exception:
    _requests = None
    _HAS_REQUESTS = False


def _http_request(method, url, headers=None, json_body=None, timeout=10):
    headers = headers or {}
    if _HAS_REQUESTS:
        resp = _requests.request(method, url, headers=headers, json=json_body, timeout=timeout)
        return resp.status_code, resp.text

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

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

REST_HEADERS = {
    'apikey': SUPABASE_KEY or '',
    'Authorization': f'Bearer {SUPABASE_KEY}' if SUPABASE_KEY else '',
    'Content-Type': 'application/json'
}


def get_note(note_id):
    if not SUPABASE_URL:
        return 500, {'error': 'SUPABASE_URL not configured'}
    if not SUPABASE_KEY:
        return 500, {'error': 'SUPABASE_SERVICE_ROLE_KEY not configured'}

    url = f"{SUPABASE_URL}/rest/v1/notes?id=eq.{note_id}&select=*"
    status, text = _http_request('GET', url, headers=REST_HEADERS, timeout=10)
    if status != 200:
        return status, {'error': text}
    try:
        data = json.loads(text)
    except Exception:
        return 500, {'error': 'invalid json from supabase', 'raw': text}
    if not data:
        return 404, {'error': 'Note not found'}
    return 200, data[0]


def update_note(note_id, req):
    try:
        payload = req.get_json() if hasattr(req, 'get_json') else json.loads(req.body or '{}')
    except Exception:
        payload = {}

    headers = REST_HEADERS.copy()
    headers['Prefer'] = 'return=representation'
    url = f"{SUPABASE_URL}/rest/v1/notes?id=eq.{note_id}"
    status, text = _http_request('PATCH', url, headers=headers, json_body=payload, timeout=10)
    if status not in (200, 204):
        return 500, {'error': text}
    try:
        data = json.loads(text)
    except Exception:
        return 500, {'error': 'invalid json from supabase', 'raw': text}
    return 200, data[0] if isinstance(data, list) and data else {}


def delete_note(note_id):
    if not SUPABASE_URL:
        return 500, {'error': 'SUPABASE_URL not configured'}
    if not SUPABASE_KEY:
        return 500, {'error': 'SUPABASE_SERVICE_ROLE_KEY not configured'}

    url = f"{SUPABASE_URL}/rest/v1/notes?id=eq.{note_id}"
    status, text = _http_request('DELETE', url, headers=REST_HEADERS, timeout=10)
    if status not in (200, 204):
        return 500, {'error': text}
    return 200, {'deleted': True}


def handler(req, res):
    # Vercel passes pathname info in req.path; we extract id
    # For robust extraction, split the path
    path = getattr(req, 'path', '') or ''
    parts = [p for p in path.split('/') if p]
    # expect path like /api/notes/<id>
    note_id = parts[-1] if parts else None
    if not note_id:
        res.status_code = 400
        res.send(json.dumps({'error': 'Missing note id'}))
        return

    method = req.method.upper()
    if method == 'GET':
        status, body = get_note(note_id)
        res.status_code = status
        res.headers['Content-Type'] = 'application/json'
        res.send(json.dumps(body))
        return

    if method in ('PUT', 'PATCH'):
        status, body = update_note(note_id, req)
        res.status_code = status
        res.headers['Content-Type'] = 'application/json'
        res.send(json.dumps(body))
        return

    if method == 'DELETE':
        status, body = delete_note(note_id)
        res.status_code = status
        res.headers['Content-Type'] = 'application/json'
        res.send(json.dumps(body))
        return

    res.status_code = 405
    res.send(json.dumps({'error': 'Method not allowed'}))
