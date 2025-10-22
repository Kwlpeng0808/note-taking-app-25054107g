"""
Serverless function for /api/translate

Accepts POST with JSON:
    { title: string, content: string, tags: [string], language: 'en'|'zh'|... }

Returns JSON:
    { title: string, content: string, tags: [string] }

Uses GitHub-hosted model via GITHUB_TOKEN and the GitHub inference endpoint.
Ensure GITHUB_TOKEN is set in Vercel env (we do not use OPENAI_API_KEY).
"""
import os
import json


def _get_openai_client():
    try:
        from openai import OpenAI
    except Exception:
        return None, 'openai not installed'
    key = os.getenv('GITHUB_TOKEN')
    if not key:
        return None, 'GITHUB_TOKEN not configured'
    try:
        from src.llm import endpoint as GH_ENDPOINT
    except Exception:
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

    title = payload.get('title', '')
    content = payload.get('content', '')
    tags = payload.get('tags', []) or []
    language = payload.get('language', 'en')

    system_msg = (
        'You are a professional translator. Given a title, content, and tags, translate them into '
        f'the target language ({language}). Preserve meaning and tone. Return ONLY a JSON object with '
        'keys: title, content, tags (array). Do not output any explanatory text.'
    )

    user_msg = json.dumps({'title': title, 'content': content, 'tags': tags}, ensure_ascii=False)

    try:
        resp = client.ChatCompletion.create(
            model='gpt-3.5-turbo',
            messages=[
                {'role': 'system', 'content': system_msg},
                {'role': 'user', 'content': 'Translate the following JSON payload to ' + language + ': ' + user_msg}
            ],
            temperature=0.2,
            max_tokens=1200
        )

        text = resp.choices[0].message.content.strip()
        # Try to parse JSON from the model output
        try:
            out = json.loads(text)
        except Exception:
            # Attempt to extract JSON substring
            first = text.find('{')
            last = text.rfind('}')
            if first != -1 and last != -1:
                try:
                    out = json.loads(text[first:last+1])
                except Exception:
                    out = {'title': '', 'content': '', 'tags': []}
            else:
                out = {'title': '', 'content': '', 'tags': []}

        res.status_code = 200
        res.headers['Content-Type'] = 'application/json'
        res.send(json.dumps(out, ensure_ascii=False))
    except Exception as e:
        res.status_code = 500
        res.send(json.dumps({'error': str(e)}))
