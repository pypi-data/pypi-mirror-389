from datetime import datetime, timedelta, timezone
import json
import os
import cv2
import numpy as np
from .BaseRepository import BaseRepository
from ..database.DatabaseManager import DatabaseManager
from ..models.worker_source_pipeline_debug import WorkerSourcePipelineDebugEntity


class WorkerSourcePipelineDebugRepository(BaseRepository):
    def __init__(self):
        super().__init__(db_name="default")
        self.storage_dir = DatabaseManager.STORAGE_PATHS["files"] / "debug_image"
        os.makedirs(self.storage_dir, exist_ok=True)

    def get_pipeline_ids_to_debug(self):
        """
        Retrieve all distinct worker_source_pipeline_id values that need debugging.

        :return: A list of pipeline IDs (str) with null data.
        """
        with self._get_session() as session:
            now = datetime.now(timezone.utc)
            cutoff_time = now - timedelta(minutes=1)

            session.query(WorkerSourcePipelineDebugEntity)\
                .filter(
                    WorkerSourcePipelineDebugEntity.data == None,
                    WorkerSourcePipelineDebugEntity.created_at < cutoff_time
                ).delete(synchronize_session=False)

            session.commit()

            results = session.query(
                WorkerSourcePipelineDebugEntity.worker_source_pipeline_id
            ).filter(
                WorkerSourcePipelineDebugEntity.data == None
            ).distinct().all()

            return [row[0] for row in results]

    def update_debug_entries_by_pipeline_id(self, pipeline_id: int, image, data: str):
        """
        Update all debug entries for a given pipeline ID with new data.

        :param pipeline_id: The ID of the pipeline for which to update debug entries.
        :param new_data: The new data to update the entries with.
        :return: The number of updated entries.
        """
        with self._get_session() as session:
            now = datetime.now(timezone.utc)
            current_datetime = now.strftime("%Y%m%d_%H%M%S")

            stringified_data = json.dumps(
                {
                    "timestamp": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "tracked_objects": data,
                },
                default=lambda o: (
                    float(o) if isinstance(o, np.floating) else
                    int(o) if isinstance(o, np.integer) else
                    list(o) if isinstance(o, (np.ndarray, tuple)) else
                    str(o)
                )
            ) 
            
            full_image_filename = f"{pipeline_id}_{current_datetime}.jpg"
            full_image_path = os.path.join(self.storage_dir, full_image_filename)
            cv2.imwrite(full_image_path, image)

            updated_entries = session.query(WorkerSourcePipelineDebugEntity)\
                .filter_by(worker_source_pipeline_id=pipeline_id)\
                .update(
                    {
                        "image_path": full_image_path,
                        "data": stringified_data
                    },
                    synchronize_session="fetch"
                )
            # Commit happens automatically via context manager
            return updated_entries