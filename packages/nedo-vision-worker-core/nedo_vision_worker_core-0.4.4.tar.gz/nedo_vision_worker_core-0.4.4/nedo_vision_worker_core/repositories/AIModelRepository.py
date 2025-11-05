import logging
from sqlalchemy.exc import SQLAlchemyError
from .BaseRepository import BaseRepository
from ..models.ai_model import AIModelEntity

class AIModelRepository(BaseRepository):
    """Handles storage of AI Models into SQLite using SQLAlchemy."""

    def __init__(self):
        super().__init__(db_name="default")

    def get_models(self) -> list:
        """
        Retrieves all AI models from the database.

        Returns:
            list: A list of AIModelEntity objects.
        """
        try:
            with self._get_session() as session:
                session.expire_all()
                models = session.query(AIModelEntity).all()
                
                for model in models:
                    session.expunge(model)

                return models
        except SQLAlchemyError as e:
            logging.error(f"Error retrieving models: {e}")
            return []

    def get_model(self, model_id: str) -> AIModelEntity | None:
        """
        Retrieves a single AI model by its ID.

        Args:
            model_id: The ID of the model to retrieve.

        Returns:
            An AIModelEntity object or None if not found.
        """
        try:
            with self._get_session() as session:
                session.expire_all()
                model = session.query(AIModelEntity).filter_by(id=model_id).first()
                if model:
                    session.expunge(model)
                return model
        except SQLAlchemyError as e:
            logging.error(f"Error retrieving model {model_id}: {e}")
            return None