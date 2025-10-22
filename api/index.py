from dotenv import load_dotenv
load_dotenv()

# Import Flask app from the package
from src.main import app

# Optionally start in-process worker for long-running dev server
# Vercel serverless functions are short-lived; do NOT start background threads in production.
import os
if os.getenv('START_IN_PROCESS_WORKER', '').lower() in ('1', 'true', 'yes'):
    try:
        from src.translation_worker import start_worker
        start_worker(app)
    except Exception as e:
        print('Failed to start in-process worker:', e)

# Vercel Python runtime expects a variable named `app` to be the WSGI/ASGI callable.
# Flask provides a WSGI app, which is compatible with Vercel's Python adapter.

# Export `app` symbol (already in module namespace) for Vercel to pick up.

# If running locally with `vercel dev`, this file will be imported and `app` will be used.

# No further code required here.
