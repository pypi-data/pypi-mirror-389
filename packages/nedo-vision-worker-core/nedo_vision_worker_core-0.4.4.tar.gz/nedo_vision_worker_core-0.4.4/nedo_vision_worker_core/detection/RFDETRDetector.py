import cv2
import logging
try:
    from rfdetr import RFDETRNano, RFDETRSmall, RFDETRMedium, RFDETRBase, RFDETRLarge
    RFDETR_AVAILABLE = True
except ImportError:
    RFDETR_AVAILABLE = False
    RFDETRNano = RFDETRSmall = RFDETRMedium = RFDETRBase = RFDETRLarge = None

from ..database.DatabaseManager import DatabaseManager
from ..models.ai_model import AIModelEntity
from ..util.PlatformDetector import PlatformDetector
from .BaseDetector import BaseDetector

logging.getLogger("ultralytics").setLevel(logging.WARNING)

class RFDETRDetector(BaseDetector):
    def __init__(self, model: AIModelEntity):
        if not RFDETR_AVAILABLE:
            raise ImportError(
                "RF-DETR is required but not installed. Install it manually with:\n"
                "pip install rfdetr @ git+https://github.com/roboflow/rf-detr.git@1e63dbad402eea10f110e86013361d6b02ee0c09\n"
                "See the documentation for more details."
            )
        if not isinstance(model, AIModelEntity):
            raise TypeError("model must be an instance of AIModelEntity")
        self.model = None
        self.metadata = None
        self.device = PlatformDetector.get_device()
        logging.info(f"ℹ️ RFDETRDetector will use '{self.device}' device.")

        if model:
            self.load_model(model)

    def _detect_model_variant(self, model_path: str):
        """
        Automatically detect the correct RF-DETR variant by trying to load the weights.
        Returns the appropriate RF-DETR class or None if all attempts fail.
        """
        variants = [
            ("Nano", RFDETRNano),
            ("Small", RFDETRSmall),
            ("Medium", RFDETRMedium),
            ("Base", RFDETRBase),
            ("Large", RFDETRLarge)
        ]
        
        for variant_name, variant_class in variants:
            try:
                logging.info(f"🔍 Trying RF-DETR {variant_name} variant...")
                temp_model = variant_class(pretrain_weights=model_path)
                logging.info(f"✅ Successfully loaded RF-DETR {variant_name} variant")
                return temp_model, variant_name
            except Exception as e:
                # Only log at debug level to avoid cluttering logs
                logging.debug(f"RF-DETR {variant_name} variant failed: {e}")
                continue
        
        return None, None

    def load_model(self, model: AIModelEntity):
        if not isinstance(model, AIModelEntity):
            raise TypeError("model must be an instance of AIModelEntity")
        self.metadata = model
        path = DatabaseManager.STORAGE_PATHS["models"] / model.file
        
        if not path.is_file() or path.stat().st_size == 0:
            logging.error(f"❌ Model file not found or empty: {path}")
            self.model = None
            return False
            
        try:
            loaded_model, variant_name = self._detect_model_variant(path.as_posix())
            
            if loaded_model is None:
                logging.error(f"❌ Could not load model with any RF-DETR variant")
                self.model = None
                return False
            
            self.model = loaded_model
            self.model.optimize_for_inference()
            logging.info(f"✅ Loaded {model.name} using RF-DETR {variant_name}")
            return True
        except Exception as e:
            logging.error(f"❌ Error loading RFDETR model {model.name}: {e}")
            self.model = None
            return False

    def detect_objects(self, frame, confidence_threshold=0.7, class_thresholds=None):
        if self.model is None:
            return []

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.model.predict(frame_rgb, confidence_threshold)

        class_names = self.metadata.get_classes() if hasattr(self.metadata, "get_classes") else None
        if not class_names:
            class_names = getattr(self.model, "class_names", None)

        detections = []
        for class_id, conf, xyxy in zip(results.class_id, results.confidence, results.xyxy):
            label = class_names[class_id - 1] if class_names else str(class_id)
            
            threshold = confidence_threshold
            if class_thresholds and label in class_thresholds:
                threshold = class_thresholds[label]

            if conf < threshold:
                continue
                
            detections.append({
                "label": label,
                "confidence": conf,
                "bbox": xyxy
            })

        return detections
