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
db.init_app(app)
with app.app_context():
    db.create_all()
    # start background translation worker (in-process)
    try:
        from src.translation_worker import start_worker
        start_worker(app)
    except Exception as e:
        print('Failed to start translation worker:', e)

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
