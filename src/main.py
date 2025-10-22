import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv
load_dotenv()

from flask import Flask, send_from_directory
from flask_cors import CORS
from src.models.user import db
from src.routes.user import user_bp
from src.routes.note import note_bp
from src.models.note import Note

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
# Load secret from environment (or fallback to previous hard-coded value)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'asdf#FGSgvasgf$5$WGT')

# Enable CORS for all routes
CORS(app)

# register blueprints
app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(note_bp, url_prefix='/api')
# configure database to use repository-root `database/app.db`, allow override from env
ROOT_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
DB_PATH = os.path.join(ROOT_DIR, 'database', 'app.db')
# ensure database directory exists
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

# Allow switching to Supabase/Postgres via SUPABASE_DATABASE_URL or SUPABASE_API_KEY
# Preferred order: SUPABASE_DATABASE_URL -> SQLALCHEMY_DATABASE_URI -> local sqlite fallback
supabase_db = os.getenv('SUPABASE_DATABASE_URL')
if supabase_db:
    app.config['SQLALCHEMY_DATABASE_URI'] = supabase_db
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI', f"sqlite:///{DB_PATH}")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# If using Supabase (pgbouncer/session pooling), keep SQLAlchemy pool very small and disable overflow.
# This avoids "MaxClientsInSessionMode: max clients reached" when the remote pooler limits clients.
if supabase_db:
    # Allow overriding via env vars if needed (defaults conservative)
    # default pool size for local/dev when connecting to Supabase; can override via env
    pool_size = int(os.getenv('DB_POOL_SIZE', '3'))
    max_overflow = int(os.getenv('DB_MAX_OVERFLOW', '0'))
    pool_timeout = int(os.getenv('DB_POOL_TIMEOUT', '30'))
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_size': pool_size,
        'max_overflow': max_overflow,
        'pool_timeout': pool_timeout,
        'pool_pre_ping': True,
    }
db.init_app(app)
with app.app_context():
    # When Flask debug reloader is on, the script runs twice (parent + child). Only run DB DDL once.
    # The reloader child process sets WERKZEUG_RUN_MAIN='true'. For non-debug runs, this will run once.
    if (not app.debug) or (os.environ.get('WERKZEUG_RUN_MAIN') == 'true'):
        db.create_all()
    # NOTE: Do NOT start the in-process background translation worker here on import.
    # Starting background threads during module import is unsafe in serverless environments
    # (like Vercel) because processes may be short-lived and multiple imports may happen.
    # To start the in-process worker for local development, set the env var
    # START_IN_PROCESS_WORKER=1 and run this module directly (python -m src.main or python src/main.py).

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
            return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404


if __name__ == '__main__':
    # Read runtime options from environment for easier local/dev overrides
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', '5001'))
    debug = os.getenv('DEBUG', 'False').lower() in ('1', 'true', 'yes') or os.getenv('FLASK_ENV') == 'development'
    app.run(host=host, port=port, debug=debug)
