import subprocess
import logging
import threading
import time
import numpy as np
import os
import sys
import cv2
import queue
from typing import Optional, Tuple, List
from ..util.PlatformDetector import PlatformDetector

# Set up a logger for this module
logger = logging.getLogger(__name__)

class RTMPStreamer:
    """
    Streams raw BGR frames to an RTMP server using a robust FFmpeg subprocess.
    
    Includes a 2-stage (HW -> CPU) fallback logic to handle
    encoder failures, such as NVENC session limits.
    This class is thread-safe.
    """
    
    # Class-level lock to stagger stream initialization across all instances
    _initialization_lock = threading.Lock()
    _last_initialization_time = 0
    _min_initialization_delay = 1.5  # 1.5 seconds between stream starts (increased from 0.5s)

    def __init__(self, pipeline_id: str, fps: int = 25, bitrate: str = "1500k"):
        self.pipeline_id = pipeline_id
        self.rtmp_server = os.environ.get("RTMP_SERVER", "rtmp://localhost:1935/live")
        self.rtmp_url = f"{self.rtmp_server}/{pipeline_id}"
        self.fps = max(int(fps), 1)
        self.bitrate = self._kbps(bitrate) # Store as integer kbps

        self.width: Optional[int] = None
        self.height: Optional[int] = None
        self._platform = PlatformDetector()
        
        # --- Internal State ---
        self._ffmpeg_process: Optional[subprocess.Popen] = None
        self._active_encoder_name: Optional[str] = None

        self._frame_queue = queue.Queue(maxsize=2)
        self._writer_thread: Optional[threading.Thread] = None
        self._stderr_thread: Optional[threading.Thread] = None
        
        # --- Concurrency and Lifecycle ---
        self._stop_evt = threading.Event()
        self._lock = threading.Lock() # Instance-level lock for state changes
        
        # --- State flags for failover ---
        self._initialization_failed = False # Hard failure on init or fallback failure
        self._hw_encoder_failed = threading.Event() # Use a thread-safe Event instance

    def _kbps(self, rate_str: str) -> int:
        """Converts a bitrate string (e.g., '1500k') to an integer in kbps."""
        return int(str(rate_str).lower().replace("k", "").strip())

    # -------------------- Public API --------------------

    def is_active(self) -> bool:
        """
        Checks if the stream is currently active and running.
        This method is thread-safe.
        """
        with self._lock:
            return self._ffmpeg_process is not None and self._ffmpeg_process.poll() is None

    def push_frame(self, frame: np.ndarray):
        """
        Pushes a raw BGR numpy array frame into the stream.
        
        If this is the first frame, it will trigger the stream initialization.
        If the stream's writer thread dies, this method will automatically
        attempt to clean up and restart.
        """
        # Don't accept frames if user stopped or init hard-failed
        if self._stop_evt.is_set() or self._initialization_failed:
            return

        # Get the current writer thread object *outside* the lock
        current_writer_snapshot = self._writer_thread
        
        # The FFmpeg process can die from startup failure (immediate termination)
        # or from runtime failure (pipe broken). In both cases, wait for the 
        # writer thread to fully exit before checking the HW flag to avoid race conditions.
        process_active = self.is_active()
        
        # If we have a writer thread but no active process, join it to ensure flags are set
        if current_writer_snapshot is not None and threading.current_thread() != current_writer_snapshot:
            if not process_active:  # Process is dead or missing
                current_writer_snapshot.join(timeout=1.0)
        
        is_running = process_active and current_writer_snapshot is not None and current_writer_snapshot.is_alive()

        if not is_running:
            # Acquire the lock to perform the restart
            with self._lock:
                # Double-check: Another thread might have fixed it while we waited for the lock.
                if self._writer_thread is not None and self._writer_thread.is_alive():
                    pass # Nothing to do, another thread fixed it
                
                elif self._stop_evt.is_set() or self._initialization_failed:
                    pass # Stream is stopped or has hard-failed
                    
                else:
                    # Clean up the old process
                    self._internal_cleanup() 
                    
                    if frame is None:
                        return # Can't initialize with None
                    
                    self.height, self.width = frame.shape[:2]
                    try:
                        self._start_stream() 
                    except Exception as e:
                        logger.error(f"❌ RTMP stream (re)start failed for {self.pipeline_id}: {e}")
                        return
        
        # Put frame in queue, dropping the oldest if full
        try:
            self._frame_queue.put_nowait(frame)
        except queue.Full:
            try:
                self._frame_queue.get_nowait()  # Discard oldest
                self._frame_queue.put_nowait(frame)  # Retry push
            except (queue.Empty, queue.Full):
                pass # Race condition, frame lost, which is fine
    def stop_stream(self):
        """
        Stops the stream, closes subprocesses, and joins the writer thread.
        This method is idempotent and thread-safe.
        """
        if self._stop_evt.is_set():
            return
        logger.info(f"Stopping RTMP stream for {self.rtmp_url}")
        self._stop_evt.set()
        
        # Send a sentinel value to unblock the writer thread
        try:
            self._frame_queue.put_nowait(None)
        except queue.Full:
            pass

        # Wait for the writer thread to finish
        thread_to_join = self._writer_thread
        if thread_to_join and thread_to_join.is_alive() and threading.current_thread() != thread_to_join:
            thread_to_join.join(timeout=2.0)

        with self._lock:
            self._internal_cleanup()

    # -------------------- Internal Stream Management --------------------

    def _internal_cleanup(self):
        """
        Cleans up all stream resources. 
        MUST be called from within self._lock.
        """
        if self._ffmpeg_process:
            try:
                if self._ffmpeg_process.stdin:
                    self._ffmpeg_process.stdin.close()
                self._ffmpeg_process.terminate()
                self._ffmpeg_process.wait(timeout=0.1)
            except Exception:
                pass 
            
            try:
                if self._ffmpeg_process and self._ffmpeg_process.poll() is None:
                    self._ffmpeg_process.kill()
            except Exception:
                pass
            self._ffmpeg_process = None
            logger.info(f"FFmpeg process stopped for {self.pipeline_id}.")
        
        self._active_encoder_name = None
        self._writer_thread = None # Thread is dead or will be
        self._stderr_thread = None # Daemon, will die
        # Note: _hw_encoder_failed Event is NOT cleared. It's persistent.

    def _start_stream(self):
        """
        Starts the stream with a 2-stage FFmpeg fallback.
        
        Fallback logic:
        1. Try FFmpeg (HW)
        2. Try FFmpeg (CPU)
        """
        
        # Stagger initialization
        with RTMPStreamer._initialization_lock:
            current_time = time.time()
            time_since_last = current_time - RTMPStreamer._last_initialization_time
            if time_since_last < RTMPStreamer._min_initialization_delay:
                delay = RTMPStreamer._min_initialization_delay - time_since_last
                logger.info(f"⏳ Staggering RTMP initialization for {self.pipeline_id} by {delay:.2f}s")
                time.sleep(delay)
            RTMPStreamer._last_initialization_time = time.time()
        
        if self._stop_evt.is_set():
            logger.info(f"Initialization cancelled for {self.pipeline_id}, stop was called.")
            return

        # --- Stage 1: Try FFmpeg (HW) ---
        if not self._hw_encoder_failed.is_set():
            cmd, encoder_name = self._build_ffmpeg_cmd(force_cpu=False)
            
            if encoder_name != "libx264":
                try:
                    self._ffmpeg_process = subprocess.Popen(
                        cmd, 
                        stdin=subprocess.PIPE, 
                        stdout=subprocess.DEVNULL, 
                        stderr=subprocess.PIPE,
                        universal_newlines=False
                    )
                    
                    time.sleep(0.5) # Give it a moment to start or fail
                    if self._ffmpeg_process.poll() is not None:
                        stderr_output = self._ffmpeg_process.stderr.read().decode('utf-8', errors='ignore') if self._ffmpeg_process.stderr else "No error output"
                        raise RuntimeError(f"FFmpeg process terminated immediately. Error: {stderr_output}")
                    
                    self._start_writer_threads(encoder_name)
                    logger.info(f"✅ RTMP streaming started with FFmpeg ({encoder_name}): {self.rtmp_url}")
                    return

                except Exception as e_hw:
                    logger.warning(f"FFmpeg ({encoder_name}) failed to start for {self.pipeline_id}: {e_hw}. Falling back to CPU.")
                    self._hw_encoder_failed.set() # Set Event on HW failure
                    if self._ffmpeg_process:
                        try: self._ffmpeg_process.kill()
                        except Exception: pass
                    self._ffmpeg_process = None
            else:
                logger.info(f"No HW encoder found for {self.pipeline_id}. Skipping straight to CPU.")
                self._hw_encoder_failed.set() # Set Event if no HW
        else:
             logger.info(f"HW encoder previously failed for {self.pipeline_id}. Skipping straight to CPU.")

        # --- Stage 2: Try FFmpeg (CPU) ---
        try:
            cmd_cpu, encoder_name_cpu = self._build_ffmpeg_cmd(force_cpu=True)
            self._ffmpeg_process = subprocess.Popen(
                cmd_cpu, 
                stdin=subprocess.PIPE, 
                stdout=subprocess.DEVNULL, 
                stderr=subprocess.PIPE,
                universal_newlines=False
            )
            
            time.sleep(0.1)
            if self._ffmpeg_process.poll() is not None:
                stderr_output = self._ffmpeg_process.stderr.read().decode('utf-8', errors='ignore') if self._ffmpeg_process.stderr else "No error output"
                raise RuntimeError(f"FFmpeg CPU process terminated immediately. Error: {stderr_output}")

            self._start_writer_threads(encoder_name_cpu)
            logger.info(f"✅ RTMP streaming started with FFmpeg (CPU Fallback: {encoder_name_cpu}): {self.rtmp_url}")

        except Exception as e_cpu:
            if self._ffmpeg_process:
                try: self._ffmpeg_process.kill()
                except Exception: pass
            self._ffmpeg_process = None
            
            logger.error(f"FATAL: Failed to start FFmpeg CPU fallback for {self.pipeline_id}: {e_cpu}")
            self._initialization_failed = True
            
            raise RuntimeError(f"Failed to start FFmpeg CPU fallback for {self.pipeline_id}") from e_cpu
        
    def _start_writer_threads(self, encoder_name: str):
        """Helper to start the stderr and stdin writer threads."""
        self._active_encoder_name = encoder_name
        self._stderr_thread = threading.Thread(
            target=self._log_ffmpeg_stderr,
            args=(self._ffmpeg_process.stderr, self.pipeline_id),
            daemon=True
        )
        self._stderr_thread.start()
        
        self._writer_thread = threading.Thread(target=self._ffmpeg_pacing_loop, daemon=True)
        self._writer_thread.start()

    def _ffmpeg_pacing_loop(self):
        """Writer thread loop for FFmpeg with manual frame pacing."""
        frame_period = 1.0 / self.fps
        last_frame_sent = None

        while not self._stop_evt.is_set():
            start_time = time.monotonic()
            
            try:
                frame = self._frame_queue.get_nowait()
                if frame is None: # Sentinel value
                    break
                last_frame_sent = frame
            except queue.Empty:
                frame = last_frame_sent

            if frame is None:
                time.sleep(frame_period)
                continue

            try:
                if not self.is_active():
                    raise BrokenPipeError("FFmpeg process is not active")
                self._ffmpeg_process.stdin.write(frame.tobytes())
                self._ffmpeg_process.stdin.flush()  # Ensure data is sent immediately
            except (BrokenPipeError, OSError) as e:
                
                # Check if this failure was from a HW encoder
                is_hw_encoder = self._active_encoder_name and \
                                ("nvenc" in self._active_encoder_name or 
                                 "omx" in self._active_encoder_name or 
                                 "videotoolbox" in self._active_encoder_name)

                if is_hw_encoder:
                    logger.warning(f"Hardware encoder {self._active_encoder_name} failed at runtime for {self.pipeline_id}. Falling back to CPU.")
                    self._hw_encoder_failed.set()
                else:
                    logger.error(f"FFmpeg ({self._active_encoder_name or 'unknown'}) process pipe broken for {self.pipeline_id}: {e}. Stream will restart.")

                break 
            
            elapsed = time.monotonic() - start_time
            sleep_duration = max(0, frame_period - elapsed)
            time.sleep(sleep_duration)

    def _log_ffmpeg_stderr(self, stderr_pipe, pipeline_id):
        """Background thread to continuously log FFmpeg's stderr."""
        try:
            for line in iter(stderr_pipe.readline, b''):
                if not line:
                    break
                logger.warning(f"[FFmpeg {pipeline_id}]: {line.decode('utf-8', errors='ignore').strip()}")
        except Exception as e:
            logger.info(f"FFmpeg stderr logging thread exited for {pipeline_id}: {e}")
        finally:
            if stderr_pipe:
                stderr_pipe.close()

    # -------------------- Pipeline Builders --------------------

    def _build_ffmpeg_cmd(self, force_cpu: bool = False) -> Tuple[List[str], str]:
        """
        Builds the FFmpeg command list.
        Returns: (command_list, encoder_name)
        """
        encoder_args, encoder_name = self._select_ffmpeg_encoder(force_cpu=force_cpu)

        cmd = [
            'ffmpeg', '-y', '-loglevel', 'error', '-nostats', '-hide_banner',
            '-f', 'rawvideo', '-pixel_format', 'bgr24',
            '-video_size', f'{self.width}x{self.height}',
            '-framerate', str(self.fps), '-i', '-',
        ]
        
        # Add encoder and encoder-specific parameters
        cmd.extend(encoder_args)
        
        # Common video parameters
        cmd.extend([
            '-pix_fmt', 'yuv420p',
            '-b:v', f"{self.bitrate}k", '-maxrate', f"{self.bitrate}k", '-bufsize', f"{self.bitrate*2}k",
            '-g', str(self.fps * 2), '-keyint_min', str(self.fps),
            '-force_key_frames', 'expr:gte(t,n_forced*1)', 
            '-an',  # No audio
            '-flvflags', 'no_duration_filesize', 
            '-f', 'flv', self.rtmp_url,
        ])
        
        return cmd, encoder_name

    def _select_ffmpeg_encoder(self, force_cpu: bool = False) -> Tuple[List[str], str]:
        """
        Returns (encoder_args_list, encoder_name_str)
        Will force CPU if force_cpu is True.
        """
        if force_cpu:
            return [
                "-c:v", "libx264",
                "-preset", "ultrafast",
                "-tune", "zerolatency",
                "-profile:v", "main",
            ], "libx264"
        
        force_encoder = os.environ.get("RTMP_ENCODER", "").lower()
        
        if force_encoder == "cpu" or force_encoder == "libx264":
            return [
                "-c:v", "libx264",
                "-preset", "ultrafast",
                "-tune", "zerolatency",
                "-profile:v", "main",
            ], "libx264"
        elif force_encoder == "nvenc":
            return [
                "-c:v", "h264_nvenc",
                "-preset", "p1",  # p1 = fastest, p7 = slowest
                "-tune", "ull",  # ultra-low latency
                "-rc:v", "cbr",  # constant bitrate for streaming
                "-rc-lookahead", "0",  # disable lookahead for lower latency
                "-delay", "0",  # zero delay
                "-zerolatency", "1",  # enable zero latency mode
                "-profile:v", "main",
                "-gpu", "0",  # Use first GPU
            ], "h264_nvenc"
        
        if self._platform.is_jetson():
            # Jetson-specific encoder with optimizations
            return [
                "-c:v", "h264_nvenc",
                "-preset", "p1",
                "-tune", "ull",
                "-rc:v", "cbr",
                "-rc-lookahead", "0",
                "-delay", "0",
                "-zerolatency", "1",
                "-profile:v", "main",
            ], "h264_nvenc"

        if sys.platform == "darwin": 
            return [
                "-c:v", "h264_videotoolbox",
                "-profile:v", "main",
                "-realtime", "1",
            ], "h264_videotoolbox"
        
        has_nvidia = (os.environ.get("NVIDIA_VISIBLE_DEVICES") is not None or 
                      os.path.exists("/proc/driver/nvidia/version"))
        
        if has_nvidia:
            return [
                "-c:v", "h264_nvenc",
                "-preset", "p1",  # p1 = fastest preset
                "-tune", "ull",  # ultra-low latency
                "-rc:v", "cbr",  # constant bitrate
                "-rc-lookahead", "0",  # disable lookahead
                "-delay", "0",  # zero delay
                "-zerolatency", "1",  # zero latency mode
                "-profile:v", "main",
                "-gpu", "0",  # Use first GPU
            ], "h264_nvenc"
        
        return [
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-tune", "zerolatency",
            "-profile:v", "main",
        ], "libx264"