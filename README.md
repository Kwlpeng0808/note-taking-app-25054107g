# NoteTaker - Personal Note Management Application

A personal note management app built with a lightweight backend and a modern, responsive frontend. Supports search, tags, optional AI generation and translation helpers.

## 🌟 Features

- **Create Notes**: Add new notes with title, content, tags and scheduled time
- **Edit Notes**: Update existing notes with real-time editing
- **Delete Notes**: Remove notes you no longer need
- **Search Notes**: Find notes quickly by searching titles and content
- **AI Notes generation**: Optional AI generation and translation (requires token)
- **Notes Translation**: Support translation into five common languages

## 🚀 Live Demo

The application is deployed and accessible at: **https://note-taking-app-25054107g.vercel.app/**

## 🛠 Technology Stack
- Backend: Flask, SQLAlchemy
- Frontend: static HTML/JS (src/static/index.html)
- Database: Supabase

## 📁 Project Structure

```
notetaking-app/
├── src/
│   ├── models/
│   │   ├── user.py            # User model (template)
│   │   └── note.py            # Note model with database schema
│   ├── routes/
│   │   ├── user.py            # User API routes (template)
│   │   └── note.py            # Note API endpoints
│   ├── static/
│   │   ├── index.html         # Frontend application
│   │   └── favicon.ico        # Application icon
│   └── llm.py                 # Optional LLM integration
│   └── main.py                # Flask application entry point
│   └── translation_worker.py  # Optional translation worker
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## 🔧 Local Development Setup

### Prerequisites
- Python 3.11+
- pip (Python package manager)

### Installation Steps

1. **Clone or download the project**
   ```bash
   python -m venv venv
   ```

2. **Activate the virtual environment**
   ```bash
   source venv/bin/activate
   ```

   Remark: On Windows, use `venv\Scripts\activate`

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   python src/main.py
   ```

5. **Access the application**
   - Open your browser and go to `http://localhost:5001`

## 📡 API Endpoints

### Notes API
- `GET /api/notes` - Get all notes
- `POST /api/notes` - Create a new note
- `GET /api/notes/<id>` - Get a specific note
- `PUT /api/notes/<id>` - Update a note
- `DELETE /api/notes/<id>` - Delete a note
- `POST /api/notes/generate` - AI Notes generate
- `POST /api/translate` - Notes translation

### Request/Response Format
```json
{
  "id": 1,
  "title": "My Note Title",
  "content": "Note content here...",
  "created_at": "2025-09-03T11:26:38.123456",
  "updated_at": "2025-09-03T11:27:30.654321"
}
```

## 🚀 Deployment
- Vercel entry: api/index.py (exports `app`)
- Provide required environment variables in your deployment environment
- For background translation tasks, use an external worker or a proper background job system; serverless functions are short-lived

Vercel deploy example:
```powershell
vercel --prod
```

## 📄 Configuration & Environment Variables
- `FLASK_ENV` — set to development for debug
- `SECRET_KEY` — Flask secret for sessions
- `GITHUB_TOKEN` — required for LLM features
- `SUPABASE_DATABASE_UR`L` — optional, when using hosted Postgres

DB pool tuning env vars (for hosted Postgres):
- `DB_POOL_SIZE` - number of persistent connections the app will keep per process (QueuePool `pool_size`).
- `DB_MAX_OVERFLOW` - additional temporary connections allowed above `DB_POOL_SIZE` when demand spikes (QueuePool `max_overflow`).
- `DB_POOL_TIMEOUT` - number of seconds to wait for a connection from the pool before erroring (QueuePool `pool_timeout`).

If SUPABASE_DATABASE_URL is not set, app falls back to local SQLite.

## 🔒 Database Schema and Notes Table
```sql
CREATE TABLE note (
  id INTEGER PRIMARY KEY,
  title VARCHAR(200) NOT NULL,
  content TEXT NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

## 🤝 Contributing
1. Fork
2. Create a branch
3. Implement features and tests
4. Open a pull request

## 📄 License

This project is open source and available under the MIT License.