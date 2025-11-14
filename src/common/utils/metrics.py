import time
from collections import deque
from typing import Dict


class MetricsLogger:
    """Track and log pipeline metrics: throughput, errors, dedup ratio."""

    def __init__(self, window_sec: int = 60):
        self.window_sec = window_sec
        self.events_processed = 0
        self.events_deduplicated = 0
        self.errors = 0
        self.start_time = time.time()
        self.recent_events = deque()  # (timestamp, count) for windowed rate

    def log_event(self, deduplicated: bool = False):
        """Log a processed event."""
        self.events_processed += 1
        if deduplicated:
            self.events_deduplicated += 1
        now = time.time()
        self.recent_events.append((now, 1))
        # Trim old events outside window
        cutoff = now - self.window_sec
        while self.recent_events and self.recent_events[0][0] < cutoff:
            self.recent_events.popleft()

    def log_error(self):
        """Log an error."""
        self.errors += 1

    def rate_per_min(self) -> float:
        """Events per minute (recent window)."""
        if not self.recent_events:
            return 0.0
        window_duration = time.time() - self.recent_events[0][0]
        if window_duration == 0:
            return 0.0
        count = sum(c for _, c in self.recent_events)
        return (count / window_duration) * 60.0

    def dedup_ratio(self) -> float:
        """Percentage of events deduplicated."""
        if self.events_processed == 0:
            return 0.0
        return (self.events_deduplicated / self.events_processed) * 100.0

    def summary(self) -> Dict:
        """Return metrics summary."""
        elapsed = time.time() - self.start_time
        return {
            'elapsed_sec': round(elapsed, 2),
            'events_processed': self.events_processed,
            'events_deduplicated': self.events_deduplicated,
            'errors': self.errors,
            'rate_per_min': round(self.rate_per_min(), 2),
            'dedup_ratio_pct': round(self.dedup_ratio(), 2)
        }

    def log_summary(self):
        """Print metrics summary to console."""
        s = self.summary()
        print(f"[METRICS] Processed: {s['events_processed']} | "
              f"Deduped: {s['events_deduplicated']} ({s['dedup_ratio_pct']}%) | "
              f"Errors: {s['errors']} | "
              f"Rate: {s['rate_per_min']:.1f} events/min | "
              f"Elapsed: {s['elapsed_sec']}s")
