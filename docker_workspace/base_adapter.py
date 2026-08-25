class BaseProxyAdapter:
    """
    Abstract base class for all reverse proxy adapters.
    """

    def collect_metrics(self) -> dict:
        """
        Collect and return normalized proxy metrics.

        Returns:
            dict: {
                "rps": float,
                "avg_latency_ms": float,
                "error_rate": float,
                "active_connections": int
            }
        """
        raise NotImplementedError("Proxy adapter must implement collect_metrics()")
