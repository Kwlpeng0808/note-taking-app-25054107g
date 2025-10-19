from flask import Blueprint, jsonify, request
from src.models.note import Note, db
from datetime import datetime
from src import llm
from src.translation_worker import enqueue_translation

note_bp = Blueprint('note', __name__)

@note_bp.route('/notes', methods=['GET'])
def get_notes():
    """Get all notes, ordered by most recently updated"""
    notes = Note.query.order_by(Note.updated_at.desc()).all()
    return jsonify([note.to_dict() for note in notes])

@note_bp.route('/notes', methods=['POST'])
def create_note():
    """Create a new note"""
    try:
        data = request.json
        if not data or 'title' not in data or 'content' not in data:
            return jsonify({'error': 'Title and content are required'}), 400
        # parse optional fields
        language = data.get('language')
        translate_flag = bool(data.get('translate'))
        tags_raw = data.get('tags', '')
        scheduled_raw = data.get('scheduled_at')

        scheduled_at = None
        if scheduled_raw:
            try:
                scheduled_at = datetime.fromisoformat(scheduled_raw)
            except Exception:
                # ignore parse error; let model validation handle if needed
                scheduled_at = None

        tags = ','.join([t.strip() for t in tags_raw.split(',') if t.strip()]) if tags_raw else None

        note = Note(title=data['title'], content=data['content'], language=language, tags=tags, scheduled_at=scheduled_at)
        if translate_flag:
            # mark as pending and enqueue work for background worker
            note.translation_status = 'pending'
        
        db.session.add(note)
        db.session.commit()
        if translate_flag:
            try:
                enqueue_translation(note.id, note.title, note.content, language)
            except Exception as e:
                print('Failed to enqueue translation:', e)
        return jsonify(note.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@note_bp.route('/notes/<int:note_id>', methods=['GET'])
def get_note(note_id):
    """Get a specific note by ID"""
    note = Note.query.get_or_404(note_id)
    return jsonify(note.to_dict())

@note_bp.route('/notes/<int:note_id>', methods=['PUT'])
def update_note(note_id):
    """Update a specific note"""
    try:
        note = Note.query.get_or_404(note_id)
        data = request.json
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        # update basic fields
        note.title = data.get('title', note.title)
        note.content = data.get('content', note.content)
        # optional updates
        if 'language' in data:
            note.language = data.get('language')
        if 'tags' in data:
            tags_raw = data.get('tags', '')
            note.tags = ','.join([t.strip() for t in tags_raw.split(',') if t.strip()]) if tags_raw else None
        if 'scheduled_at' in data:
            try:
                note.scheduled_at = datetime.fromisoformat(data.get('scheduled_at')) if data.get('scheduled_at') else None
            except Exception:
                pass

        # translation on update if requested
        if data.get('translate'):
            try:
                trans = llm.translate_text(title=note.title, content=note.content, target_language=note.language)
                if trans:
                    note.translated_title = trans.get('title')
                    note.translated_content = trans.get('content')
            except Exception as e:
                print('Translation failed on update:', e)
        db.session.commit()
        return jsonify(note.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@note_bp.route('/notes/<int:note_id>', methods=['DELETE'])
def delete_note(note_id):
    """Delete a specific note"""
    try:
        note = Note.query.get_or_404(note_id)
        db.session.delete(note)
        db.session.commit()
        return '', 204
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@note_bp.route('/notes/search', methods=['GET'])
def search_notes():
    """Search notes by title or content"""
    query = request.args.get('q', '')
    if not query:
        return jsonify([])
    
    notes = Note.query.filter(
        (Note.title.contains(query)) | (Note.content.contains(query))
    ).order_by(Note.updated_at.desc()).all()
    
    return jsonify([note.to_dict() for note in notes])


@note_bp.route('/notes/generate', methods=['POST'])
def generate_note_route():
    """Generate a note from natural language input (does not persist)."""
    try:
        data = request.json
        if not data or 'prompt' not in data:
            return jsonify({'error': 'prompt is required'}), 400
        prompt = data['prompt']
        target_language = data.get('language', 'en')
        gen = llm.generate_note(prompt=prompt, target_language=target_language)
        if gen is None:
            return jsonify({'error': 'generation failed'}), 500
        return jsonify(gen)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@note_bp.route('/translate', methods=['POST'])
def translate_route():
    """Translate provided title/content/tags into the requested language and return translations without persisting."""
    try:
        data = request.json or {}
        title = data.get('title', '')
        content = data.get('content', '')
        tags = data.get('tags', [])
        target_language = data.get('language') or 'en'

        trans = llm.translate_text(title=title, content=content, target_language=target_language)
        trans_tags = None
        try:
            trans_tags = llm.translate_tags(tags, target_language)
        except Exception:
            trans_tags = None

        result = {
            'title': trans.get('title') if trans else None,
            'content': trans.get('content') if trans else None,
            'tags': trans_tags
        }
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

