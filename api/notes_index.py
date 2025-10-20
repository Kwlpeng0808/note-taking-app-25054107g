"""
Vercel Serverless function for /api/notes (index)

Copied from api/notes.py but placed in a different filename to avoid import
conflicts when a package named `notes` exists (api/notes/ directory).

Environment variables required:
 - SUPABASE_URL
 - SUPABASE_SERVICE_ROLE_KEY

Supported methods:
 - GET: list notes
 - POST: create a note
"""
import os
import json
from urllib.parse import urlencode
import requests

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    # We won't raise here to avoid import-time crash in dev editors; handler will return 500.
    pass

REST_HEADERS = {
    'apikey': SUPABASE_KEY or '',
    'Authorization': f'Bearer {SUPABASE_KEY}' if SUPABASE_KEY else '',
    'Content-Type': 'application/json'
}


def list_notes(req):
    # Query params: optional limit/offset etc. We'll return newest first.
    qs = {'select': '*', 'order': 'updated_at.desc'}
    url = f"{SUPABASE_URL}/rest/v1/notes?{urlencode(qs)}"
    r = requests.get(url, headers=REST_HEADERS, timeout=10)
    if r.status_code != 200:
        return 500, {'error': r.text}
    return 200, r.json()


def create_note(req):
    try:
        payload = req.get_json() if hasattr(req, 'get_json') else json.loads(req.body or '{}')
    except Exception:
        payload = {}

    # Basic server-side defaults
    note = {
        'title': payload.get('title') or 'Untitled',
        'content': payload.get('content') or '',
        'language': payload.get('language'),
        'tags': payload.get('tags'),
        'scheduled_at': payload.get('scheduled_at')
    }

    # Use Prefer: return=representation to get the created row back
    headers = REST_HEADERS.copy()
    headers['Prefer'] = 'return=representation'
    url = f"{SUPABASE_URL}/rest/v1/notes"
    r = requests.post(url, headers=headers, json=note, timeout=10)
    if r.status_code not in (201, 200):
        return 500, {'error': r.text}
    # Supabase returns an array of created rows
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
