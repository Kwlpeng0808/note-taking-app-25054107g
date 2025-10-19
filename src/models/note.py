from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from src.models.user import db


class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    # optional original language code (e.g., 'en', 'zh')
    language = db.Column(db.String(16), nullable=True)
    # translated copies (if translation requested)
    translated_title = db.Column(db.String(200), nullable=True)
    translated_content = db.Column(db.Text, nullable=True)
    # tags stored as comma-separated string (saved/served as list)
    tags = db.Column(db.Text, nullable=True)
    # translation status: None | 'pending' | 'completed' | 'failed'
    translation_status = db.Column(db.String(32), nullable=True)
    # optional scheduled datetime for the note
    scheduled_at = db.Column(db.DateTime, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Note {self.title}>'

    def to_dict(self):
        tags_list = []
        if self.tags:
            # split by comma and strip whitespace, ignore empty
            tags_list = [t.strip() for t in self.tags.split(',') if t.strip()]

        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'language': self.language,
            'translated_title': self.translated_title,
            'translated_content': self.translated_content,
            'tags': tags_list,
            'scheduled_at': self.scheduled_at.isoformat() if self.scheduled_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

