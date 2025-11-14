from .files_sink import FileSink
try:
    from .kafka_sink import KafkaSink  # optional
except Exception:  # pragma: no cover
    KafkaSink = None

__all__ = ["FileSink", "KafkaSink"]
