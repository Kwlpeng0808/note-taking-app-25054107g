"""
Serverless function for /api/generate

Accepts POST with JSON: { prompt: string, language?: string }
Returns JSON: { title: string, content: string, tags: [string], scheduled_at?: string }

Uses OpenAI via OPENAI_API_KEY. Ensure OPENAI_API_KEY is set in Vercel env.
"""
import os
import json
import openai

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
openai.api_key = OPENAI_API_KEY


def handler(req, res):
    if req.method.upper() != 'POST':
        res.status_code = 405
        res.send(json.dumps({'error': 'Method not allowed'}))
        return

    if not OPENAI_API_KEY:
        res.status_code = 500
        res.send(json.dumps({'error': 'OpenAI API key not configured'}))
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
        resp = openai.ChatCompletion.create(
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
