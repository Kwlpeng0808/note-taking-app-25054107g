import threading
import queue
import time
import traceback
from typing import Optional

from src.models.note import Note, db
from src import llm

_task_queue = queue.Queue()
_worker_thread = None


def enqueue_translation(note_id: int, title: str, content: str, target_language: Optional[str]):
    _task_queue.put((note_id, title, content, target_language))


def _worker_loop(app):
    with app.app_context():
        while True:
            try:
                note_id, title, content, target_language = _task_queue.get()
                note = Note.query.get(note_id)
                if not note:
                    continue
                try:
                    note.translation_status = 'in_progress'
                    db.session.commit()

                    result = llm.translate_text(title=title, content=content, target_language=target_language)
                    if result:
                        note.translated_title = result.get('title')
                        note.translated_content = result.get('content')
                        note.translation_status = 'completed'
                    else:
                        note.translation_status = 'failed'
                    db.session.commit()
                except Exception:
                    traceback.print_exc()
                    db.session.rollback()
                    if note:
                        note.translation_status = 'failed'
                        db.session.commit()
                finally:
                    _task_queue.task_done()
            except Exception:
                traceback.print_exc()
                time.sleep(1)


def start_worker(app):
    global _worker_thread
    if _worker_thread and _worker_thread.is_alive():
        return
    _worker_thread = threading.Thread(target=_worker_loop, args=(app,), daemon=True)
    _worker_thread.start()
