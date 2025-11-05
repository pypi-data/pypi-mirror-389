from datetime import datetime, timezone
import json
import os
import cv2
import numpy as np
from .BaseRepository import BaseRepository
from ..ai.FrameDrawer import FrameDrawer
from ..database.DatabaseManager import DatabaseManager
from ..models.worker_source_pipeline_detection import WorkerSourcePipelineDetectionEntity


class WorkerSourcePipelineDetectionRepository(BaseRepository):
    def __init__(self):
        super().__init__(db_name="default")
        self.storage_dir = DatabaseManager.STORAGE_PATHS["files"] / "detection_image"
        os.makedirs(self.storage_dir, exist_ok=True)

    def save_detection(self, pipeline_id: int, frame, tracked_objects, frame_drawer: FrameDrawer):
        """
        Save detection data that need to be sent to database.
        Only saves if there are violations detected.
        """
        now = datetime.now(timezone.utc)
        current_datetime = now.strftime("%Y%m%d_%H%M%S")

        frame_drawer.draw_polygons(frame)
        filtered_objects = []
        has_violations = False

        for tracked_obj in tracked_objects:
            attributes = tracked_obj["attributes"]

            if not any(attr.get("count", 0) == 5 for attr in attributes):
                continue

            obj = tracked_obj.copy()
            obj["attributes"] = [attr for attr in attributes if attr.get("count", 0) >= 5]

            # Check if any attribute is a violation
            for attr in obj["attributes"]:
                attr_label = attr.get("label", "")
                if attr_label in frame_drawer.violation_labels:
                    has_violations = True
                    break

            filtered_objects.append(obj)

        # Only save and trigger webhook/MQTT if there are actual violations
        if not filtered_objects or not has_violations:
            return

        drawn_frame = frame_drawer.draw_frame(frame.copy(), filtered_objects)

        full_image_filename = f"{pipeline_id}_{current_datetime}.jpg"
        full_image_path = os.path.join(self.storage_dir, full_image_filename)
        cv2.imwrite(full_image_path, drawn_frame)

        stringified_data = json.dumps(filtered_objects,
            default=lambda o: (
                float(o) if isinstance(o, np.floating) else
                int(o) if isinstance(o, np.integer) else
                list(o) if isinstance(o, (np.ndarray, tuple)) else
                str(o)
            )
        ) 

        try:
            with self._get_session() as session:
                new_detection = WorkerSourcePipelineDetectionEntity(
                    worker_source_pipeline_id=pipeline_id,
                    image_path=full_image_path,
                    data=stringified_data,
                    created_at=datetime.utcnow()
                )
                session.add(new_detection)
                session.flush()
        except Exception as e:
            print(f"❌ Database error while saving detection: {e}")
