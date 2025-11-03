"""instrumentation.py"""

try:
    from opentelemetry.trace import get_current_span, get_tracer_provider # pylint: disable=unused-import
except ModuleNotFoundError:
    def get_current_span() -> None:
        """dummy current span"""

    def get_tracer_provider() -> None:
        """dummy trace provider"""
