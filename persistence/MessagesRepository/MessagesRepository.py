from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from db.session import SessionLocal
from db.models import Message
from errors import PersistenceError




class MessagesRepository:
    def __init__(self, db_connection=None, project_id: int | None = None):
        self.db_connection = db_connection
        self.project_id = project_id

    def list_by_project(self) -> list[dict]:
        session = self.db_connection or SessionLocal()
        try:
            stmt = (
                select(Message)
                .where(Message.project_id == self.project_id)
                .order_by(Message.sequence_no)
            )

            rows = session.execute(stmt).scalars().all()

            return [
                {
                    "id": r.id,
                    "project_id": r.project_id,
                    "sequence_no": r.sequence_no,
                    "role": r.role,
                    "content": r.content,
                    "thinking": r.thinking,
                    "tool_name": r.tool_name,
                    "tool_calls_json": r.tool_calls_json,
                    "images_json": r.images_json,
                    "created_at": r.created_at,
                }
                for r in rows
            ]

        except SQLAlchemyError as e:
            raise PersistenceError(str(e))
        finally:
            if self.db_connection is None:
                session.close()

    def insert_message(self, message_data: dict) -> dict:
        session = self.db_connection or SessionLocal()
        try:
            message = Message(**message_data)
            session.add(message)
            session.commit()
            session.refresh(message)

            return {
                "id": message.id,
                "project_id": message.project_id,
                "sequence_no": message.sequence_no,
                "role": message.role,
                "content": message.content,
                "thinking": message.thinking,
            }

        except SQLAlchemyError as e:
            session.rollback()
            raise PersistenceError(str(e))
        finally:
            if self.db_connection is None:
                session.close()