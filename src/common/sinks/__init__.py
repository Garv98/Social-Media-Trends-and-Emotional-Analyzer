from .files_sink import FileSink
from .supabase_sink import SupabaseSink
try:
    from .kafka_sink import KafkaSink  # optional
except Exception:  # pragma: no cover
    KafkaSink = None

__all__ = ["FileSink", "KafkaSink", "SupabaseSink"]
