"""
Serverless function for /api/notes (package index)

This file implements list and create for notes and lives inside the
api/notes package alongside [id].py to avoid module name collisions.
"""
import os
import json
from urllib.parse import urlencode


SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

REST_HEADERS = {
    'apikey': SUPABASE_KEY or '',
    'Authorization': f'Bearer {SUPABASE_KEY}' if SUPABASE_KEY else '',
    'Content-Type': 'application/json'
}


def list_notes(req):
    qs = {'select': '*', 'order': 'updated_at.desc'}
    url = f"{SUPABASE_URL}/rest/v1/notes?{urlencode(qs)}"
    # import requests lazily to avoid import-time failures in environments
    # where requests may not be installed during a partial build step.
    import requests

    r = requests.get(url, headers=REST_HEADERS, timeout=10)
    if r.status_code != 200:
        return 500, {'error': r.text}
    return 200, r.json()


def create_note(req):
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
    import requests

    r = requests.post(url, headers=headers, json=note, timeout=10)
    if r.status_code not in (201, 200):
        return 500, {'error': r.text}
    data = r.json()
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
