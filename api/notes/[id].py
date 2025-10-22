"""
Vercel Serverless function for /api/notes/:id

Supports GET, PUT, DELETE using Supabase REST via HTTP requests.
"""
import os
import json

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

REST_HEADERS = {
    'apikey': SUPABASE_KEY or '',
    'Authorization': f'Bearer {SUPABASE_KEY}' if SUPABASE_KEY else '',
    'Content-Type': 'application/json'
}


def get_note(note_id):
    url = f"{SUPABASE_URL}/rest/v1/notes?id=eq.{note_id}&select=*"
    import requests
    r = requests.get(url, headers=REST_HEADERS, timeout=10)
    if r.status_code != 200:
        return r.status_code, {'error': r.text}
    data = r.json()
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
    import requests
    r = requests.patch(url, headers=headers, json=payload, timeout=10)
    if r.status_code not in (200, 204):
        return 500, {'error': r.text}
    data = r.json()
    return 200, data[0] if isinstance(data, list) and data else {}


def delete_note(note_id):
    url = f"{SUPABASE_URL}/rest/v1/notes?id=eq.{note_id}"
    import requests
    r = requests.delete(url, headers=REST_HEADERS, timeout=10)
    if r.status_code not in (200, 204):
        return 500, {'error': r.text}
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
