import cv2
import threading
import time
from collections import defaultdict
import logging

class VideoDebugger:
    """Real-time visualization of video streams with detections."""

    def __init__(self, enable_visualization=True):
        self.enable_visualization = enable_visualization
        self.windows = {}
        self.lock = threading.Lock()
        self.fps_tracker = defaultdict(lambda: {"start_time": time.time(), "frame_count": 0})
        self._cv_lock = threading.Lock()  # Prevent OpenCV segfaults

    def show_frame(self, pipeline_id, worker_source_id, frame):
        """Display frame with FPS overlay."""
        if not self.enable_visualization or frame is None:
            return

        window_name = f"Pipeline {pipeline_id} - {worker_source_id}"
        
        try:
            # Serialize ALL OpenCV operations to prevent segfaults
            with self._cv_lock:
                with self.lock:
                    if window_name not in self.fps_tracker:
                        self.fps_tracker[window_name] = {"start_time": time.time(), "frame_count": 0}

                    self.fps_tracker[window_name]["frame_count"] += 1
                    elapsed_time = time.time() - self.fps_tracker[window_name]["start_time"]
                    fps = self.fps_tracker[window_name]["frame_count"] / max(elapsed_time, 1e-5)

                    if window_name not in self.windows:
                        self.windows[window_name] = True
                
                # Make a copy to avoid modifying the original frame from multiple threads
                display_frame = frame.copy()
                
                try:
                    cv2.putText(display_frame, f"FPS: {fps:.2f}", (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
                    cv2.imshow(window_name, display_frame)
                    key = cv2.waitKey(1) & 0xFF
                    
                    if key == ord('q'):
                        self._close_window_unsafe(window_name)
                except Exception as e:
                    logging.error(f"Error displaying frame for {window_name}: {e}")
                    
        except Exception as e:
            logging.error(f"Error in show_frame for {window_name}: {e}")

    def _close_window_unsafe(self, window_name):
        """Close window without acquiring locks (called when already locked)."""
        if window_name in self.windows:
            try:
                cv2.destroyWindow(window_name)
            except Exception as e:
                logging.error(f"Error closing window {window_name}: {e}")
            del self.windows[window_name]

    def close_window(self, window_name):
        """Close specific window."""
        with self._cv_lock:
            with self.lock:
                self._close_window_unsafe(window_name)
    
    def is_window_open(self, pipeline_id):
        """Check if a window is open for a given pipeline."""
        with self.lock:
            # Check if any window exists for this pipeline
            for window_name in self.windows.keys():
                if f"Pipeline {pipeline_id}" in window_name:
                    return True
            return False

    def close_all(self):
        """Close all windows."""
        with self.lock:
            window_list = list(self.windows.keys())
        
        with self._cv_lock:
            try:
                for window in window_list:
                    try:
                        cv2.destroyWindow(window)
                    except Exception as e:
                        logging.debug(f"Error destroying window {window}: {e}")
                cv2.waitKey(1)
            except Exception as e:
                logging.error(f"Error in close_all: {e}")
        
        with self.lock:
            self.windows.clear()
