"""
Serverless function for /api/generate

Accepts POST with JSON: { prompt: string, language?: string }
Returns JSON: { title: string, content: string, tags: [string], scheduled_at?: string }

Uses GitHub's hosted model via GITHUB_TOKEN and the GitHub inference endpoint.
Ensure GITHUB_TOKEN is set in Vercel env (we do not use OPENAI_API_KEY).
"""
import os
import json


def _get_openai_client():
    try:
        from openai import OpenAI
    except Exception:
        # openai may not be installed in some build steps; allow import-time
        # to succeed and fail at call-time with a clear message.
        return None, 'openai not installed'

    # Use GITHUB_TOKEN for GitHub-hosted model access
    key = os.getenv('GITHUB_TOKEN')
    if not key:
        return None, 'GITHUB_TOKEN not configured'

    # reuse endpoint defined in src/llm.py to keep a single source of truth
    try:
        from src.llm import endpoint as GH_ENDPOINT
    except Exception:
        # fallback to the known GitHub inference endpoint
        GH_ENDPOINT = 'https://models.github.ai/inference'

    client = OpenAI(base_url=GH_ENDPOINT, api_key=key)
    return client, None


def handler(req, res):
    if req.method.upper() != 'POST':
        res.status_code = 405
        res.send(json.dumps({'error': 'Method not allowed'}))
        return

    client, err = _get_openai_client()
    if err:
        res.status_code = 500
        res.send(json.dumps({'error': err}))
        return

    try:
        payload = req.get_json() if hasattr(req, 'get_json') else json.loads(req.body or '{}')
    except Exception:
        payload = {}

    prompt = payload.get('prompt', '')
    language = payload.get('language', 'en')

    if not prompt:
        res.status_code = 400
        res.send(json.dumps({'error': 'Missing prompt'}))
        return

    system_msg = (
        'You are a helpful assistant that generates short note drafts. Given a prompt, produce a JSON '
        'object with keys: title (short, <=50 chars), content (a few paragraphs), tags (array of strings), '
        'and optional scheduled_at (ISO date). Return ONLY the JSON object.'
    )

    user_msg = f'Language: {language}. Prompt: {prompt}'

    try:
        resp = client.ChatCompletion.create(
            model='gpt-3.5-turbo',
            messages=[
                {'role': 'system', 'content': system_msg},
                {'role': 'user', 'content': user_msg}
            ],
            temperature=0.7,
            max_tokens=800
        )

        text = resp.choices[0].message.content.strip()
        # Try parse JSON
        try:
            out = json.loads(text)
        except Exception:
            first = text.find('{')
            last = text.rfind('}')
            if first != -1 and last != -1:
                try:
                    out = json.loads(text[first:last+1])
                except Exception:
                    out = {'title': '', 'content': text, 'tags': []}
            else:
                out = {'title': '', 'content': text, 'tags': []}

        res.status_code = 200
        res.headers['Content-Type'] = 'application/json'
        res.send(json.dumps(out, ensure_ascii=False))
    except Exception as e:
        res.status_code = 500
        res.send(json.dumps({'error': str(e)}))
