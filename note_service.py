from sqlmodel import Session, select
from db.database import get_session
from db.models import Note

class NoteService:
    @staticmethod
    def create_note(title, content, user_id=1):
        with get_session() as session:
            note = Note(title=title, content=content, user_id=user_id)
            session.add(note)
            session.commit()
            session.refresh(note)
            return note

    @staticmethod
    def get_all_notes(user_id=1):
        with get_session() as session:
            return session.exec(select(Note).where(Note.user_id == user_id)).all()

    @staticmethod
    def update_note(note_id, title, content):
        with get_session() as session: # Fixed the // here
            note = session.get(Note, note_id)
            if note:
                note.title, note.content = title, content
                session.add(note)
                session.commit()

    @staticmethod
    def delete_note(note_id):
        with get_session() as session:
            note = session.get(Note, note_id)
            if note:
                session.delete(note)
                session.commit()
