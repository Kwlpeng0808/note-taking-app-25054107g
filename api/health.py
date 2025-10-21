"""Debug health endpoint used temporarily to surface import-time errors on Vercel.

This endpoint should be removed once we've diagnosed the deployment issue.
It attempts to import key modules used by the serverless functions and returns
OK or the exception traceback (without printing env var values).
"""
import traceback
import json


def handler(req, res):
    try:
        # Try importing the modules that typically fail on deploy
        import importlib

        modules = [
            'api.notes',
            'api.notes.index',
            'api.translate',
            'api.generate',
            'openai',
            'requests'
        ]

        results = {}
        for m in modules:
            try:
                importlib.import_module(m)
                results[m] = 'import OK'
            except Exception as e:
                results[m] = f'IMPORT_ERROR: {type(e).__name__}: {e}'

        res.status_code = 200
        res.headers['Content-Type'] = 'application/json'
        res.send(json.dumps({'status': 'ok', 'modules': results}, ensure_ascii=False))
    except Exception as exc:
        tb = traceback.format_exc()
        res.status_code = 500
        res.headers['Content-Type'] = 'application/json'
        # Only return the first 10 lines of traceback to avoid huge responses
        short_tb = '\n'.join(tb.splitlines()[:10])
        res.send(json.dumps({'status': 'error', 'trace': short_tb}, ensure_ascii=False))
