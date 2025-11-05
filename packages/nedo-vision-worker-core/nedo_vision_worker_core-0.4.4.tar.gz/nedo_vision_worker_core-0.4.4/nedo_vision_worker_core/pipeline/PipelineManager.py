import logging
import time
import threading
from typing import Dict
from concurrent.futures import ThreadPoolExecutor
from .PipelineProcessor import PipelineProcessor
from ..streams.VideoStreamManager import VideoStreamManager

class PipelineManager:
    """Manages AI pipeline execution with thread pooling for scalability."""

    def __init__(self, video_manager: VideoStreamManager, on_pipeline_stopped, max_workers=None):
        # Auto-detect optimal worker count if not specified
        if max_workers is None:
            import os
            cpu_count = os.cpu_count() or 4
            # Reserve 2 cores for system/video streams, use rest for pipelines
            max_workers = max(4, cpu_count - 2)
        
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(
            max_workers=max_workers,
            thread_name_prefix="pipeline-worker"
        )
        self.pipeline_futures = {}  # {pipeline_id: Future}
        self.pipeline_metadata = {}  # {pipeline_id: metadata}
        self.video_manager = video_manager
        self.processors: Dict[str, PipelineProcessor] = {}  # {pipeline_id: PipelineProcessor}
        self.running = True
        self._stopping_pipelines = set()
        self._stop_lock = threading.Lock()
        self.on_pipeline_stopped = on_pipeline_stopped
        
        # Stagger pipeline startup to reduce CPU spikes
        self._last_pipeline_start = 0
        self._pipeline_start_delay = 1.0  # 1 second between pipeline starts
        self._start_lock = threading.Lock()
        
        logging.info(f"🚀 PipelineManager initialized with {max_workers} worker threads")

    def start_pipeline(self, pipeline, detector):
        """Start a pipeline processing."""
        pipeline_id = pipeline.id
        worker_source_id = pipeline.worker_source_id

        if not self.running:
            logging.warning(f"⚠️ Attempt to start pipeline {pipeline_id} after shutdown.")
            return

        if self.is_running(pipeline_id):
            logging.warning(f"⚠️ Pipeline {pipeline_id} is already running.")
            return

        # Stagger pipeline starts to reduce CPU spikes
        with self._start_lock:
            time_since_last_start = time.time() - self._last_pipeline_start
            if time_since_last_start < self._pipeline_start_delay:
                delay = self._pipeline_start_delay - time_since_last_start
                logging.info(f"⏳ Staggering pipeline {pipeline_id} start by {delay:.2f}s to reduce CPU spike")
                time.sleep(delay)
            self._last_pipeline_start = time.time()

        logging.info(f"🚀 Starting Pipeline processing for pipeline: {pipeline_id} | Source: {worker_source_id} ({pipeline.name})")

        # Acquire video stream
        if not self.video_manager.acquire_stream(worker_source_id, pipeline_id):
            logging.error(f"❌ Failed to acquire stream {worker_source_id} for pipeline {pipeline_id}")
            return

        processor = PipelineProcessor(pipeline, detector, False)
        processor.frame_drawer.location_name = pipeline.location_name
        self.processors[pipeline_id] = processor

        active_count = len([f for f in self.pipeline_futures.values() if not f.done()])
        logging.info(f"📋 Submitting pipeline {pipeline_id} to thread pool (active: {active_count}/{self.max_workers})")
        
        try:
            # Submit to thread pool instead of creating dedicated thread
            future = self.executor.submit(
                self._pipeline_worker,
                pipeline_id,
                processor
            )
            
            # Add completion callback
            future.add_done_callback(lambda f: self._handle_pipeline_completion(pipeline_id, f))
            
            self.pipeline_futures[pipeline_id] = future
            self.pipeline_metadata[pipeline_id] = pipeline
            
            logging.info(f"✅ Pipeline {pipeline_id} submitted to thread pool")

        except Exception as e:
            logging.error(f"❌ Failed to submit pipeline {pipeline_id} to thread pool: {e}", exc_info=True)
            self.processors.pop(pipeline_id, None)
            self.video_manager.release_stream(worker_source_id, pipeline_id)
            raise
    
    def _pipeline_worker(self, pipeline_id: str, processor: PipelineProcessor):
        """Worker function executed in thread pool."""
        try:
            logging.info(f"🏁 Pipeline {pipeline_id} worker starting...")
            processor.process_pipeline(self.video_manager)
        except Exception as e:
            logging.error(f"❌ Unhandled error in pipeline {pipeline_id} worker: {e}", exc_info=True)
        finally:
            logging.info(f"🏁 Pipeline {pipeline_id} worker finished")

    def _handle_pipeline_completion(self, pipeline_id: str, future=None):
        """Handle cleanup when pipeline finishes."""
        with self._stop_lock:
            if pipeline_id in self._stopping_pipelines:
                return

        try:
            logging.info(f"🏁 Pipeline {pipeline_id} completed execution")
            
            # Log any exception from the future
            if future and not future.cancelled():
                try:
                    future.result(timeout=0)
                except Exception as e:
                    logging.error(f"Pipeline {pipeline_id} ended with exception: {e}")
        except Exception as e:
            logging.error(f"⚠️ Error in handling pipeline {pipeline_id} completion: {e}")
        finally:
            self.on_pipeline_stopped(pipeline_id)

    def stop_pipeline(self, pipeline_id: str):
        """Stop an AI processing pipeline."""
        with self._stop_lock:
            if pipeline_id in self._stopping_pipelines:
                logging.debug(f"Pipeline {pipeline_id} already being stopped, skipping")
                return
            self._stopping_pipelines.add(pipeline_id)

        try:
            pipeline = self.pipeline_metadata.get(pipeline_id)
            worker_source_id = pipeline.worker_source_id if pipeline else None

            # Stop processor first to signal threads
            processor = self.processors.pop(pipeline_id, None)
            if processor:
                processor.stop()

            # Cancel future if still pending/running
            future = self.pipeline_futures.pop(pipeline_id, None)
            if future and not future.done():
                logging.debug(f"Cancelling future for pipeline {pipeline_id}")
                future.cancel()
                
                # Wait briefly for graceful shutdown
                try:
                    future.result(timeout=1.0)
                except Exception as e:
                    logging.debug(f"Pipeline {pipeline_id} future ended: {e}")

            self.pipeline_metadata.pop(pipeline_id, None)

            # Release video stream
            if worker_source_id:
                self.video_manager.release_stream(worker_source_id, pipeline_id)

            logging.info(f"✅ Pipeline {pipeline_id} stopped successfully.")

        except Exception as e:
            logging.error(f"❌ Error during pipeline shutdown: {e}")
        
        finally:
            self._stopping_pipelines.discard(pipeline_id)
            self.on_pipeline_stopped(pipeline_id)

    def get_active_pipelines(self):
        """Returns a list of active pipeline IDs."""
        return list(self.pipeline_metadata.keys())

    def get_pipeline(self, pipeline_id):
        """Returns the pipeline metadata."""
        return self.pipeline_metadata.get(pipeline_id, None)

    def is_running(self, pipeline_id):
        """Check if pipeline is currently running."""
        future = self.pipeline_futures.get(pipeline_id)
        return future is not None and not future.done()

    def shutdown(self):
        """Shuts down the pipeline manager gracefully."""
        logging.info("🛑 Shutting down PipelineManager...")
        self.running = False

        # Stop all pipelines
        for pipeline_id in list(self.pipeline_futures.keys()):
            self.stop_pipeline(pipeline_id)

        # Shutdown thread pool
        logging.info("🛑 Shutting down thread pool executor...")
        self.executor.shutdown(wait=True)
        logging.info("✅ PipelineManager stopped.")
