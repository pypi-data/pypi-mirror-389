import logging
import time
import threading
import queue
from ..detection.detection_processing.HumanDetectionProcessor import HumanDetectionProcessor
from ..detection.detection_processing.PPEDetectionProcessor import PPEDetectionProcessor
from .PipelineConfigManager import PipelineConfigManager
from .PipelinePrepocessor import PipelinePrepocessor
from ..repositories.WorkerSourcePipelineDebugRepository import WorkerSourcePipelineDebugRepository
from ..repositories.WorkerSourcePipelineDetectionRepository import WorkerSourcePipelineDetectionRepository
from ..repositories.WorkerSourcePipelineRepository import WorkerSourcePipelineRepository
from ..streams.VideoStreamManager import VideoStreamManager
from ..ai.VideoDebugger import VideoDebugger
from ..ai.FrameDrawer import FrameDrawer
from ..tracker.TrackerManager import TrackerManager
from ..detection.BaseDetector import BaseDetector
from ..streams.RTMPStreamer import RTMPStreamer
from ..util.PipelinePreviewChecker import PipelinePreviewChecker


class PipelineProcessor:
    """Handles pipeline processing including preprocessing, AI model inference, tracking, and video stream processing."""

    def __init__(self, pipeline, detector: BaseDetector, enable_visualization=True):
        self._pipeline = pipeline
        self.running = True
        self.video_debugger = VideoDebugger(enable_visualization)
        self.tracker_manager = TrackerManager()
        self.detector = detector
        self.config_manager = PipelineConfigManager()
        self.preprocessor = PipelinePrepocessor()
        self.detection_processor = None
        self.threshold = 0.7

        # Keep the latest frame for detection; size=1 and we overwrite when full
        self.frame_queue = queue.Queue(maxsize=1)

        self.tracked_objects_render = []
        self.detection_thread = None
        self.frame_counter = 0
        self.frame_drawer = FrameDrawer()
        self.pipeline_id = pipeline.id
        self.worker_source_id = pipeline.worker_source_id

        self.rtmp_streamer = None
        self.rtmp_streaming_active = False
        self.last_preview_check_time = 0
        self.preview_check_interval = 10.0  # Check every 10 seconds (reduced from 5s to save CPU)
        self.pipeline_repo = WorkerSourcePipelineRepository()
        
        # RTMP frame rate limiting to reduce CPU
        self.last_rtmp_frame_time = 0
        self.rtmp_frame_interval = 1.0 / 25.0  # 25 FPS for RTMP (matching render FPS)

        self.detection_processor_codes = [
            PPEDetectionProcessor.code,
            HumanDetectionProcessor.code,
        ]

        self.debug_flag = False
        self.debug_repo = WorkerSourcePipelineDebugRepository()
        self.detection_repo = WorkerSourcePipelineDetectionRepository()
        
        # Frame recovery mechanism
        self.consecutive_frame_failures = 0
        self.max_consecutive_failures = 150  # 1.5 seconds at 0.01s intervals
        self.last_successful_frame_time = time.time()
        self.stream_recovery_timeout = 30.0  # 30 seconds timeout for stream recovery
        
        # HEVC error tracking
        self.hevc_error_count = 0
        self.last_hevc_recovery = 0
        self.hevc_recovery_cooldown = 30.0  # 30 seconds between HEVC recovery attempts
        
        self.base_detection_interval = 1.0 / 3.0
        self.detection_interval = self.base_detection_interval
        self.is_fps_user_configured = False

    def update_config(self, pipeline):
        """Updates the pipeline configuration."""
        self._pipeline = pipeline
        self._update_config_internal()

    def load_detector(self, detector: BaseDetector):
        logging.info(f"🔄 Loading new detector for pipeline {self.pipeline_id}")
        self.detector = detector
        self._update_detection_processor()
        logging.info(f"✅ Detector updated for pipeline {self.pipeline_id}")

    def _get_detection_processor_code(self):
        for code in self.detection_processor_codes:
            if self.config_manager.is_feature_enabled(code):
                return code
        return None
    
    def _get_detection_processor(self, code):
        if code == PPEDetectionProcessor.code:
            return PPEDetectionProcessor()
        elif code == HumanDetectionProcessor.code:
            return HumanDetectionProcessor()
        else:
            return None
    
    def _update_detection_processor(self):
        code = self._get_detection_processor_code()
        if self.detection_processor and self.detection_processor.code == code:
            return
        
        self.detection_processor = self._get_detection_processor(code)
        if self.detection_processor:
            self.frame_drawer.update_config(
                icons=self.detection_processor.icons,
                violation_labels=self.detection_processor.violation_labels,
                compliance_labels=self.detection_processor.compliance_labels,
            )
            multi_instance_classes = []
            if hasattr(self.detection_processor, 'get_multi_instance_classes'):
                multi_instance_classes = self.detection_processor.get_multi_instance_classes()
            
            self.tracker_manager.update_config(
                attribute_labels=self.detection_processor.labels,
                exclusive_attribute_groups=self.detection_processor.exclusive_labels,
                multi_instance_classes=multi_instance_classes
            )
        else:
            # Reset drawer/tracker when no processor enabled
            self.frame_drawer.update_config()
            self.tracker_manager.update_config([], [], [])

    def _update_config_internal(self):
        self.config_manager.update(self.pipeline_id)
        self.preprocessor.update(self.config_manager)
        self.base_detection_interval, self.is_fps_user_configured = self._get_detection_interval()
        self.detection_interval = self.base_detection_interval
        self._update_detection_processor()
        
        # Reset failure counters on config update
        self.consecutive_frame_failures = 0
        self.last_successful_frame_time = time.time()

        ai_model = self.detector.metadata if self.detector else None
        if self.detection_processor:
            config = self.config_manager.get_feature_config(self.detection_processor.code)
            self.detection_processor.update(self.config_manager, ai_model)
            self.threshold = config.get("minimumDetectionConfidence", 0.7)

            if self.detection_processor.code == HumanDetectionProcessor.code:
                self.frame_drawer.polygons = [((0, 0, 255), p) for p in self.detection_processor.restricted_areas]
        else:
            self.threshold = 0.7

    def process_pipeline(self, video_manager: VideoStreamManager):
        pipeline_id = self.pipeline_id
        worker_source_id = self.worker_source_id
        
        logging.info(f"🎯 Running pipeline processing for pipeline {pipeline_id} | Source: {worker_source_id}")

        self._update_config_internal()
        self.consecutive_frame_failures = 0
        self.last_successful_frame_time = time.time()

        initial_frame = self._wait_for_frame(video_manager)
        if initial_frame is None:
            logging.error(f"❌ Pipeline {pipeline_id} | Source {worker_source_id}: No initial frame available. Exiting...")
            return
        
        # Auto-adjust FPS based on resolution when user hasn't configured FPS
        if not self.is_fps_user_configured:
            self.detection_interval = self._auto_adjust_detection_interval_for_resolution(initial_frame)
            logging.info(f"📊 Pipeline {pipeline_id}: Auto-adjusted FPS to {1.0/self.detection_interval:.1f} based on {initial_frame.shape[1]}x{initial_frame.shape[0]} resolution (no user config)")
        else:
            logging.info(f"📊 Pipeline {pipeline_id}: Using user-configured FPS {1.0/self.detection_interval:.1f} for {initial_frame.shape[1]}x{initial_frame.shape[0]} stream")

        self.detection_thread = threading.Thread(
            target=self._detection_worker,
            name=f"detection-{pipeline_id}",
            daemon=True
        )
        self.detection_thread.start()

        target_render_fps = 25.0
        target_frame_time = 1.0 / target_render_fps
        last_preview_check = 0

        try:
            while self.running:
                loop_start = time.time()
                
                frame = video_manager.get_frame(worker_source_id)

                if frame is None:
                    if not self._handle_frame_failure(video_manager, worker_source_id):
                        break
                    time.sleep(0.04)
                    continue
                    
                self.consecutive_frame_failures = 0
                self.last_successful_frame_time = loop_start
                self.frame_counter += 1

                # Check preview status less frequently
                if loop_start - last_preview_check >= self.preview_check_interval:
                    self._check_and_update_rtmp_streaming()
                    last_preview_check = loop_start
                
                # For RTMP, also check if it's time to send a frame (rate limiting)
                should_draw_for_rtmp = (
                    self.rtmp_streaming_active and 
                    self.rtmp_streamer is not None and
                    (loop_start - self.last_rtmp_frame_time >= self.rtmp_frame_interval)
                )
                
                if should_draw_for_rtmp or self.debug_flag:
                    try:
                        frame_to_draw = frame.copy()
                        self.frame_drawer.draw_polygons(frame_to_draw)
                        drawn_frame = self.frame_drawer.draw_frame(
                            frame_to_draw,
                            self.tracked_objects_render,
                            with_trails=True,
                            trail_length=int(max(1, 2 / self.detection_interval))
                        )
                    except Exception as e:
                        logging.error(f"❌ Draw failed, using raw frame: {e}")
                        drawn_frame = frame
                else:
                    drawn_frame = None  # Don't waste CPU drawing if not needed

                if self.debug_flag:
                    tracked_objects_render = self._process_frame(frame)
                    try:
                        debug_frame = frame.copy()
                        self.debug_repo.update_debug_entries_by_pipeline_id(
                            self.pipeline_id,
                            self.frame_drawer.draw_frame(debug_frame, tracked_objects_render),
                            tracked_objects_render
                        )
                    except Exception as e:
                        logging.warning(f"Debug save failed: {e}")
                    self.debug_flag = False

                if self.rtmp_streaming_active:
                    if self.rtmp_streamer is None:
                        try:
                            self.rtmp_streamer = RTMPStreamer(self.pipeline_id)
                            logging.info(f"🎬 RTMP streamer initialized for pipeline {pipeline_id} (preview requested)")
                            self.last_rtmp_frame_time = 0  # Reset frame time on new stream
                        except Exception as e:
                            logging.error(f"❌ Failed to initialize RTMP streamer for pipeline {pipeline_id}: {e}")
                            self.rtmp_streamer = None

                    if self.rtmp_streamer and drawn_frame is not None:
                        # Frame already rate-limited by drawing logic above
                        try:
                            self.rtmp_streamer.push_frame(drawn_frame)
                            self.last_rtmp_frame_time = loop_start
                        except Exception as e:
                            logging.error(f"❌ RTMP push error for pipeline {pipeline_id}: {e}")
                            if "initialization_failed" in str(e).lower():
                                try:
                                    self.rtmp_streamer.stop_stream()
                                except Exception:
                                    pass
                                self.rtmp_streamer = None
                elif self.rtmp_streamer is not None:
                    try:
                        logging.info(f"🛑 Stopping RTMP streamer for pipeline {pipeline_id} (preview expired)")
                        self.rtmp_streamer.stop_stream()
                    except Exception as e:
                        logging.error(f"❌ Error stopping RTMP streamer: {e}")
                    finally:
                        self.rtmp_streamer = None

                # Only feed frames to detection queue if detection processor is active
                if self.detection_processor is not None:
                    if not self.frame_queue.full():
                        self.frame_queue.put_nowait(frame)
                
                loop_elapsed = time.time() - loop_start
                sleep_time = max(0.001, target_frame_time - loop_elapsed)
                time.sleep(sleep_time)

        except Exception as e:
            logging.error(f"❌ Error in pipeline {pipeline_id}: {e}", exc_info=True)

    def _process_frame(self, frame):
        dimension = frame.shape[:2]
        processed_frame = self.preprocessor.apply(frame)
        
        class_thresholds = {}
        ai_model = self.detector.metadata if self.detector else None
        
        if self.detection_processor:
            if self.detection_processor.code == PPEDetectionProcessor.code:
                class_thresholds.update(self.detection_processor.get_class_thresholds())
            elif self.detection_processor.code == HumanDetectionProcessor.code:
                main_threshold = self.detection_processor.get_main_class_threshold(ai_model)
                if main_threshold and ai_model and ai_model.get_main_class():
                    class_thresholds[ai_model.get_main_class()] = main_threshold
        
        detections = []
        if self.detector:
            detections = self.detector.detect_objects(processed_frame, self.threshold, class_thresholds)
        
        detections = self.preprocessor.revert_detections_bboxes(detections, dimension)
        
        if self.detection_processor:
            matched_results = self.detection_processor.process(detections, dimension)
            return self.tracker_manager.track_objects(matched_results)
        else:
            return self.tracker_manager.track_objects(detections)

    def _detection_worker(self):
        """Runs detection in a separate thread and updates configuration periodically."""
        pipeline_id = self.pipeline_id
        worker_source_id = self.worker_source_id
        last_detection_time = time.time()
        last_config_update_time = time.time()
        config_update_interval = 5  # seconds

        while self.running:
            try:
                # Calculate how long to wait for next detection
                current_time = time.time()
                time_since_last_detection = current_time - last_detection_time
                time_until_next_detection = max(0.1, self.detection_interval - time_since_last_detection)
                
                # Wait for frame with timeout aligned to detection interval
                frame = self.frame_queue.get(block=True, timeout=time_until_next_detection)
                
                # Check for poison pill (None = stop signal)
                if frame is None:
                    logging.debug(f"Detection worker for {pipeline_id} received stop signal")
                    break
                
                current_time = time.time()

                # Update config periodically
                if (current_time - last_config_update_time) >= config_update_interval:
                    self._update_config_internal()
                    last_config_update_time = current_time

                # Keep only the latest frame if we fell behind
                try:
                    while True:
                        newer = self.frame_queue.get_nowait()
                        if newer is None:  # Stop signal
                            logging.debug(f"Detection worker for {pipeline_id} received stop signal")
                            return
                        frame = newer
                except queue.Empty:
                    pass

                # Respect detection interval - skip if too soon
                if (current_time - last_detection_time) < self.detection_interval:
                    # Sleep the remaining time instead of busy-waiting
                    remaining_time = self.detection_interval - (current_time - last_detection_time)
                    if remaining_time > 0.01:
                        time.sleep(remaining_time)
                    continue
                
                last_detection_time = current_time

                if self.detection_processor is None or frame is None or frame.size == 0:
                    self.tracked_objects_render = []
                    continue

                self.tracked_objects_render = self._process_frame(frame)
                
                # Save to database if enabled
                if self.config_manager.is_feature_enabled("db"):
                    self.detection_processor.save_to_db(
                        pipeline_id,
                        worker_source_id,
                        self.frame_counter,
                        self.tracked_objects_render,
                        frame,
                        self.frame_drawer
                    )

                if self.config_manager.is_feature_enabled("webhook") or self.config_manager.is_feature_enabled("mqtt"):
                    self.detection_repo.save_detection(
                        pipeline_id,
                        frame,
                        self.tracked_objects_render,
                        self.frame_drawer
                    )

            except queue.Empty:
                # Timeout occurred - this is normal, just continue to next iteration
                pass
            except Exception as e:
                logging.error(f"❌ Error in detection thread for pipeline {pipeline_id}: {e}", exc_info=True)
    
    def _wait_for_frame(self, video_manager, max_wait_time=30.0):
        logging.info(f"⏳ Waiting for initial frame from {self.worker_source_id}...")
        
        is_ready = video_manager.wait_for_stream_ready(self.worker_source_id, timeout=max_wait_time)

        if is_ready:
            frame = video_manager.get_frame(self.worker_source_id)
            if frame is not None:
                logging.info(f"✅ Initial frame received from {self.worker_source_id}")
                return frame
            else:
                logging.error(f"❌ Stream {self.worker_source_id} reported ready, but the first frame could not be retrieved.")
                self._log_stream_diagnostics(video_manager, self.worker_source_id)
                return None
        else:
            logging.error(f"❌ Timed out after {max_wait_time}s waiting for first frame from {self.worker_source_id}.")
            self._log_stream_diagnostics(video_manager, self.worker_source_id)
            return None

    def _handle_frame_failure(self, video_manager, worker_source_id):
        """Handle frame retrieval failures with progressive backoff and recovery attempts."""
        self.consecutive_frame_failures += 1
        
        if not video_manager.has_stream(worker_source_id):
            logging.info(f"🛑 Stream {worker_source_id} was removed, stopping pipeline")
            return False
        
        time_since_last_frame = time.time() - self.last_successful_frame_time
        if time_since_last_frame > self.stream_recovery_timeout:
            logging.error(f"❌ Stream {worker_source_id} recovery timeout ({self.stream_recovery_timeout}s). Stopping pipeline.")
            return False
        
        if self.consecutive_frame_failures <= 10:
            if self.consecutive_frame_failures % 5 == 1:
                logging.debug(f"⚠️ No frame for {worker_source_id} (attempt {self.consecutive_frame_failures})")
            time.sleep(0.01)
        elif self.consecutive_frame_failures <= 50:
            if self.consecutive_frame_failures % 10 == 1:
                logging.warning(f"⚠️ No frame for {worker_source_id} (attempt {self.consecutive_frame_failures}). Stream may be reconnecting...")
            time.sleep(0.05)
        elif self.consecutive_frame_failures <= self.max_consecutive_failures:
            if self.consecutive_frame_failures % 20 == 1:
                logging.warning(f"⚠️ Persistent frame issues for {worker_source_id} (attempt {self.consecutive_frame_failures}). Checking stream health...")
                self._log_stream_diagnostics(video_manager, worker_source_id)
                if self.consecutive_frame_failures % 60 == 1:
                    if self._should_attempt_hevc_recovery(video_manager, worker_source_id):
                        logging.info("🔧 Attempting HEVC-specific recovery for persistent frame failures...")
                        if self._handle_hevc_recovery(video_manager, worker_source_id):
                            logging.info("✅ HEVC recovery successful, continuing pipeline...")
                            return True
            time.sleep(0.1)
        else:
            logging.error(f"❌ Too many consecutive frame failures for {worker_source_id} ({self.consecutive_frame_failures}). Stopping pipeline.")
            self._log_stream_diagnostics(video_manager, worker_source_id)
            return False
        
        return True
    
    def _log_stream_diagnostics(self, video_manager, worker_source_id):
        try:
            stream_url = video_manager.get_stream_url(worker_source_id)
            is_file = video_manager.is_video_file(worker_source_id)
            if hasattr(video_manager, 'streams') and worker_source_id in video_manager.streams:
                stream = video_manager.streams[worker_source_id]
                state = stream.get_state() if hasattr(stream, 'get_state') else "unknown"
                is_connected = stream.is_connected() if hasattr(stream, 'is_connected') else "unknown"
                
                logging.info(f"📊 Stream diagnostics for {worker_source_id}:")
                logging.info(f"   URL: {stream_url}")
                logging.info(f"   Type: {'Video file' if is_file else 'Live stream'}")
                logging.info(f"   State: {state}")
                logging.info(f"   Connected: {is_connected}")
                logging.info(f"   Time since last frame: {time.time() - self.last_successful_frame_time:.1f}s")
                
                if hasattr(stream, 'get_codec_info'):
                    codec_info = stream.get_codec_info()
                    if codec_info:
                        logging.info(f"   Codec: {codec_info}")
                        if 'hevc' in str(codec_info).lower() or 'h265' in str(codec_info).lower():
                            logging.warning("   ⚠️ HEVC stream detected - potential QP/POC errors")
                
                if hasattr(stream, 'get_recent_errors'):
                    recent_errors = stream.get_recent_errors()
                    if recent_errors:
                        hevc_errors = [err for err in recent_errors if 'cu_qp_delta' in str(err.get('error', '')) or 'Could not find ref with POC' in str(err.get('error', ''))]
                        if hevc_errors:
                            logging.warning(f"   🔥 Recent HEVC errors: {len(hevc_errors)}")
                            self.hevc_error_count += len(hevc_errors)
                            for i, err in enumerate(hevc_errors[-3:]):
                                logging.warning(f"   🔥 HEVC Error {i+1}: {err.get('error', '')[:100]}...")
            else:
                logging.info(f"📊 Stream {worker_source_id} not found in registry; checking device directly...")
        except Exception as e:
            logging.error(f"Error getting stream diagnostics: {e}")

    def _should_attempt_hevc_recovery(self, video_manager, worker_source_id) -> bool:
        current_time = time.time()
        if current_time - self.last_hevc_recovery < self.hevc_recovery_cooldown:
            logging.debug(f"HEVC recovery on cooldown ({current_time - self.last_hevc_recovery:.1f}s elapsed)")
            return False
        
        if hasattr(video_manager, 'streams') and worker_source_id in video_manager.streams:
            stream = video_manager.streams[worker_source_id]
            if hasattr(stream, 'get_recent_errors'):
                recent_errors = stream.get_recent_errors(max_age_seconds=60)
                hevc_errors = [err for err in recent_errors if 
                               'cu_qp_delta' in str(err.get('error', '')) or 
                               'Could not find ref with POC' in str(err.get('error', ''))]
                if len(hevc_errors) >= 3:
                    logging.info(f"HEVC recovery warranted: {len(hevc_errors)} HEVC errors in last minute")
                    return True
        
        if self.hevc_error_count >= 5:
            logging.info(f"HEVC recovery warranted: {self.hevc_error_count} total HEVC errors detected")
            return True
        
        return False

    def _handle_hevc_recovery(self, video_manager, worker_source_id):
        try:
            self.last_hevc_recovery = time.time()
            logging.info(f"🔧 Attempting HEVC stream recovery for {worker_source_id}")
            stream_url = video_manager.get_stream_url(worker_source_id)
            if not stream_url:
                logging.error(f"   Cannot get stream URL for {worker_source_id}")
                return False
            
            # Use internal methods to restart the stream without affecting reference counting
            video_manager._stop_stream(worker_source_id)
            time.sleep(1.0)
            video_manager._start_stream(worker_source_id, stream_url)
            time.sleep(2.0)
            
            if not video_manager.has_stream(worker_source_id):
                logging.error(f"   Failed to recreate stream {worker_source_id}")
                return False
            
            self.reset_frame_failure_counters()
            self.hevc_error_count = 0
            logging.info(f"✅ HEVC recovery attempt completed for {worker_source_id}")
            return True
        except Exception as e:
            logging.error(f"❌ HEVC recovery failed for {worker_source_id}: {e}")
            return False

    def stop(self):
        """Stop processor and cleanup resources."""
        if not self.running:
            return
        logging.info("🛑 Stopping PipelineProcessor...")
        self.running = False

        # Wake up detection thread immediately with poison pill
        try:
            self.frame_queue.put_nowait(None)
        except queue.Full:
            try:
                self.frame_queue.get_nowait()
                self.frame_queue.put_nowait(None)
            except:
                pass

        # Stop RTMP streamer
        if hasattr(self, 'rtmp_streamer') and self.rtmp_streamer:
            try:
                self.rtmp_streamer.stop_stream()
            except Exception as e:
                logging.error(f"Error stopping RTMP streamer: {e}")
            finally:
                self.rtmp_streamer = None

        # Clear frame queue
        try:
            while True:
                try:
                    self.frame_queue.get_nowait()
                except queue.Empty:
                    break
        except Exception as e:
            logging.error(f"Error clearing frame queue: {e}")

        # Wait for detection thread (should exit quickly with poison pill)
        if self.detection_thread and self.detection_thread.is_alive():
            try:
                self.detection_thread.join(timeout=1.0)
                if self.detection_thread.is_alive():
                    logging.warning("Detection thread did not terminate cleanly within 1s")
            except Exception as e:
                logging.error(f"Error joining detection thread: {e}")
            finally:
                self.detection_thread = None

        # Unload detector immediately to free GPU memory
        if hasattr(self, 'detector') and self.detector:
            try:
                if hasattr(self.detector, 'model') and self.detector.model:
                    if hasattr(self.detector.model, 'cpu'):
                        self.detector.model.cpu()
                    self.detector.model = None
            except Exception as e:
                logging.debug(f"Error clearing detector: {e}")

        # Clear tracking data
        if hasattr(self, 'tracked_objects_render'):
            self.tracked_objects_render.clear()
        
        # Clear tracker state
        if hasattr(self, 'tracker_manager') and self.tracker_manager:
            try:
                if hasattr(self.tracker_manager, 'track_uuid_map'):
                    self.tracker_manager.track_uuid_map.clear()
                if hasattr(self.tracker_manager, 'track_count_map'):
                    self.tracker_manager.track_count_map.clear()
                if hasattr(self.tracker_manager, 'track_attributes_presence'):
                    self.tracker_manager.track_attributes_presence.clear()
                if hasattr(self.tracker_manager, 'track_last_seen'):
                    self.tracker_manager.track_last_seen.clear()
            except Exception as e:
                logging.error(f"Error clearing tracker state: {e}")

        # Close debugger
        try:
            if hasattr(self, 'video_debugger'):
                self.video_debugger.close_all()
        except Exception as e:
            logging.error(f"Error closing video debugger: {e}")
        
        # Force garbage collection
        import gc
        gc.collect()

        logging.info("✅ PipelineProcessor stopped successfully")
        
    def _get_detection_interval(self):
        """Returns (interval, is_user_configured) tuple."""
        config = self.config_manager.get_feature_config("processing_speed")
        fps = config.get("decimal", None)
        
        # Check if user explicitly configured FPS
        is_user_configured = fps is not None
        
        if fps is None or fps <= 0:
            fps = 3.0  # default 3 fps when not configured
        
        return 1.0 / fps, is_user_configured
    
    def _auto_adjust_detection_interval_for_resolution(self, frame):
        """
        Auto-adjust detection interval based on frame resolution.
        Automatically applies when user hasn't configured processing_speed FPS.
        User-configured FPS always takes precedence.
        """
        if frame is None:
            return self.base_detection_interval
        
        height, width = frame.shape[:2]
        total_pixels = height * width
        
        # Define resolution tiers
        PIXELS_4K = 3840 * 2160  # ~8.3M pixels
        PIXELS_2K = 2560 * 1440  # ~3.7M pixels
        
        base_interval = self.base_detection_interval
        
        # Adjust based on resolution
        if total_pixels >= PIXELS_4K:
            # 4K: Reduce FPS by 50% (double the interval)
            adjusted_interval = base_interval * 2.0
            logging.debug(f"📊 4K stream detected ({width}x{height}): FPS reduced to {1.0/adjusted_interval:.1f}")
        elif total_pixels >= PIXELS_2K:
            # 2K: Reduce FPS by 25% (increase interval by 1.33x)
            adjusted_interval = base_interval * 1.33
            logging.debug(f"📊 2K stream detected ({width}x{height}): FPS reduced to {1.0/adjusted_interval:.1f}")
        else:
            # 1080p and below: Use full configured FPS
            adjusted_interval = base_interval
        
        return adjusted_interval

    def enable_debug(self):
        self.debug_flag = True
        self.consecutive_frame_failures = 0
        self.last_successful_frame_time = time.time()
    
    def _check_and_update_rtmp_streaming(self):
        """
        Check if RTMP streaming should be active based on preview requests.
        Updates the rtmp_streaming_active flag.
        """
        try:
            # Get fresh pipeline data from database
            pipeline = self.pipeline_repo.get_worker_source_pipeline(self.pipeline_id)
            
            if not pipeline:
                logging.warning(f"⚠️ Pipeline {self.pipeline_id} not found in database")
                self.rtmp_streaming_active = False
                return
            
            # Check if preview is active using the utility
            should_stream = PipelinePreviewChecker.should_stream_rtmp(
                pipeline.last_preview_request_at,
                preview_window_seconds=300  # 5 minutes
            )
            
            self.rtmp_streaming_active = should_stream
            
        except Exception as e:
            logging.error(f"❌ Error checking preview status for pipeline {self.pipeline_id}: {e}")
            # On error, disable streaming to be safe
            self.rtmp_streaming_active = False
    
    def reset_frame_failure_counters(self):
        logging.info(f"🔄 Resetting frame failure counters for pipeline {self.pipeline_id}")
        self.consecutive_frame_failures = 0
        self.last_successful_frame_time = time.time()
        self.hevc_error_count = 0
    
    def get_hevc_diagnostics(self, video_manager) -> dict:
        diagnostics = {
            'hevc_error_count': self.hevc_error_count,
            'last_hevc_recovery': self.last_hevc_recovery,
            'time_since_last_recovery': time.time() - self.last_hevc_recovery,
            'recovery_cooldown_remaining': max(0, self.hevc_recovery_cooldown - (time.time() - self.last_hevc_recovery)),
            'consecutive_failures': self.consecutive_frame_failures,
            'time_since_last_frame': time.time() - self.last_successful_frame_time,
        }
        if hasattr(video_manager, 'streams') and self.worker_source_id in video_manager.streams:
            stream = video_manager.streams[self.worker_source_id]
            if hasattr(stream, 'get_codec_info'):
                diagnostics['codec'] = stream.get_codec_info()
            if hasattr(stream, 'get_recent_errors'):
                recent_errors = stream.get_recent_errors(max_age_seconds=300)
                hevc_errors = [err for err in recent_errors if 
                               'cu_qp_delta' in str(err.get('error', '')) or 
                               'Could not find ref with POC' in str(err.get('error', ''))]
                diagnostics['recent_hevc_errors'] = len(hevc_errors)
                diagnostics['total_recent_errors'] = len(recent_errors)
        return diagnostics