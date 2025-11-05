from datetime import datetime

class PipelinePreviewChecker:
    """
    Utility class to check if RTMP streaming should be enabled for a pipeline
    based on the last preview request timestamp.
    """
    
    @staticmethod
    def should_stream_rtmp(last_preview_request_at, preview_window_seconds=300):
        """
        Check if RTMP streaming should be enabled based on the last preview request.
        
        Args:
            last_preview_request_at: DateTime object or None representing the last preview request
            preview_window_seconds: Time window in seconds to keep streaming after a request (default: 300 = 5 minutes)
            
        Returns:
            bool: True if streaming should be enabled, False otherwise
        """
        if last_preview_request_at is None:
            return False
        
        # Calculate the time difference
        current_time = datetime.utcnow()
        time_since_request = current_time - last_preview_request_at
        
        # Check if we're within the preview window
        return time_since_request.total_seconds() <= preview_window_seconds
    
    @staticmethod
    def get_remaining_preview_time(last_preview_request_at, preview_window_seconds=300):
        """
        Get the remaining time (in seconds) for the preview window.
        
        Args:
            last_preview_request_at: DateTime object or None representing the last preview request
            preview_window_seconds: Time window in seconds (default: 300 = 5 minutes)
            
        Returns:
            int: Remaining seconds in the preview window, or 0 if expired/not requested
        """
        if last_preview_request_at is None:
            return 0
        
        current_time = datetime.utcnow()
        time_since_request = current_time - last_preview_request_at
        remaining = preview_window_seconds - time_since_request.total_seconds()
        
        return max(0, int(remaining))
